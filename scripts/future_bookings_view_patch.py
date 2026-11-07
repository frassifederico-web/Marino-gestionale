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
      const q=await marinoBookingsWithTimeout(db.from('reservations').select('id,service_date,service_code,arrival_time,guest_name,party_size,area,status').gt('service_date',today).neq('status','annullata').order('service_date',{ascending:true}).order('arrival_time',{ascending:true}).order('id',{ascending:true}).range(offset,offset+499));
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
      const row=document.createElement('div');row.className='marinoBookingCard';
      const heading=document.createElement('div');heading.className='marinoBookingHeading';
      const number=document.createElement('span');number.className='marinoBookingNumber';number.textContent='#'+String(b.id).slice(-4);
      const name=document.createElement('strong');name.textContent=b.guest_name||'—';
      heading.append(number,name);
      const detail=document.createElement('div');detail.className='marinoBookingDetails';
      const time=document.createElement('strong');time.textContent=String(b.arrival_time||'').slice(0,5);
      const party=document.createElement('strong');party.textContent=Number(b.party_size||0)+' coperti';
      detail.append(time,party);
      const location=document.createElement('div');location.className='marinoBookingLocation';
      location.textContent=String(b.service_code||'').replaceAll('-',' ')+' · '+(names.get(String(b.id))||['Tavolo da assegnare']).join(' + ')+' · '+(b.area||'interno');
      const edit=document.createElement('button');edit.type='button';edit.className='marinoBookingEdit';edit.textContent='✎';edit.setAttribute('aria-label','Modifica prenotazione di '+(b.guest_name||'ospite'));
      edit.addEventListener('click',async()=>{
        try{
          $('date').value=b.service_date;
          serviceOptions();
          $('service').value=b.service_code;
          await loadAll();
          editBooking(b.id);
        }catch(e){console.error(e);alert('Impossibile aprire la prenotazione. Riprova.')}
      });
      row.append(heading,detail,location,edit);
      fragment.append(row);
    }
    target.replaceChildren(fragment);
    status.textContent=bookings.length+' prenotazioni nei giorni successivi · usa la matita per modificarle';
    if(!bookings.length)target.textContent='Nessuna prenotazione nei giorni successivi.';
  }catch(e){
    console.error('MARINO chronological bookings loading failed',e);
    status.textContent='Errore nel caricamento: '+String(e?.message||e)+'. Riapri Prenotazioni per riprovare.';
    document.getElementById('bookingList')?.style.removeProperty('display');
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
#bookings #bookingList{display:block!important}
#marinoAllBookings{width:100%}
.marinoCompactDay{position:sticky;top:55px;z-index:5;padding:9px 6px 5px;background:#fff9df;font-weight:800;text-transform:capitalize;font-size:12px;border-bottom:1px solid #d9b85c}
.marinoBookingCard{position:relative;padding:13px 112px 13px 12px;border-bottom:1px solid #e2e6ea;background:#fff;color:#163c63;min-height:114px}
.marinoBookingHeading{display:flex;align-items:center;gap:10px;font-size:16px;margin-bottom:5px}
.marinoBookingNumber{background:#d5a52b;color:#102b43;border-radius:9px;padding:5px 8px;font-weight:800}
.marinoBookingDetails{display:flex;gap:12px;align-items:center;font-size:17px;margin-bottom:5px}
.marinoBookingLocation{color:#758195;font-size:13px;line-height:1.4}
.marinoBookingEdit{position:absolute;right:12px;top:42px;width:44px;height:44px;border:1px solid #b5c8d8;border-radius:12px;background:#fff;color:#12416c;font-size:22px}
@media(max-width:380px){.marinoBookingCard{padding-right:65px}}
</style>"""
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
print('MARINO: original booking cards preserved; future dates shown as matching cards')
