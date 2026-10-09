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
  m.querySelector('.atomicChainHead').insertAdjacentHTML('beforeend','<button type="button" class="secondary" data-parking-open>Riorganizza sala</button>');
  m.querySelector('[data-parking-open]').addEventListener('click',startParkingPlanner);
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
  const a0=tm(src.arrival_time);
  const blockEnd=r=>Math.max(effEnd(r.arrival_time,r.expected_end_time,90),tm(r.arrival_time)+(r.forced?90:105))+15;
  const a1=blockEnd(src);
  return links.filter(x=>x.restaurant_tables?.code===code&&x.reservation_id!==resId)
    .map(x=>atomicReservation(x.reservation_id)).filter(Boolean)
    .find(r=>r.status==='confermata'&&!planned.has(r.id)&&overlapsM(a0,a1,tm(r.arrival_time),blockEnd(r)))||null;
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

let parkingDraft=new Map(),parkingBaseline=new Map(),parkingScope=null,parkingFocus=null,parkingBusy=false;
function parkingCodes(id){return [...tableCodesForRes(id)].sort()}
function parkingStart(id){const r=atomicReservation(id);return r?tm(r.arrival_time):null}
function parkingEnd(id){const r=atomicReservation(id);if(!r)return null;return Math.max(effEnd(r.arrival_time,r.expected_end_time,90),tm(r.arrival_time)+(r.forced?90:105))+15}
function parkingConflict(id,codes){
  const a=parkingStart(id),b=parkingEnd(id);
  return [...parkingDraft].some(([other,assigned])=>other!==id&&assigned.length&&assigned.some(c=>codes.includes(c))&&overlapsM(a,b,parkingStart(other),parkingEnd(other)));
}
function startParkingPlanner(){
  const r=atomicReservation(atomicChainStartId)||reservations.find(x=>x.status==='confermata');
  if(!r)return alert('Nessuna prenotazione confermata disponibile.');
  atomicChainPlan=[];parkingDraft=new Map();parkingBaseline=new Map();parkingBusy=false;
  parkingScope={date:r.service_date,service:r.service_code,area:r.area};
  parkingFocus=r.id;atomicChainModal().classList.add('open');renderParkingPlanner();
}
function parkingScopeRows(){return reservations.filter(r=>r.status==='confermata'&&r.service_date===parkingScope.date&&r.service_code===parkingScope.service&&r.area===parkingScope.area)}
function parkingAdd(id){
  const r=atomicReservation(id);if(!r||!parkingScopeRows().some(x=>x.id===id))return;
  if(!parkingDraft.has(id)){parkingDraft.set(id,[]);parkingBaseline.set(id,parkingCodes(id))}
  parkingFocus=id;renderParkingPlanner();
}
function parkingSet(id,codes){
  if(!parkingDraft.has(id))return;
  const allowed=allTables.filter(t=>t.active!==false&&t.area===parkingScope.area).map(t=>t.code);
  if(codes.some(c=>!allowed.includes(c)))return alert('Tavolo non disponibile in questa area.');
  if(parkingConflict(id,codes))return alert('Due prenotazioni parcheggiate si sovrappongono sullo stesso tavolo.');
  parkingDraft.set(id,codes);renderParkingPlanner();
}
function parkingCancel(){parkingDraft.clear();parkingBaseline.clear();parkingFocus=null;parkingScope=null;closeAtomicChainMove()}
function renderParkingPlanner(){
  const body=document.getElementById('atomicChainBody');if(!body||!parkingScope)return;
  const rows=parkingScopeRows(),options=rows.map(r=>'<option value="'+esc(r.id)+'">'+esc(r.guest_name)+' · '+r.party_size+' coperti · '+hhmm(r.arrival_time)+'</option>').join('');
  const parked=[...parkingDraft].map(([id,codes])=>{const r=atomicReservation(id);return '<div class="atomicChainRow"><span>'+esc(r?.guest_name||id)+' · '+(r?.party_size||'')+' coperti · da '+esc(parkingBaseline.get(id).join(', '))+'</span><b>'+(codes.length?esc(codes.join(', ')):'IN PARCHEGGIO')+'</b><button type="button" class="secondary" data-park-focus="'+esc(id)+'">Assegna</button><button type="button" class="secondary" data-park-remove="'+esc(id)+'">Ripristina</button></div>'}).join('');
  const focus=parkingDraft.has(parkingFocus)?atomicReservation(parkingFocus):null;
  const eligible=allTables.filter(t=>t.active!==false&&t.area===parkingScope.area);
  const checks=focus?eligible.map(t=>{const checked=parkingDraft.get(focus.id).includes(t.code);const a=parkingStart(focus.id),b=parkingEnd(focus.id);
    const used=links.some(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==focus.id&&!parkingDraft.has(x.reservation_id)&&(()=>{const r=atomicReservation(x.reservation_id);return r&&r.status==='confermata'&&overlapsM(a,b,tm(r.arrival_time),Math.max(effEnd(r.arrival_time,r.expected_end_time,90),tm(r.arrival_time)+(r.forced?90:105))+15)})());
    return '<label style="display:inline-flex;align-items:center;gap:5px;padding:7px;border:1px solid #ccd;border-radius:8px;margin:3px"><input type="checkbox" data-park-table="'+esc(t.code)+'" '+(checked?'checked ':'')+(used?'disabled ':'')+'/>'+esc(t.label||t.code)+(used?' · occupato':'')+'</label>'}).join(''):'';
  const unresolved=[...parkingDraft].filter(([id,codes])=>!codes.length);
  body.innerHTML='<div class="atomicChainHint"><b>Riorganizza sala · '+esc(parkingScope.date)+'</b><br>Parcheggia più prenotazioni e assegna tutti i tavoli. Nessuna modifica viene salvata fino alla conferma.</div><select id="parkingAddSelect">'+options+'</select><div class="atomicChainActions"><button type="button" data-park-add>Parcheggia prenotazione</button><button type="button" class="secondary" data-park-cancel>Annulla tutto</button></div><div class="atomicChainSummary" style="margin-top:12px">'+(parked||'<div style="padding:12px">Nessuna prenotazione parcheggiata</div>')+'</div>'+(focus?'<h4>Assegna '+esc(focus.guest_name)+' ('+focus.party_size+' coperti)</h4><div>'+checks+'</div><div class="atomicChainActions"><button type="button" data-park-apply>Applica tavoli selezionati</button></div>':'')+'<div class="atomicChainActions"><button type="button" '+(!parkingDraft.size||unresolved.length||parkingBusy?'disabled':'')+' data-park-confirm>Conferma tutti gli spostamenti</button></div>'+(unresolved.length?'<div class="muted">Da assegnare: '+unresolved.length+' prenotazioni</div>':'');
  body.querySelector('[data-park-add]').onclick=()=>parkingAdd(body.querySelector('#parkingAddSelect').value);
  body.querySelector('[data-park-cancel]').onclick=parkingCancel;
  body.querySelectorAll('[data-park-focus]').forEach(b=>b.onclick=()=>{parkingFocus=b.dataset.parkFocus;renderParkingPlanner()});
  body.querySelectorAll('[data-park-remove]').forEach(b=>b.onclick=()=>{parkingDraft.delete(b.dataset.parkRemove);parkingBaseline.delete(b.dataset.parkRemove);parkingFocus=[...parkingDraft.keys()][0]||null;renderParkingPlanner()});
  if(focus)body.querySelector('[data-park-apply]').onclick=()=>parkingSet(focus.id,[...body.querySelectorAll('[data-park-table]:checked')].map(x=>x.dataset.parkTable));
  const btn=body.querySelector('[data-park-confirm]');if(btn)btn.onclick=()=>parkingCommit(false);
}
async function parkingCommit(force){
  if(parkingBusy||!parkingDraft.size||[...parkingDraft.values()].some(x=>!x.length))return;
  parkingBusy=true;
  try{
    const fresh=await db.from('reservation_tables').select('reservation_id,restaurant_tables(code)').in('reservation_id',[...parkingDraft.keys()]);
    if(fresh.error)throw fresh.error;
    for(const [id,baseline] of parkingBaseline){
      const now=fresh.data.filter(x=>x.reservation_id===id).map(x=>x.restaurant_tables?.code).filter(Boolean).sort();
      if(JSON.stringify(now)!==JSON.stringify(baseline))throw Error('I tavoli di una prenotazione sono cambiati su un altro dispositivo. Annulla e riparti dalla situazione aggiornata.');
    }
    const moves=[...parkingDraft].map(([reservation_id,table_codes])=>({reservation_id,table_codes}));
    const result=await db.rpc('move_reservation_tables_batch',{p_moves:moves,p_forced:force});
    if(result.error){
      if(!force&&/forzatura|capienza|massima|consecutiv/i.test(result.error.message||'')&&confirm(result.error.message+'\\nVuoi forzare gli spostamenti?')){parkingBusy=false;return parkingCommit(true)}
      throw result.error;
    }
    parkingCancel();await loadAll();showPage('map',document.querySelector('[data-p="map"]'));alert('Riorganizzazione salvata: '+moves.length+' prenotazioni riassegnate.');
  }catch(e){alert('Nessuna modifica confermata. '+(e.message||e));}
  finally{parkingBusy=false;if(parkingScope)renderParkingPlanner()}
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
