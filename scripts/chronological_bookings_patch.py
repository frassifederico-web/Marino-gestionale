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
    let covers=rows.reduce((sum,r)=>sum+Number(r.party_size||0),0);
    let title=dayLabel(iso);
    let cards=rows.map(r=>{
      let state=r.status==='completata'?'<span class="presenceBadge completedBadge">LIBERATO</span>':r.arrived_at?'<span class="presenceBadge arrivedBadge">CLIENTE ARRIVATO</span>':'';
      let arriveAction='';
      if(r.status==='confermata'){
        arriveAction=r.arrived_at
          ? '<button class="secondary chronoArriveToggle chronoArrived" data-chrono-unarrive="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'">Cliente da arrivare</button>'
          : '<button class="arriveBtn chronoArriveToggle" data-chrono-arrive="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'">Cliente arrivato</button>';
      }
      return '<div class="chronoBookingRow"><div class="chronoBookingMain"><b><span class="reservationNo">#'+reservationDisplayNo(r)+'</span> · '+hhmm(r.arrival_time)+' · '+esc(r.guest_name)+' · '+Number(r.party_size||0)+' coperti</b> '+state+'<div class="muted">'+serviceLabel(r.service_code)+' · '+esc(labelsFor(r.id)||'Tavolo da assegnare')+' · '+esc(r.area||'')+'</div></div><div class="chronoQuickActions">'+arriveAction+'<button class="secondary" data-open-chrono="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'" data-service="'+esc(r.service_code)+'">Apri</button></div></div>';
    }).join('');
    return '<section class="chronoDay"><div class="chronoDayHead"><div><b>'+esc(title)+'</b><span>'+covers+' '+(covers===1?'coperto prenotato':'coperti prenotati')+'</span></div></div>'+(rows.length?'<div class="chronoDayList">'+cards+'</div>':'')+'</section>';
  }).join('');
  host.querySelectorAll('[data-open-chrono]').forEach(b=>b.addEventListener('click',()=>openChronologicalBooking(b.dataset.openChrono,b.dataset.date,b.dataset.service)));
  host.querySelectorAll('[data-chrono-arrive]').forEach(b=>b.addEventListener('click',()=>setChronologicalArrival(b.dataset.chronoArrive,true,b.dataset.date)));
  host.querySelectorAll('[data-chrono-unarrive]').forEach(b=>b.addEventListener('click',()=>setChronologicalArrival(b.dataset.chronoUnarrive,false,b.dataset.date)));
}
async function setChronologicalArrival(id,arrived,date){
  if(!arrived&&!confirm('Segnare nuovamente questo cliente come DA ARRIVARE? Il tavolo resterà assegnato.'))return;
  const patch={arrived_at:arrived?new Date().toISOString():null};
  if(profile?.user_id)patch.updated_by=profile.user_id;
  const q=await db.from('reservations').update(patch).eq('id',id).eq('status','confermata');
  if(q.error)return alert(q.error.message);
  if($('date')?.value===date)await loadAll();
  else await renderBookings();
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

if 'openChronologicalBooking' not in s or 'setChronologicalArrival' not in s:
    raise SystemExit('Funzioni cronologiche non presenti')
if 'Object.assign(window,{' in s:
    m=re.search(r'Object\.assign\(window,\{.*?\}\);',s,re.S)
    if m:
        prefix=[]
        if 'openChronologicalBooking' not in m.group(0): prefix.append('openChronologicalBooking')
        if 'setChronologicalArrival' not in m.group(0): prefix.append('setChronologicalArrival')
        if prefix:s=s.replace('Object.assign(window,{','Object.assign(window,{'+','.join(prefix)+',',1)

css=r'''<style id="marino-chronological-bookings">
.chronoDay{margin:0 0 14px;border:1px solid #dfe8ef;border-radius:16px;overflow:hidden;background:#fff}
.chronoDayHead{padding:12px 14px;background:#eef5fb;border-bottom:1px solid #dfe8ef;text-transform:capitalize}
.chronoDayHead>div{display:flex;align-items:center;justify-content:space-between;gap:12px}
.chronoDayHead b{font-size:16px;color:#063f78}.chronoDayHead span{font-size:12px;font-weight:800;color:#526574}
.chronoDayList{padding:0 12px}.chronoBookingRow{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 2px;border-bottom:1px solid #edf1f4}.chronoBookingRow:last-child{border-bottom:0}
.chronoBookingMain{min-width:0;flex:1}.chronoQuickActions{display:flex;align-items:center;gap:5px;flex:0 0 auto}.chronoQuickActions button{min-height:34px;padding:6px 8px;font-size:11px;white-space:nowrap;border-radius:8px}.chronoArriveToggle{font-weight:900}.chronoArrived{background:#eef2f5!important;color:#34404a!important;border-color:#aeb6bd!important}
@media(max-width:720px){.chronoDay{margin-bottom:11px}.chronoDayHead{padding:10px 11px}.chronoDayHead b{font-size:15px}.chronoBookingRow{align-items:flex-start;padding:9px 1px;gap:7px}.chronoQuickActions{flex-direction:column;gap:4px}.chronoQuickActions button{min-height:31px!important;padding:5px 7px!important;font-size:10px!important;width:100%;max-width:108px}.chronoArriveToggle{max-width:108px!important}.presenceBadge{font-size:8px!important;padding:3px 5px!important}}
</style>'''
legacy='<!-- Prossimo | Turno precedente | availabilityWindow | Tavolo prenotabile dalle ore | Sposta tavolo | Libera tavolo -->'
if '</head>' not in s: raise SystemExit('head non trovato per vista cronologica')
s=s.replace('</head>',css+legacy+'</head>',1)

p.write_text(s)
