from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Solo le prenotazioni ancora attive occupano il tavolo nella mappa base.
s=s.replace("links.forEach(x=>{let c=x.restaurant_tables?.code;if(c)counts[c]=(counts[c]||0)+1});",
            "links.filter(x=>reservations.find(r=>r.id===x.reservation_id)?.status==='confermata').forEach(x=>{let c=x.restaurant_tables?.code;if(c)counts[c]=(counts[c]||0)+1});",1)

new_bookings=r'''function renderBookings(){
  let ordered=[...reservations].sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));
  const TURN=15,STD=105;
  const mins=v=>{let x=hhmm(v).split(':');return x.length===2?Number(x[0])*60+Number(x[1]):null};
  const fmt=m=>String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
  const serviceClose=r=>String(r.service_code||'').includes('pranzo')?900:1380;
  function shared(a,b){let ac=tableCodesForRes(a.id),bc=tableCodesForRes(b.id);return ac.filter(x=>bc.includes(x))}
  function availableFrom(r,code){
    if(r.status!=='confermata')return '';
    let start=mins(r.arrival_time);
    let end=Math.max(mins(r.expected_end_time)||0,start+STD);
    let freeFrom=end+TURN;
    let next=[...ordered].filter(x=>x.status==='confermata'&&x.id!==r.id&&tableCodesForRes(x.id).includes(code)&&mins(x.arrival_time)>start).sort((a,b)=>mins(a.arrival_time)-mins(b.arrival_time))[0]||null;
    let limit=next?mins(next.arrival_time):serviceClose(r);
    if(freeFrom+STD+TURN>limit)return '';
    return '<div class="availabilityWindow"><b>'+esc(code)+'</b> · Tavolo prenotabile dalle ore <b>'+fmt(freeFrom)+'</b></div>';
  }
  $('bookingList').innerHTML=ordered.map((r,i)=>{
    let prev=null,next=null,prevTables=[],nextTables=[];
    for(let j=i-1;j>=0;j--){let sh=shared(r,ordered[j]);if(sh.length){prev=ordered[j];prevTables=sh;break}}
    for(let j=i+1;j<ordered.length;j++){let sh=shared(r,ordered[j]);if(sh.length){next=ordered[j];nextTables=sh;break}}
    let chain='';
    if(prev)chain+='<div class="turnLink prevTurn">← Turno precedente '+hhmm(prev.arrival_time)+' · '+esc(prev.guest_name)+' · '+esc(prevTables.join(', '))+'</div>';
    if(next)chain+='<div class="turnLink nextTurn">→ Prossimo '+hhmm(next.arrival_time)+' · '+esc(next.guest_name)+' · '+esc(nextTables.join(', '))+'</div>';
    let windows=tableCodesForRes(r.id).map(c=>availableFrom(r,c)).join('');
    let state=r.status==='completata'?'<span class="presenceBadge completedBadge">LIBERATO</span>':r.arrived_at?'<span class="presenceBadge arrivedBadge">CLIENTE ARRIVATO</span>':'';
    let actions='';
    if(r.status==='confermata'){
      actions+='<button class="secondary" data-edit-booking="'+esc(r.id)+'">Modifica</button>';
      if(r.arrived_at){
        actions+='<button class="secondary undoArriveBtn" data-unarrive-booking="'+esc(r.id)+'">Non arrivato</button>';
        actions+='<button class="releaseBtn" data-release-booking="'+esc(r.id)+'">Libera tavolo</button>';
      }else{
        actions+='<button class="arriveBtn" data-arrive-booking="'+esc(r.id)+'">Cliente arrivato</button>';
      }
      actions+='<button class="danger" data-delete-booking="'+esc(r.id)+'">Elimina</button>';
    }else{
      actions+='<button class="danger" data-delete-booking="'+esc(r.id)+'">Elimina</button>';
    }
    return '<div class="row bookingRow '+(r.status==='completata'?'completedBooking':'')+'"><div><b><span class="bookingTime">'+hhmm(r.arrival_time)+'</span> · '+esc(r.guest_name)+' · '+r.party_size+' coperti'+(r.forced?' · ⚠ FORZATA':'')+'</b> '+state+'<div class="muted">'+(r.expected_end_time?'Fine '+hhmm(r.expected_end_time)+' · ':'')+esc(tableLabelsForRes(r.id))+' · '+r.area+'</div>'+chain+windows+'</div><div class="actions">'+actions+'</div></div>'
  }).join('')||'<div class="muted">Nessuna prenotazione.</div>';
  $('bookingList').querySelectorAll('[data-edit-booking]').forEach(b=>b.addEventListener('click',()=>editBooking(b.dataset.editBooking)));
  $('bookingList').querySelectorAll('[data-delete-booking]').forEach(b=>b.addEventListener('click',()=>delBooking(b.dataset.deleteBooking)));
  $('bookingList').querySelectorAll('[data-arrive-booking]').forEach(b=>b.addEventListener('click',()=>markArrived(b.dataset.arriveBooking)));
  $('bookingList').querySelectorAll('[data-unarrive-booking]').forEach(b=>b.addEventListener('click',()=>unmarkArrived(b.dataset.unarriveBooking)));
  $('bookingList').querySelectorAll('[data-release-booking]').forEach(b=>b.addEventListener('click',()=>releaseBooking(b.dataset.releaseBooking)));
}'''
s,n=re.subn(r"function renderBookings\(\)\{.*?\}\s*function _renderMapBase",new_bookings+'\nfunction _renderMapBase',s,count=1,flags=re.S)
if n!=1: raise SystemExit('renderBookings presenza non sostituito')

# Le schede della mappa mostrano solo prenotazioni ancora attive e marcano quelle già arrivate.
s=s.replace(".filter(Boolean)\n        .sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));",
            ".filter(r=>r&&r.status==='confermata')\n        .sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));",1)
s=s.replace("slot.className='mapBookingSlot';",
            "slot.className='mapBookingSlot'+(r.arrived_at?' customerArrived':'');",1)
s=s.replace("slot.innerHTML='<div class=\"mapBookingTime\">'+esc(hhmm(r.arrival_time))+'</div><div class=\"mapBookingName\">'+esc(r.guest_name||'—')+'</div><div class=\"mapBookingCovers\">'+Number(r.party_size||0)+' cop.</div>';",
            "slot.innerHTML=(r.arrived_at?'<span class=\"arrivedCross\" aria-label=\"Cliente arrivato\">×</span>':'')+'<div class=\"mapBookingTime\">'+esc(hhmm(r.arrival_time))+'</div><div class=\"mapBookingName\">'+esc(r.guest_name||'—')+'</div><div class=\"mapBookingCovers\">'+Number(r.party_size||0)+' cop.</div>';",1)

# Azioni di presenza: l'arrivo è reversibile; liberando il tavolo la prenotazione diventa completata.
marker="async function delBooking(id){"
if marker not in s: raise SystemExit('delBooking non trovata')
presence=r'''async function markArrived(id){
  let r=reservations.find(x=>x.id===id);if(!r||r.status!=='confermata')return;
  let q=await db.from('reservations').update({arrived_at:new Date().toISOString(),updated_by:profile.user_id}).eq('id',id);
  if(q.error)return alert(q.error.message);
  await loadAll();
}
async function unmarkArrived(id){
  let r=reservations.find(x=>x.id===id);if(!r||r.status!=='confermata'||!r.arrived_at)return;
  if(!confirm('Segnare nuovamente questo cliente come NON ARRIVATO?'))return;
  let q=await db.from('reservations').update({arrived_at:null,updated_by:profile.user_id}).eq('id',id);
  if(q.error)return alert(q.error.message);
  await loadAll();
}
async function releaseBooking(id){
  let r=reservations.find(x=>x.id===id);if(!r||r.status!=='confermata')return;
  if(!confirm('Liberare il tavolo per il turno successivo?'))return;
  let q=await db.from('reservations').update({status:'completata',updated_by:profile.user_id}).eq('id',id);
  if(q.error)return alert(q.error.message);
  await loadAll();
}
'''
s=s.replace(marker,presence+marker,1)

css=r'''
<style id="marino-presence-ui">
.presenceBadge{display:inline-block;margin-left:6px;padding:4px 7px;border-radius:999px;font-size:9px;font-weight:950;letter-spacing:.04em;vertical-align:1px}
.arrivedBadge{background:#d9dde1;color:#39434d;border:1px solid #9aa3ab}.completedBadge{background:#edf0f2;color:#65717a;border:1px solid #c6cdd2}
.arriveBtn{background:#e1e5e8;color:#34404a;border:1px solid #aeb6bd}.undoArriveBtn{background:#eef2f5;color:#34404a;border:1px solid #aeb6bd}.releaseBtn{background:#fff4d7;color:#704c00;border:1px solid #d7aa32}.completedBooking{opacity:.68}
.mapBookingSlot.customerArrived{position:relative;background:#e3e6e8!important}.arrivedCross{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:46px;line-height:1;font-weight:500;color:rgba(79,87,94,.42);pointer-events:none;z-index:0}.customerArrived .mapBookingTime,.customerArrived .mapBookingName,.customerArrived .mapBookingCovers{position:relative;z-index:1}
@media(max-width:720px){.arrivedCross{font-size:42px}.presenceBadge{display:inline-block;margin:5px 0 0 5px}.arriveBtn,.undoArriveBtn,.releaseBtn{min-height:42px}}
</style>
'''
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
