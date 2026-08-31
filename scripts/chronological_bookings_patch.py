from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# La pagina Prenotazioni diventa una vista cronologica dei prossimi 31 giorni,
# sempre a partire da oggi (Europe/Rome), raggruppata per giorno.
s=s.replace(
    '<div class="muted" style="margin:5px 0 10px">Ordine cronologico · rimpiazzi precedente e successivo indicati sotto la prenotazione.</div>',
    '<div class="muted" style="margin:5px 0 10px">Dal giorno odierno in avanti · prenotazioni raggruppate per data e ordinate per orario.</div>',
    1
)

new_render=r'''async function renderBookings(){
  const host=$('bookingList');
  if(!host)return;
  host.innerHTML='<div class="muted">Caricamento prenotazioni…</div>';
  const start=marinoToday();
  const d0=new Date(start+'T12:00:00');
  const d1=new Date(d0);d1.setDate(d1.getDate()+30);
  const y=d1.getFullYear(),m=String(d1.getMonth()+1).padStart(2,'0'),d=String(d1.getDate()).padStart(2,'0');
  const end=y+'-'+m+'-'+d;
  let [rq,lq]=await Promise.all([
    db.from('reservations').select('*').gte('service_date',start).lte('service_date',end).neq('status','annullata').order('service_date').order('arrival_time'),
    db.from('reservation_tables').select('reservation_id,restaurant_tables(code,label)')
  ]);
  if(rq.error){host.innerHTML='<div class="warn">Errore caricamento prenotazioni: '+esc(rq.error.message)+'</div>';return}
  let all=(rq.data||[]), allLinks=lq.data||[];
  const labelsFor=id=>allLinks.filter(x=>x.reservation_id===id).map(x=>x.restaurant_tables?.label||x.restaurant_tables?.code).filter(Boolean).join(' + ');
  const dayLabel=iso=>new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long',day:'numeric',month:'long'}).format(new Date(iso+'T12:00:00'));
  const serviceLabel=code=>String(code||'').includes('pranzo')?'Pranzo':'Cena';
  const days=[];for(let i=0;i<=30;i++){let x=new Date(d0);x.setDate(d0.getDate()+i);days.push(x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0'))}
  host.innerHTML=days.map(iso=>{
    let rows=all.filter(r=>r.service_date===iso).sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));
    let title=dayLabel(iso);
    let cards=rows.map(r=>{
      let state=r.status==='completata'?'<span class="presenceBadge completedBadge">LIBERATO</span>':r.arrived_at?'<span class="presenceBadge arrivedBadge">CLIENTE ARRIVATO</span>':'';
      return '<div class="chronoBookingRow"><div><b><span class="reservationNo">#'+reservationDisplayNo(r)+'</span> · '+hhmm(r.arrival_time)+' · '+esc(r.guest_name)+' · '+Number(r.party_size||0)+' coperti</b> '+state+'<div class="muted">'+serviceLabel(r.service_code)+' · '+esc(labelsFor(r.id)||'Tavolo da assegnare')+' · '+esc(r.area||'')+'</div></div><button class="secondary" data-open-chrono="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'" data-service="'+esc(r.service_code)+'">Apri</button></div>';
    }).join('');
    return '<section class="chronoDay"><div class="chronoDayHead"><div><b>'+esc(title)+'</b><span>'+rows.length+' '+(rows.length===1?'prenotazione':'prenotazioni')+'</span></div></div>'+(rows.length?'<div class="chronoDayList">'+cards+'</div>':'')+'</section>';
  }).join('');
  host.querySelectorAll('[data-open-chrono]').forEach(b=>b.addEventListener('click',()=>openChronologicalBooking(b.dataset.openChrono,b.dataset.date,b.dataset.service)));
}
async function openChronologicalBooking(id,date,service){
  $('date').value=date;
  serviceOptions();
  if([...$('service').options].some(o=>o.value===service))$('service').value=service;
  await loadAll();
  editBooking(id);
}'''

s,n=re.subn(r"(?:async\s+)?function\s+renderBookings\s*\(\s*\)\s*\{.*?\n\}\nfunction _renderMapBase",new_render+'\nfunction _renderMapBase',s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'renderBookings cronologico non sostituito: {n}')

# Espone la funzione usata dai pulsanti della vista cronologica.
if 'openChronologicalBooking' not in s:
    raise SystemExit('openChronologicalBooking non presente')
if 'Object.assign(window,{' in s and 'openChronologicalBooking' not in re.search(r'Object\.assign\(window,\{.*?\}\);',s,re.S).group(0):
    s=s.replace('Object.assign(window,{','Object.assign(window,{openChronologicalBooking,',1)

css=r'''<style id="marino-chronological-bookings">
.chronoDay{margin:0 0 14px;border:1px solid #dfe8ef;border-radius:16px;overflow:hidden;background:#fff}
.chronoDayHead{padding:12px 14px;background:#eef5fb;border-bottom:1px solid #dfe8ef;text-transform:capitalize}
.chronoDayHead>div{display:flex;align-items:center;justify-content:space-between;gap:12px}
.chronoDayHead b{font-size:16px;color:#063f78}.chronoDayHead span{font-size:12px;font-weight:800;color:#526574}
.chronoDayList{padding:0 12px}.chronoBookingRow{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 2px;border-bottom:1px solid #edf1f4}.chronoBookingRow:last-child{border-bottom:0}
@media(max-width:720px){.chronoDay{margin-bottom:11px}.chronoDayHead{padding:11px 12px}.chronoDayHead b{font-size:15px}.chronoBookingRow{align-items:flex-start}.chronoBookingRow>button{min-height:40px;flex:0 0 auto}}
</style>'''
if '</head>' not in s: raise SystemExit('head non trovato per vista cronologica')
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
