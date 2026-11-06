from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()
anchor='<div id="bookingList"></div>'
if anchor not in s: raise SystemExit('Booking list anchor missing')
s=s.replace(anchor,anchor+'<div id="marinoAllBookings" aria-live="polite"><div id="marinoAllBookingsStatus" class="muted">Caricamento prenotazioni…</div><div id="marinoAllBookingsRows"></div></div>',1)
js=r"""
// Single compact chronological list, today and all future dates. Read-only query.
let marinoAllBookingsLoading=false,marinoAllBookingsPending=false;
async function marinoLoadAllBookings(){
  if(!profile)return;
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
      const q=await db.from('reservations').select('id,service_date,service_code,arrival_time,guest_name,party_size,area,status').gte('service_date',today).neq('status','annullata').order('service_date',{ascending:true}).order('arrival_time',{ascending:true}).order('id',{ascending:true}).range(offset,offset+499);
      if(q.error)throw q.error;
      bookings.push(...(q.data||[]));
      if((q.data||[]).length<500)break;
      if(offset===19500)throw Error('Elenco troppo lungo: limite di sicurezza raggiunto');
    }
    const names=new Map();
    for(let i=0;i<bookings.length;i+=100){
      const q=await db.from('reservation_tables').select('reservation_id,table_id').in('reservation_id',bookings.slice(i,i+100).map(b=>b.id));
      if(q.error)throw q.error;
      for(const link of q.data||[]){
        const t=allTables.find(t=>String(t.id)===String(link.table_id));
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
      const row=document.createElement('button');
      row.type='button';row.className='marinoCompactBooking';
      const time=document.createElement('span');time.className='marinoCompactTime';time.textContent=String(b.arrival_time||'').slice(0,5);
      const name=document.createElement('span');name.className='marinoCompactName';name.textContent=b.guest_name||'—';
      const party=document.createElement('span');party.className='marinoCompactParty';party.textContent=Number(b.party_size||0)+' pers.';
      const table=document.createElement('span');table.className='marinoCompactTable';table.textContent=(names.get(String(b.id))||['Da assegnare']).join(' + ');
      row.append(time,name,party,table);
      row.addEventListener('click',async()=>{
        try{
          $('date').value=b.service_date;
          serviceOptions();
          $('service').value=b.service_code;
          await loadAll();
          editBooking(b.id);
        }catch(e){console.error(e);alert('Impossibile aprire la prenotazione. Riprova.')}
      });
      fragment.append(row);
    }
    target.replaceChildren(fragment);
    status.textContent=bookings.length+' prenotazioni da oggi in avanti · tocca una riga per modificarla';
    if(!bookings.length)target.textContent='Nessuna prenotazione da oggi in avanti.';
  }catch(e){
    console.error('MARINO chronological bookings loading failed',e);
    status.textContent='Impossibile caricare l’elenco completo. Riapri Prenotazioni per riprovare.';
    target.replaceChildren();
  }finally{
    marinoAllBookingsLoading=false;
    if(marinoAllBookingsPending){marinoAllBookingsPending=false;void marinoLoadAllBookings()}
  }
}
const marinoAllBookingsShowPageBase=showPage;
showPage=function(id,...args){
  const out=marinoAllBookingsShowPageBase.call(this,id,...args);
  if(id==='bookings')void marinoLoadAllBookings();
  return out;
};
const marinoAllBookingsRenderBase=renderBookings;
renderBookings=function(...args){
  const out=marinoAllBookingsRenderBase.apply(this,args);
  if(document.getElementById('bookings')?.classList.contains('on'))void marinoLoadAllBookings();
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
.marinoCompactBooking{display:grid;grid-template-columns:44px minmax(0,1fr) 48px 72px;align-items:center;gap:5px;width:100%;text-align:left;background:transparent;color:#063f78;border-radius:0;border-bottom:1px solid #e7dcc0;padding:9px 3px;min-height:42px;font-size:12px;font-weight:500}
.marinoCompactTime{font-weight:800}.marinoCompactName{font-weight:750;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.marinoCompactParty,.marinoCompactTable{text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media(min-width:700px){.marinoCompactBooking{grid-template-columns:70px minmax(0,1fr) 80px 130px;font-size:14px}}
</style>"""
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
print('MARINO: compact all-dates bookings list installed')
