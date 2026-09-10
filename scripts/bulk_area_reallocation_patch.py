from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Aggiunge ai gruppi giornalieri della lista Prenotazioni i comandi per
# riallocare atomicamente un intero servizio da Interno a Dehors e viceversa.
old="""    return '<section class=\"chronoDay\"><div class=\"chronoDayHead\"><div><b>'+esc(title)+'</b><span>'+covers+' '+(covers===1?'coperto prenotato':'coperti prenotati')+'</span></div></div>'+(rows.length?'<div class=\"chronoDayList\">'+cards+'</div>':'')+'</section>';"""
new="""    let bulkBtns=[...new Set(rows.filter(r=>r.status==='confermata').map(r=>r.service_code))].map(sc=>'<div class=\"bulkAreaService\"><span>'+serviceLabel(sc)+'</span><button type=\"button\" class=\"secondary bulkAreaBtn\" data-bulk-area=\"interno\" data-bulk-date=\"'+esc(iso)+'\" data-bulk-service=\"'+esc(sc)+'\">→ Interno</button><button type=\"button\" class=\"secondary bulkAreaBtn\" data-bulk-area=\"dehors\" data-bulk-date=\"'+esc(iso)+'\" data-bulk-service=\"'+esc(sc)+'\">→ Esterno</button></div>').join('');
    return '<section class=\"chronoDay\"><div class=\"chronoDayHead\"><div><b>'+esc(title)+'</b><span>'+covers+' '+(covers===1?'coperto prenotato':'coperti prenotati')+'</span></div>'+(bulkBtns?'<div class=\"bulkAreaControls\">'+bulkBtns+'</div>':'')+'</div>'+(rows.length?'<div class=\"chronoDayList\">'+cards+'</div>':'')+'</section>';"""
if old not in s:
    raise SystemExit('Intestazione giorno prenotazioni non trovata per riallocazione area')
s=s.replace(old,new,1)

listener="""  host.querySelectorAll('[data-cancel-chrono]').forEach(b=>b.addEventListener('click',()=>cancelBookingFromList(b.dataset.cancelChrono)));"""
listener_new=listener+"""
  host.querySelectorAll('[data-bulk-area]').forEach(b=>b.addEventListener('click',async()=>{
    if(b.disabled)return;b.disabled=true;
    try{await bulkReallocateServiceArea(b.dataset.bulkDate,b.dataset.bulkService,b.dataset.bulkArea)}finally{b.disabled=false}
  }));"""
if listener not in s:
    raise SystemExit('Listener lista prenotazioni non trovato per riallocazione area')
s=s.replace(listener,listener_new,1)

helpers=r'''
function bulkAreaMin(t){const x=String(t||'00:00').slice(0,5).split(':').map(Number);return x[0]*60+x[1]}
function bulkAreaWindow(r){
  const a=bulkAreaMin(r.arrival_time), minDur=r.forced?90:105;
  const explicit=r.expected_end_time?bulkAreaMin(r.expected_end_time):a+minDur;
  return [a,Math.max(explicit,a+minDur)+15];
}
function bulkAreaOverlap(a,b){const x=bulkAreaWindow(a),y=bulkAreaWindow(b);return x[0]<y[1]&&y[0]<x[1]}
function bulkAreaActive(area){return allTables.filter(t=>t.active!==false&&t.area===area).sort((a,b)=>(a.sort_order||0)-(b.sort_order||0))}
function bulkAreaRange(area,codes){
  const ts=codes.map(c=>allTables.find(t=>t.code===c)).filter(Boolean),n=ts.length;
  if(area==='dehors')return n===1?[1,4,4]:n===2?[4,8,8]:[2*n+1,2*n+2,2*n+2];
  const groups=g=>ts.filter(t=>t.group_name===g).length;
  const pc=groups('panca_principale'),qc=groups('quadrati'),lc=groups('bancone_sinistra'),p56=groups('bancone_56'),rc=groups('rotondi');
  if(n===1)return [Number(ts[0].single_min_covers||1),Number(ts[0].single_max_covers||1),Number(ts[0].single_max_covers||1)];
  if(lc===n)return [1,n===2?4:7,n===2?4:7];
  if(p56===n&&n===2)return [1,4,4];
  if(qc===n){const mn=n===2?4:n===3?7:n===4?9:11,mx=n===2?6:n===3?8:n===4?10:12;return [mn,mx,mx]}
  if(pc===n){const mx=n===1?3:Math.min(14,2*n+2);return [n===1?1:2*n,mx,mx]}
  if(pc>0&&qc>0&&pc+qc===n){const pm=pc===1?3:Math.min(14,2*pc+2),mx=Math.min(16,pm+2*qc),hard=Math.min(18,pm+4*qc);return [1,mx,hard]}
  const mn=ts.reduce((a,t)=>a+Number(t.single_min_covers||1),0),mx=ts.reduce((a,t)=>a+Number(t.single_max_covers||1),0);return [Math.max(1,mn),mx,mx]
}
function bulkAreaComb(arr,k,limit=80){
  const out=[];function rec(start,pick){if(out.length>=limit)return;if(pick.length===k){out.push([...pick]);return}for(let i=start;i<=arr.length-(k-pick.length);i++){pick.push(arr[i]);rec(i+1,pick);pick.pop();if(out.length>=limit)return}}rec(0,[]);return out
}
function bulkAreaInternalCandidates(r){
  const party=Number(r.party_size||0),tables=bulkAreaActive('interno'),by=c=>tables.find(t=>t.code===c),out=[],seen=new Set();
  const add=codes=>{codes=codes.filter(c=>by(c));if(!codes.length)return;const key=codes.join('|');if(seen.has(key))return;const [mn,mx,hard]=bulkAreaRange('interno',codes);if(party<mn||party>(r.forced?hard:mx))return;seen.add(key);out.push({codes,mn,mx,hard,waste:(r.forced?hard:mx)-party})};
  tables.forEach(t=>{if(!['B5','B6'].includes(t.code))add([t.code])});
  [['B1','B2'],['B1','B3'],['B2','B3'],['B1','B2','B3'],['B5','B6'],['PR1','PR2']].forEach(add);
  const p=tables.filter(t=>t.group_name==='panca_principale').map(t=>t.code),q=tables.filter(t=>t.group_name==='quadrati').map(t=>t.code);
  for(let n=2;n<=p.length;n++)for(let i=0;i<=p.length-n;i++)add(p.slice(i,i+n));
  for(let n=2;n<=q.length;n++)for(let i=0;i<=q.length-n;i++)add(q.slice(i,i+n));
  if(p.length>=6)q.forEach(sq=>add([p[0],p[1],p[2],p[3],p[4],p[5],sq]));
  out.sort((a,b)=>a.waste-b.waste||a.codes.length-b.codes.length||a.codes.join('').localeCompare(b.codes.join('')));
  return out;
}
function bulkAreaPlan(rows,target){
  const bookings=[...rows].sort((a,b)=>Number(b.party_size||0)-Number(a.party_size||0)||String(a.arrival_time).localeCompare(String(b.arrival_time)));
  const used=new Map(),plan=[],maxSteps=60000;let steps=0;
  const freeFor=(codes,r)=>codes.every(c=>!(used.get(c)||[]).some(x=>bulkAreaOverlap(x,r)));
  const reserve=(codes,r)=>codes.forEach(c=>{const a=used.get(c)||[];a.push(r);used.set(c,a)});
  const release=(codes,r)=>codes.forEach(c=>{const a=(used.get(c)||[]).filter(x=>x.id!==r.id);if(a.length)used.set(c,a);else used.delete(c)});
  function options(r){
    if(target==='interno')return bulkAreaInternalCandidates(r).map(x=>x.codes).filter(c=>freeFor(c,r));
    const party=Number(r.party_size||0),n=party<=4?1:party<=8?2:Math.ceil((party-2)/2),available=bulkAreaActive('dehors').map(t=>t.code).filter(c=>freeFor([c],r));
    if(available.length<n)return [];
    if(n===1)return available.slice(0,22).map(c=>[c]);
    let opts=[];for(let i=0;i<=available.length-n&&opts.length<40;i++)opts.push(available.slice(i,i+n));
    if(opts.length<40)opts.push(...bulkAreaComb(available,n,40-opts.length));
    return opts;
  }
  function rec(i){
    if(++steps>maxSteps)return false;if(i>=bookings.length)return true;
    const r=bookings[i],opts=options(r);for(const codes of opts){reserve(codes,r);plan.push({reservation_id:r.id,table_codes:codes,guest_name:r.guest_name,party_size:r.party_size});if(rec(i+1))return true;plan.pop();release(codes,r)}return false;
  }
  return rec(0)?plan:null;
}
async function bulkReallocateServiceArea(date,service,target){
  const label=target==='interno'?'INTERNO':'ESTERNO';
  const rq=await db.from('reservations').select('*').eq('service_date',date).eq('service_code',service).eq('status','confermata').order('arrival_time');
  if(rq.error)return alert('Errore caricamento prenotazioni: '+rq.error.message);
  const rows=rq.data||[];if(!rows.length)return alert('Non ci sono prenotazioni confermate da riallocare per questo servizio.');
  const plan=bulkAreaPlan(rows,target);
  if(!plan){return alert('Non riesco a sistemare tutte le prenotazioni in '+label+' rispettando capienze, combinazioni dei tavoli e sovrapposizioni orarie. Nessuna prenotazione è stata modificata.');}
  const names=plan.slice(0,12).map(x=>'• '+x.guest_name+' ('+x.party_size+') → '+x.table_codes.map(c=>allTables.find(t=>t.code===c)?.label||c).join(' + ')).join('\n');
  const extra=plan.length>12?'\n… e altre '+(plan.length-12)+' prenotazioni.':'';
  if(!confirm('Riallocare TUTTE le '+rows.length+' prenotazioni del servizio in '+label+'?\n\nIl sistema cambierà anche l’area principale del servizio in '+label+' e riassegnerà i tavoli. Nomi, orari, coperti e note resteranno invariati.\n\n'+names+extra))return;
  const moves=plan.map(x=>({reservation_id:x.reservation_id,table_codes:x.table_codes}));
  const q=await db.rpc('reallocate_reservations_area_batch',{p_service_date:date,p_service_code:service,p_target_area:target,p_moves:moves});
  if(q.error)return alert('Nessuna modifica applicata.\n\n'+(q.error.message||'Errore nella riallocazione.'));
  if($('date')?.value===date){$('date').value=date;serviceOptions();if([...$('service').options].some(o=>o.value===service))$('service').value=service;await loadAll()}
  await renderBookings();
  alert('Riallocazione completata: '+rows.length+' prenotazioni spostate in '+label+'. Tutti i dati delle prenotazioni sono rimasti invariati; sono cambiati soltanto area e tavoli.');
}
'''
marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('_renderMapBase non trovata per riallocazione area')
s=s.replace(marker,helpers+'\n'+marker,1)

m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m:
    raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
if 'bulkReallocateServiceArea' not in items:
    items=items.rstrip()+',bulkReallocateServiceArea'
s=s[:m.start()]+'Object.assign(window,{'+items+'});'+s[m.end():]

css=r'''<style id="marino-bulk-area-reallocation">
.bulkAreaControls{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;padding-top:8px;border-top:1px solid #d8e5ef}.bulkAreaService{display:flex;align-items:center;gap:5px}.bulkAreaService>span{font-size:10px;font-weight:900;color:#526574;text-transform:uppercase}.bulkAreaBtn{min-height:32px!important;padding:5px 9px!important;font-size:10px!important;font-weight:900!important;white-space:nowrap}.bulkAreaBtn[data-bulk-area="interno"]{border-color:#063f78!important;color:#063f78!important}.bulkAreaBtn[data-bulk-area="dehors"]{border-color:#c65300!important;color:#9d4200!important}@media(max-width:720px){.bulkAreaControls{gap:5px}.bulkAreaService{width:100%}.bulkAreaService>span{width:42px;flex:0 0 42px}.bulkAreaBtn{flex:1;min-height:34px!important}}
</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato per stile riallocazione area')
s=s.replace('</head>',css+'</head>',1)

for required in ['bulkReallocateServiceArea','reallocate_reservations_area_batch','data-bulk-area','marino-bulk-area-reallocation']:
    if required not in s: raise SystemExit('Riallocazione area incompleta: '+required)

p.write_text(s)
