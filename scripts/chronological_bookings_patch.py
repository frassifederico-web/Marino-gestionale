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
      let state=r.status==='completata'?'<span class="presenceBadge completedBadge">LIBERATO</span>':r.arrived_at?'<span class="presenceBadge arrivedBadge">ARRIVATO</span>':'';
      let arriveAction='';
      if(r.status==='confermata'){
        arriveAction=r.arrived_at
          ? '<button class="secondary chronoActionBtn chronoArriveToggle chronoArrived" title="Segna da arrivare" aria-label="Segna cliente da arrivare" data-chrono-unarrive="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'"><span class="chronoActionIcon">↩</span></button>'
          : '<button class="arriveBtn chronoActionBtn chronoArriveToggle" title="Arrivato" aria-label="Segna cliente arrivato" data-chrono-arrive="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'"><span class="chronoActionIcon">✓</span></button>';
      }
      return '<div class="chronoBookingRow"><div class="chronoBookingMain"><div class="chronoGuestLine"><span class="reservationNo">#'+reservationDisplayNo(r)+'</span><strong class="chronoGuestName">'+esc(r.guest_name)+'</strong>'+state+'</div><div class="chronoCoreInfo"><span class="chronoTime">'+hhmm(r.arrival_time)+'</span><span class="chronoCovers">'+Number(r.party_size||0)+' coperti</span></div><div class="muted">'+serviceLabel(r.service_code)+' · '+esc(labelsFor(r.id)||'Tavolo da assegnare')+' · '+esc(r.area||'')+'</div></div><div class="chronoQuickActions">'+arriveAction+'<button class="secondary chronoActionBtn chronoOpenBtn" title="Modifica" aria-label="Modifica prenotazione" data-modify-chrono="'+esc(r.id)+'" data-date="'+esc(r.service_date)+'" data-service="'+esc(r.service_code)+'"><span class="chronoActionIcon">✎</span></button><button class="danger chronoActionBtn chronoCancelBtn" title="Annulla" aria-label="Annulla prenotazione" data-cancel-chrono="'+esc(r.id)+'"><span class="chronoActionIcon">×</span></button></div></div>';
    }).join('');
    return '<section class="chronoDay"><div class="chronoDayHead"><div><b>'+esc(title)+'</b><span>'+covers+' '+(covers===1?'coperto prenotato':'coperti prenotati')+'</span></div></div>'+(rows.length?'<div class="chronoDayList">'+cards+'</div>':'')+'</section>';
  }).join('');
  host.querySelectorAll('[data-modify-chrono]').forEach(b=>b.addEventListener('click',()=>openChronologicalBooking(b.dataset.modifyChrono,b.dataset.date,b.dataset.service)));
  host.querySelectorAll('[data-chrono-arrive]').forEach(b=>b.addEventListener('click',()=>setChronologicalArrival(b.dataset.chronoArrive,true,b.dataset.date)));
  host.querySelectorAll('[data-chrono-unarrive]').forEach(b=>b.addEventListener('click',()=>setChronologicalArrival(b.dataset.chronoUnarrive,false,b.dataset.date)));
  host.querySelectorAll('[data-cancel-chrono]').forEach(b=>b.addEventListener('click',()=>cancelBookingFromList(b.dataset.cancelChrono)));
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
function removeChronologicalEditActions(){document.getElementById('chronoEditManagement')?.remove()}
function showChronologicalEditActions(id){
  removeChronologicalEditActions();
  const modal=document.querySelector('#modal .box');
  const picker=$('picker');
  if(!modal||!picker)return;
  const bar=document.createElement('div');
  bar.id='chronoEditManagement';
  bar.className='chronoEditManagement';
  bar.innerHTML='<button type="button" class="secondary" data-edit-change-day>📅 Cambia giorno</button><button type="button" class="secondary" data-edit-move-table>↔ Sposta tavolo</button>';
  picker.parentNode.insertBefore(bar,picker);
  bar.querySelector('[data-edit-change-day]').addEventListener('click',()=>changeBookingDate(id));
  bar.querySelector('[data-edit-move-table]').addEventListener('click',()=>{removeChronologicalEditActions();moveBookingTable(id)});
}
async function openChronologicalBooking(id,date,service){
  $('date').value=date;
  serviceOptions();
  if([...$('service').options].some(o=>o.value===service))$('service').value=service;
  await loadAll();
  editBooking(id);
  showChronologicalEditActions(id);
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
.chronoDay{margin:0 0 12px;border:1px solid #dfe8ef;border-radius:14px;overflow:hidden;background:#fff}
.chronoDayHead{padding:10px 12px;background:#eef5fb;border-bottom:1px solid #dfe8ef;text-transform:capitalize}
.chronoDayHead>div{display:flex;align-items:center;justify-content:space-between;gap:10px}
.chronoDayHead b{font-size:15px;color:#063f78}.chronoDayHead span{font-size:11px;font-weight:800;color:#526574}
.chronoDayList{padding:0 10px}.chronoBookingRow{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 1px;border-bottom:1px solid #edf1f4}.chronoBookingRow:last-child{border-bottom:0}
.chronoBookingMain{min-width:0;flex:1}.chronoGuestLine{display:flex;align-items:center;gap:6px;min-width:0}.chronoGuestName{font-size:15px;line-height:1.15;color:#063f78;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.reservationNo{flex:0 0 auto}.chronoCoreInfo{display:flex;align-items:baseline;gap:8px;margin-top:4px}.chronoTime{font-size:17px;line-height:1;font-weight:900;color:#102c45;font-variant-numeric:tabular-nums}.chronoCovers{font-size:13px;font-weight:900;color:#102c45}.chronoBookingMain .muted{font-size:11px;line-height:1.25;margin-top:4px}.chronoQuickActions{display:flex;align-items:center;justify-content:flex-end;gap:5px;flex:0 0 auto}.chronoActionBtn{width:38px!important;height:38px!important;min-width:38px!important;min-height:38px!important;padding:0!important;border-radius:10px!important;display:inline-flex!important;align-items:center!important;justify-content:center!important}.chronoActionIcon{font-size:18px;line-height:1;font-weight:900}.chronoArrived{background:#eef2f5!important;color:#34404a!important;border-color:#aeb6bd!important}.chronoCancelBtn{font-size:18px}.presenceBadge{margin-left:1px!important;font-size:7px!important;padding:2px 4px!important;letter-spacing:.02em!important;flex:0 0 auto}.chronoEditManagement{display:flex;gap:8px;margin:12px 0 10px;padding:10px;border:1px solid #d7e1ea;border-radius:12px;background:#f4f8fb}.chronoEditManagement button{flex:1;min-height:42px;font-size:12px}
@media(max-width:720px){.chronoDay{margin-bottom:8px}.chronoDayHead{padding:8px 9px}.chronoDayHead b{font-size:14px}.chronoDayHead span{font-size:10px}.chronoDayList{padding:0 8px}.chronoBookingRow{align-items:center;padding:9px 0;gap:7px}.chronoGuestName{font-size:14px}.chronoTime{font-size:16px}.chronoCovers{font-size:12px}.chronoBookingMain .muted{font-size:10px}.chronoQuickActions{gap:4px}.chronoActionBtn{width:34px!important;height:34px!important;min-width:34px!important;min-height:34px!important;border-radius:9px!important}.chronoActionIcon{font-size:16px}.presenceBadge{font-size:6.8px!important;padding:2px 3px!important}.chronoEditManagement{gap:6px;padding:8px}.chronoEditManagement button{min-height:40px;font-size:11px}}
@media(max-width:390px){.chronoDayList{padding:0 6px}.chronoBookingRow{gap:5px}.chronoGuestName{font-size:13px}.chronoTime{font-size:15px}.chronoCovers{font-size:11px}.chronoBookingMain .muted{font-size:9.5px}.chronoQuickActions{gap:3px}.chronoActionBtn{width:31px!important;height:31px!important;min-width:31px!important;min-height:31px!important}.chronoActionIcon{font-size:15px}}
</style>'''
legacy='<!-- Prossimo | Turno precedente | availabilityWindow | Tavolo prenotabile dalle ore | Sposta tavolo | Libera tavolo -->'
if '</head>' not in s: raise SystemExit('head non trovato per vista cronologica')
s=s.replace('</head>',css+legacy+'</head>',1)

p.write_text(s)
