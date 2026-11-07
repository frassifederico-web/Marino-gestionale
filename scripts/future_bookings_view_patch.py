from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()
anchor='<div id="bookingList"></div>'
if anchor not in s: raise SystemExit('Booking list anchor missing')
s=s.replace(anchor,anchor+'<div id="marinoAllBookings" aria-live="polite"><div id="marinoAllBookingsStatus" class="muted">Caricamento prenotazioni…</div><div id="marinoAllBookingsRows"></div></div>',1)
js=r"""
// Single compact chronological list, today and all future dates. Read-only query.
let marinoAllBookingsLoading=false,marinoAllBookingsPending=false,marinoAllBookingsRefreshTimer=null;
const marinoBookingsWithTimeout=(work,ms=16000)=>Promise.race([
  work,
  new Promise((_,reject)=>setTimeout(()=>reject(new Error('Tempo scaduto nel caricamento prenotazioni')),ms))
]);
async function marinoLoadAllBookings(){
  if(!profile){
    const status=document.getElementById('marinoAllBookingsStatus');
    if(status)status.textContent='Sessione non pronta: riapri Prenotazioni per riprovare.';
    return;
  }
  if(marinoAllBookingsLoading){marinoAllBookingsPending=true;return}
  const status=document.getElementById('marinoAllBookingsStatus'),target=document.getElementById('marinoAllBookingsRows');
  if(!status||!target)return;
  marinoAllBookingsLoading=true;
  status.textContent='Caricamento prenotazioni…';
  try{
    const today=marinoToday();
    const bookings=[];
    // Paginate: no 31-day cutoff and no silent 1000-row truncation.
    for(let offset=0;offset<20000;offset+=500){
      const q=await marinoBookingsWithTimeout(db.from('reservations').select('*').gte('service_date',today).neq('status','annullata').order('service_date',{ascending:true}).order('arrival_time',{ascending:true}).order('id',{ascending:true}).range(offset,offset+499));
      if(q.error)throw q.error;
      bookings.push(...(q.data||[]));
      if((q.data||[]).length<500)break;
      if(offset===19500)throw Error('Elenco troppo lungo: limite di sicurezza raggiunto');
    }
    const names=new Map();
    const marinoTableById=new Map(allTables.map(t=>[String(t.id),t]));
    for(let i=0;i<bookings.length;i+=100){
      let q;
      try {
        q=await marinoBookingsWithTimeout(db.from('reservation_tables').select('reservation_id,table_id').in('reservation_id',bookings.slice(i,i+100).map(b=>b.id)));
        if(q.error)throw q.error;
      } catch(linkError) {
        console.warn('MARINO: assegnazioni tavoli non disponibili; elenco prenotazioni comunque visibile',linkError);
        break;
      }
      for(const link of q.data||[]){
        const t=marinoTableById.get(String(link.table_id));
        if(t){
          const k=String(link.reservation_id);
          names.set(k,[...(names.get(k)||[]),t.label||t.code]);
        }
      }
    }
    const fragment=document.createDocumentFragment();
    let previous='';
    for(const b of bookings){
      if(b.service_date!==previous){
        previous=b.service_date;
        const h=document.createElement('div');h.className='marinoCompactDay';
        h.textContent=new Intl.DateTimeFormat('it-IT',{weekday:'long',day:'2-digit',month:'long',year:'numeric'}).format(new Date(previous+'T12:00:00'));
        fragment.append(h);
      }
      const row=document.createElement('div');row.className='marinoCompactOriginalRow';
      const left=document.createElement('div');left.className='marinoCompactOriginalMain';
      const head=document.createElement('div');head.className='marinoCompactOriginalHead';
      const no=document.createElement('span');no.className='marinoCompactOriginalNo';
      no.textContent='#'+(typeof reservationDisplayNo==='function'?reservationDisplayNo(b):String(b.id).slice(-4));
      const name=document.createElement('strong');name.textContent=b.guest_name||'—';
      head.append(no,name);
      const core=document.createElement('div');core.className='marinoCompactOriginalCore';
      const time=document.createElement('strong');time.textContent=String(b.arrival_time||'').slice(0,5);
      const party=document.createElement('strong');party.textContent=Number(b.party_size||0)+' coperti';
      core.append(time,party);
      const location=document.createElement('div');location.className='marinoCompactOriginalLocation';
      location.textContent=(String(b.service_code||'').includes('pranzo')?'Pranzo':'Cena')+' · '+(names.get(String(b.id))||['Tavolo da assegnare']).join(' + ')+' · '+(b.area||'interno');
      left.append(head,core,location);
      if(String(b.notes||'').trim()){
        const note=document.createElement('div');note.className='marinoCompactOriginalNote';
        const label=document.createElement('b');label.textContent='NOTE: ';
        note.append(label,document.createTextNode(String(b.notes).trim()));
        left.append(note);
      }
      const actions=document.createElement('div');actions.className='marinoCompactOriginalActions';
      const button=(symbol,cls,description,handler)=>{
        const el=document.createElement('button');el.type='button';el.className='marinoCompactAction '+cls;
        el.textContent=symbol;el.setAttribute('aria-label',description);
        el.addEventListener('click',handler);actions.append(el);
      };
      if(b.status==='confermata'){
        const arrived=Boolean(b.arrived_at);
        button(arrived?'↩':'✓','marinoCompactArrive',arrived?'Da arrivare':'Arrivato',async()=>{
          if(typeof setChronologicalArrival==='function')await setChronologicalArrival(b.id,!arrived,b.service_date);
          else alert('Azione arrivo momentaneamente non disponibile');
          void marinoLoadAllBookings();
        });
      }
      button('✎','marinoCompactEdit','Modifica',async()=>{
        try{
          if(typeof openChronologicalBooking==='function')await openChronologicalBooking(b.id,b.service_date,b.service_code);
          else{
            $('date').value=b.service_date;serviceOptions();$('service').value=b.service_code;
            await loadAll();editBooking(b.id);
          }
        }catch(e){console.error(e);alert('Impossibile aprire la prenotazione. Riprova.')}
      });
      button('×','marinoCompactCancel','Annulla',async()=>{
        if(typeof cancelBookingFromList==='function')await cancelBookingFromList(b.id);
        else alert('Azione annullamento momentaneamente non disponibile');
        void marinoLoadAllBookings();
      });
      row.append(left,actions);fragment.append(row);
    }
    target.replaceChildren(fragment);
    status.textContent=bookings.length+' prenotazioni da oggi in avanti · tocca una riga per modificarla';
    if(!bookings.length)target.textContent='Nessuna prenotazione da oggi in avanti.';
  }catch(e){
    console.error('MARINO chronological bookings loading failed',e);
    status.textContent='Errore nel caricamento: '+String(e?.message||e)+'. Riapri Prenotazioni per riprovare.';
    document.getElementById('bookingList')?.style.setProperty('display','block','important');
    target.replaceChildren();
  }finally{
    marinoAllBookingsLoading=false;
    if(marinoAllBookingsPending){marinoAllBookingsPending=false;void marinoLoadAllBookings()}
  }
}
// The initial bookings page may be opened during boot(), before these hooks are installed.
// Start the first read once authentication and the active bookings view are ready.
let marinoBookingsInitialStarted=false;
const marinoBookingsStartupCheck=setInterval(()=>{
  if(marinoBookingsInitialStarted)return clearInterval(marinoBookingsStartupCheck);
  const active=document.getElementById('bookings')?.classList.contains('on');
  if(active&&profile&&document.getElementById('marinoAllBookingsStatus')){
    marinoBookingsInitialStarted=true;
    clearInterval(marinoBookingsStartupCheck);
    void marinoLoadAllBookings();
  }
},650);
const marinoAllBookingsShowPageBase=showPage;
showPage=function(id,...args){
  const out=marinoAllBookingsShowPageBase.call(this,id,...args);
  if(id==='bookings')void marinoLoadAllBookings();
  return out;
};
const marinoAllBookingsRenderBase=renderBookings;
renderBookings=function(...args){
  const out=marinoAllBookingsRenderBase.apply(this,args);
  if(document.getElementById('bookings')?.classList.contains('on')){
    clearTimeout(marinoAllBookingsRefreshTimer);
    marinoAllBookingsRefreshTimer=setTimeout(()=>void marinoLoadAllBookings(),350);
  }
  return out;
};
"""
end=s.rfind('</script>')
if end<0:raise SystemExit('Script end not found')
s=s[:end]+'\n'+js+'\n'+s[end:]
css="""<style id="marino-compact-bookings-css">
#bookings #bookingList{display:none!important}
#marinoAllBookings{width:100%}
.marinoCompactDay{position:sticky;top:55px;z-index:5;padding:9px 6px 5px;background:#fff9df;font-weight:800;text-transform:capitalize;font-size:12px;border-bottom:1px solid #d9b85c}
.marinoCompactOriginalRow{display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px solid #e6ebee;padding:10px 3px;background:white;color:#073e76}
.marinoCompactOriginalMain{flex:1;min-width:0}
.marinoCompactOriginalHead{display:flex;gap:7px;align-items:center;min-width:0;font-size:15px;color:#073e76}
.marinoCompactOriginalHead strong{white-space:nowrap;text-overflow:ellipsis;overflow:hidden}
.marinoCompactOriginalNo{flex:none;border-radius:9px;background:#d9a82d;padding:6px 8px;font-weight:800;color:#1c3445}
.marinoCompactOriginalCore{display:flex;gap:9px;align-items:center;font-size:16px;color:#102c45;margin-top:4px}
.marinoCompactOriginalLocation{font-size:11px;color:#7a879b;margin-top:4px}
.marinoCompactOriginalNote{background:#fff4d8;border:1px solid #e9ce7c;border-radius:7px;padding:5px 7px;font-size:11px;color:#564100;margin-top:5px;overflow-wrap:anywhere}
.marinoCompactOriginalActions{display:flex;flex:none;gap:4px}
.marinoCompactAction{display:inline-flex;align-items:center;justify-content:center;padding:0!important;width:35px!important;height:35px!important;min-width:35px!important;min-height:35px!important;border:1px solid #b7c8d8!important;border-radius:10px!important;background:white!important;color:#25486b!important;font-size:20px!important;font-weight:800}
.marinoCompactArrive{background:#e4e9ed!important;color:#34404a!important;border-color:#aeb6bd!important}
.marinoCompactCancel{background:#fae8e8!important;color:#a83e3e!important;border-color:#eababa!important}
@media(max-width:390px){.marinoCompactOriginalHead{font-size:13px}.marinoCompactOriginalCore{font-size:14px}.marinoCompactAction{width:31px!important;height:33px!important;min-width:31px!important}.marinoCompactOriginalRow{gap:5px}}
</style>"""
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
print('MARINO: chronological original-style bookings, all dates and actions restored')
