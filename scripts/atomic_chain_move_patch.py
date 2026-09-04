from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

old="function moveBookingTable(id){\n  const r=reservations.find(x=>x.id===id);"
new="function moveBookingTable(id){return startAtomicChainMove(id);}\nfunction legacyMoveBookingTable_UNUSED(id){\n  const r=reservations.find(x=>x.id===id);"
if old not in s:
    raise SystemExit('moveBookingTable originale non trovato')
s=s.replace(old,new,1)

insert=r'''
let atomicChainPlan=[];
let atomicChainCurrentId=null;
let atomicChainStartId=null;
function atomicChainModal(){
  let m=document.getElementById('atomicChainMoveModal');
  if(m)return m;
  m=document.createElement('div');
  m.id='atomicChainMoveModal';
  m.className='atomicChainOverlay';
  m.innerHTML='<div class="atomicChainCard"><div class="atomicChainHead"><b>Riorganizza tavoli</b><button type="button" class="secondary" data-chain-close>×</button></div><div id="atomicChainBody"></div></div>';
  document.body.appendChild(m);
  m.querySelector('[data-chain-close]').addEventListener('click',closeAtomicChainMove);
  m.addEventListener('click',e=>{if(e.target===m)closeAtomicChainMove()});
  return m;
}
function closeAtomicChainMove(){
  const m=document.getElementById('atomicChainMoveModal');
  if(m)m.classList.remove('open');
  atomicChainPlan=[];atomicChainCurrentId=null;atomicChainStartId=null;
}
function atomicReservation(id){return reservations.find(r=>r.id===id)||null}
function atomicCurrentLabels(id){return tableLabelsForRes(id)||'Tavolo da assegnare'}
function atomicTableLabel(code){return allTables.find(t=>t.code===code)?.label||code}
function atomicPlannedIds(){return new Set(atomicChainPlan.map(x=>x.reservation_id))}
function atomicConflict(code,resId){
  const src=atomicReservation(resId);if(!src)return null;
  const planned=atomicPlannedIds();
  const a0=tm(src.arrival_time),a1=effEnd(src.arrival_time,src.expected_end_time,90);
  return links.filter(x=>x.restaurant_tables?.code===code&&x.reservation_id!==resId)
    .map(x=>atomicReservation(x.reservation_id)).filter(Boolean)
    .find(r=>r.status==='confermata'&&!planned.has(r.id)&&overlapsM(a0,a1,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,90)))||null;
}
function atomicDestinationOptions(r){
  const current=new Set(tableCodesForRes(r.id));
  return allTables.filter(t=>t.active!==false&&t.area===r.area&&!current.has(t.code)).map(t=>{
    const c=atomicConflict(t.code,r.id);
    const occ=c?' · occupato da '+c.guest_name:'';
    return '<option value="'+esc(t.code)+'">'+esc(t.label||t.code)+esc(occ)+'</option>';
  }).join('');
}
function startAtomicChainMove(id){
  const r=atomicReservation(id);if(!r)return alert('Prenotazione non trovata.');
  atomicChainPlan=[];atomicChainCurrentId=id;atomicChainStartId=id;
  const m=atomicChainModal();m.classList.add('open');renderAtomicChainStep();
}
function renderAtomicChainStep(){
  const body=document.getElementById('atomicChainBody');if(!body)return;
  const r=atomicReservation(atomicChainCurrentId);if(!r)return closeAtomicChainMove();
  const opts=atomicDestinationOptions(r);
  const intro=atomicChainPlan.length
    ? '<div class="atomicChainHint"><b>'+esc(atomicCurrentLabels(r.id))+' è occupato da '+esc(r.guest_name)+'.</b><br>Dove vuoi spostare questa prenotazione?</div>'
    : '<div class="atomicChainHint"><b>Sposta '+esc(r.guest_name)+'</b><br>Attuale: '+esc(atomicCurrentLabels(r.id))+'. Scegli il tavolo di destinazione, anche se è già occupato.</div>';
  body.innerHTML=intro+'<label class="atomicChainLabel">Tavolo di destinazione</label><select id="atomicChainTarget">'+opts+'</select><div class="atomicChainActions"><button type="button" class="secondary" data-chain-cancel>Annulla</button><button type="button" data-chain-next>Continua</button></div>';
  body.querySelector('[data-chain-cancel]').addEventListener('click',closeAtomicChainMove);
  body.querySelector('[data-chain-next]').addEventListener('click',advanceAtomicChainMove);
}
function advanceAtomicChainMove(){
  const r=atomicReservation(atomicChainCurrentId);if(!r)return;
  const sel=document.getElementById('atomicChainTarget');const code=sel?.value;if(!code)return alert('Scegli un tavolo di destinazione.');
  if(atomicChainPlan.some(x=>x.reservation_id===r.id))return alert('Questa prenotazione è già presente nella catena.');
  atomicChainPlan.push({reservation_id:r.id,table_codes:[code],from_label:atomicCurrentLabels(r.id),to_label:atomicTableLabel(code),guest_name:r.guest_name});
  const conflict=atomicConflict(code,r.id);
  if(conflict){atomicChainCurrentId=conflict.id;renderAtomicChainStep();return}
  renderAtomicChainSummary();
}
function renderAtomicChainSummary(){
  const body=document.getElementById('atomicChainBody');if(!body)return;
  const rows=atomicChainPlan.map((x,i)=>'<div class="atomicChainRow"><span>'+(i+1)+'. '+esc(x.guest_name)+'</span><b>'+esc(x.from_label)+' → '+esc(x.to_label)+'</b></div>').join('');
  body.innerHTML='<div class="atomicChainHint"><b>Controlla prima di confermare</b><br>Le prenotazioni restano invariate: cambiano soltanto i tavoli. L’operazione viene eseguita tutta insieme.</div><div class="atomicChainSummary">'+rows+'</div><div class="atomicChainActions"><button type="button" class="secondary" data-chain-back>Indietro</button><button type="button" data-chain-confirm>Conferma spostamenti</button></div>';
  body.querySelector('[data-chain-back]').addEventListener('click',()=>{const last=atomicChainPlan.pop();atomicChainCurrentId=last?.reservation_id||atomicChainStartId;renderAtomicChainStep()});
  body.querySelector('[data-chain-confirm]').addEventListener('click',()=>confirmAtomicChainMove(false));
}
async function confirmAtomicChainMove(force){
  if(!atomicChainPlan.length)return;
  const moves=atomicChainPlan.map(x=>({reservation_id:x.reservation_id,table_codes:x.table_codes}));
  const body=document.getElementById('atomicChainBody');
  if(body)body.innerHTML='<div class="atomicChainHint"><b>Applicazione spostamenti…</b><br>Non chiudere questa schermata.</div>';
  const q=await db.rpc('move_reservation_tables_batch',{p_moves:moves,p_forced:force});
  if(q.error){
    const t=q.error.message||'Errore durante lo spostamento.';
    if(!force&&(t.toLowerCase().includes('forzatura')||t.toLowerCase().includes('capienza')||t.toLowerCase().includes('massima')||t.toLowerCase().includes('consecutiv'))){
      if(confirm(t+'\n\nVuoi forzare l’intera catena di spostamenti?'))return confirmAtomicChainMove(true);
    }
    alert('Nessuno spostamento è stato applicato.\n\n'+t);
    renderAtomicChainSummary();return;
  }
  closeAtomicChainMove();
  await loadAll();
  showPage('map',document.querySelector('[data-p="map"]'));
  alert('Spostamenti completati. Tutte le prenotazioni sono rimaste disponibili e sono stati modificati soltanto i tavoli.');
}
'''
marker='function renderMap(){'
if marker not in s:
    raise SystemExit('renderMap non trovato per atomic chain')
s=s.replace(marker,insert+'\n'+marker,1)

css=r'''<style id="marino-atomic-chain-move">
.atomicChainOverlay{position:fixed;inset:0;z-index:10050;background:rgba(3,18,31,.62);display:none;align-items:center;justify-content:center;padding:18px}.atomicChainOverlay.open{display:flex}.atomicChainCard{width:min(560px,100%);max-height:88dvh;overflow:auto;background:#fff;border-radius:18px;box-shadow:0 18px 60px rgba(0,0,0,.28);padding:14px}.atomicChainHead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}.atomicChainHead>b{font-size:19px;color:#063f78}.atomicChainHead button{width:38px;min-width:38px;padding:0}.atomicChainHint{padding:10px 12px;border-radius:12px;background:#eef5fb;border:1px solid #c9dceb;color:#102c45;line-height:1.35;margin-bottom:12px}.atomicChainLabel{display:block;font-size:12px;font-weight:900;color:#526574;margin:0 0 5px}.atomicChainCard select{width:100%;min-height:46px;font-size:15px}.atomicChainActions{display:flex;gap:8px;margin-top:14px}.atomicChainActions button{flex:1;min-height:44px}.atomicChainSummary{border:1px solid #dfe8ef;border-radius:12px;overflow:hidden}.atomicChainRow{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 11px;border-bottom:1px solid #edf1f4}.atomicChainRow:last-child{border-bottom:0}.atomicChainRow span{font-size:12px;color:#526574}.atomicChainRow b{font-size:13px;color:#102c45;text-align:right}@media(max-width:720px){.atomicChainOverlay{padding:10px}.atomicChainCard{border-radius:14px;padding:12px;max-height:92dvh}.atomicChainHead>b{font-size:17px}.atomicChainHint{font-size:12px}.atomicChainRow{align-items:flex-start;flex-direction:column;gap:3px}.atomicChainRow b{text-align:left}.atomicChainActions button{font-size:12px}}
</style>'''
if '</head>' not in s: raise SystemExit('head non trovato atomic chain')
s=s.replace('</head>',css+'</head>',1)

if 'move_reservation_tables_batch' not in s or 'Conferma spostamenti' not in s:
    raise SystemExit('atomic chain non inserita')

p.write_text(s)
