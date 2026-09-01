from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Aggiunge il comando esplicito di modifica tavolo alla riga azioni della prenotazione.
edit_action="actions+='<button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button>';"
move_action="actions+='<button class=\"secondary moveTableBtn\" data-move-booking=\"'+esc(r.id)+'\">Modifica tavolo</button>';\n      "+edit_action
if edit_action in s:
    s=s.replace(edit_action,move_action,1)
else:
    old="<button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button><button class=\"danger\" data-delete-booking=\"'+esc(r.id)+'\">Elimina</button>"
    new="<button class=\"secondary moveTableBtn\" data-move-booking=\"'+esc(r.id)+'\">Modifica tavolo</button><button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button><button class=\"danger\" data-delete-booking=\"'+esc(r.id)+'\">Elimina</button>"
    if old not in s:
        raise SystemExit('Punto inserimento pulsante Modifica tavolo non trovato')
    s=s.replace(old,new,1)

old_listener="$('bookingList').querySelectorAll('[data-edit-booking]').forEach(b=>b.addEventListener('click',()=>editBooking(b.dataset.editBooking)));"
new_listener="$('bookingList').querySelectorAll('[data-move-booking]').forEach(b=>b.addEventListener('click',()=>moveBookingTable(b.dataset.moveBooking)));\n  "+old_listener
if old_listener not in s:
    raise SystemExit('Listener modifica prenotazione non trovato')
s=s.replace(old_listener,new_listener,1)

# In modalità modifica tavolo anche un tavolo occupato resta cliccabile: se è occupato
# viene avviato un passaggio guidato che sposta prima la prenotazione che lo occupa.
old_busy="+(busy?'disabled aria-disabled=\"true\"':'data-table-code=\"'+esc(t.code)+'\"')+"
new_busy="+((busy&& !movingOnly)?'disabled aria-disabled=\"true\"':'data-table-code=\"'+esc(t.code)+'\"')+"
if old_busy in s:
    s=s.replace(old_busy,new_busy,1)

old_click="$('picker').querySelectorAll('[data-table-code]').forEach(b=>b.addEventListener('click',()=>toggleTable(b.dataset.tableCode)));"
new_click="$('picker').querySelectorAll('[data-table-code]').forEach(b=>b.addEventListener('click',()=>movingOnly?handleMoveTableClick(b.dataset.tableCode):toggleTable(b.dataset.tableCode)));"
if old_click not in s:
    raise SystemExit('Listener tavoli picker non trovato')
s=s.replace(old_click,new_click,1)

# Stato dedicato allo spostamento. La modifica normale continua a usare il flusso esistente.
marker="function renderMap(){"
fn=r'''let movingOnly=null;
let movingFromCodes=[];
let chainMove=null;
function moveNotice(html){
  setTimeout(()=>{
    try{
      const summary=document.getElementById('tableSelectionSummary');
      if(summary){
        summary.querySelectorAll('.moveTableNotice').forEach(x=>x.remove());
        const note=document.createElement('div');note.className='moveTableNotice';note.innerHTML=html;summary.prepend(note);
      }
      const picker=document.getElementById('picker');if(picker)picker.scrollIntoView({behavior:'smooth',block:'center'});
    }catch(e){console.warn('Modifica tavolo:',e)}
  },80);
}
function moveBookingTable(id){
  const r=reservations.find(x=>x.id===id);
  if(!r){alert('Prenotazione non trovata.');return}
  chainMove=null;
  const current=tableLabelsForRes(id)||'tavolo attuale';
  editBooking(id);
  movingOnly=id;
  movingFromCodes=tableCodesForRes(id);
  $('room').disabled=true;
  selected=[];
  renderPicker();
  moveNotice('<b>Modifica tavolo</b><div>Attuale: '+esc(current)+'. Tocca il tavolo di destinazione. Se è libero lo puoi scegliere subito; se è occupato, il programma ti farà spostare prima quella prenotazione e poi completerà automaticamente lo spostamento.</div>');
}
function moveConflictFor(code,resId){
  const src=reservations.find(r=>r.id===resId);if(!src)return null;
  const a0=tm(src.arrival_time),a1=effEnd(src.arrival_time,src.expected_end_time,90);
  return links.filter(x=>x.restaurant_tables?.code===code&&x.reservation_id!==resId)
    .map(x=>reservations.find(r=>r.id===x.reservation_id)).filter(Boolean)
    .find(r=>r.status==='confermata'&&overlapsM(a0,a1,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,90)))||null;
}
function handleMoveTableClick(code){
  if(!movingOnly)return toggleTable(code);
  if(movingFromCodes.includes(code))return alert('Questo è già il tavolo attuale della prenotazione. Scegli un altro tavolo.');
  const src=reservations.find(r=>r.id===movingOnly);if(!src)return;
  const conflict=moveConflictFor(code,movingOnly);
  if(conflict){
    if(chainMove)return alert('Per completare questo spostamento scegli adesso un tavolo libero per '+conflict.guest_name+'.');
    const target=allTables.find(t=>t.code===code);const targetLabel=target?.label||code;
    const from=tableLabelsForRes(movingOnly)||'tavolo attuale';
    const occupiedBy=tableLabelsForRes(conflict.id)||targetLabel;
    if(!confirm(targetLabel+' è occupato da '+conflict.guest_name+'.\n\nVuoi spostare prima questa prenotazione su un altro tavolo e poi spostare '+src.guest_name+' da '+from+' a '+targetLabel+'?'))return;
    chainMove={sourceId:movingOnly,targetCode:code,targetLabel,displacedId:conflict.id,sourceName:src.guest_name};
    editBooking(conflict.id);
    movingOnly=conflict.id;
    movingFromCodes=tableCodesForRes(conflict.id);
    $('room').disabled=true;
    selected=[];
    renderPicker();
    moveNotice('<b>Libera '+esc(targetLabel)+'</b><div>'+esc(conflict.guest_name)+' è su '+esc(occupiedBy)+'. Scegli adesso un <b>tavolo libero</b> per questa prenotazione e premi Salva prenotazione. Subito dopo il programma sposterà automaticamente '+esc(src.guest_name)+' su '+esc(targetLabel)+'.</div>');
    return;
  }
  toggleTable(code);
}
'''
if 'function moveBookingTable(id)' not in s:
    if marker not in s:
        raise SystemExit('renderMap non trovato')
    s=s.replace(marker,fn+'\n'+marker,1)
else:
    raise SystemExit('Patch modifica tavolo già presente nel sorgente base')

# Nuova prenotazione / modifica normale: escono sempre dalla modalità spostamento.
s=s.replace('function openBooking(){','function openBooking(){movingOnly=null;movingFromCodes=[];chainMove=null;if($(\'room\'))$(\'room\').disabled=false;',1)
s=s.replace('function editBooking(id){','function editBooking(id){movingOnly=null;movingFromCodes=[];if($(\'room\'))$(\'room\').disabled=false;',1)
s=s.replace("function closeBooking(){$('modal').classList.remove('open')}","function closeBooking(){movingOnly=null;movingFromCodes=[];chainMove=null;if($('room'))$('room').disabled=false;$('modal').classList.remove('open')}",1)

# In modalità spostamento usa l'RPC dedicato. Nel caso guidato, dopo aver liberato
# il tavolo di destinazione sposta automaticamente anche la prenotazione originaria.
save_marker='async function saveBooking(force){'
move_save=r'''async function saveBooking(force){
  $('saveMsg').style.display='none';
  if(movingOnly&&editing===movingOnly){
    if(!selected.length)return alert('Seleziona il nuovo tavolo.');
    if(chainMove){
      for(const c of selected){if(moveConflictFor(c,movingOnly))return alert('Scegli un tavolo libero per completare lo spostamento guidato.');}
    }
    let q=await db.rpc('move_reservation_tables',{p_reservation_id:editing,p_table_codes:selected,p_forced:force});
    if(q.error){
      let t=q.error.message||'';
      if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura')||t.toLowerCase().includes('non sono consecutivi')||t.toLowerCase().includes('associarli comunque'))){
        let ask=(t.toLowerCase().includes('non sono consecutivi')||t.toLowerCase().includes('associarli comunque'))?'I tavoli selezionati non sono consecutivi. Vuoi associarli comunque?':t+'\n\nVuoi comunque forzare questo spostamento?';
        if(confirm(ask))return saveBooking(true);
      }
      $('saveMsg').style.display='block';$('saveMsg').textContent=t;return;
    }
    if(chainMove&&editing===chainMove.displacedId){
      const cm=chainMove;
      let q2=await db.rpc('move_reservation_tables',{p_reservation_id:cm.sourceId,p_table_codes:[cm.targetCode],p_forced:false});
      if(q2.error){
        const msg=q2.error.message||'errore sconosciuto';
        chainMove=null;movingOnly=null;movingFromCodes=[];closeBooking();await loadAll();
        return alert('Il tavolo '+cm.targetLabel+' è stato liberato, ma lo spostamento di '+cm.sourceName+' non è riuscito: '+msg+'\n\nPuoi ora usare Modifica tavolo sulla prenotazione originale e scegliere '+cm.targetLabel+'.');
      }
      chainMove=null;movingOnly=null;movingFromCodes=[];closeBooking();await loadAll();showPage('map',document.querySelector('[data-p="map"]'));
      alert('Spostamento completato: '+cm.sourceName+' è ora su '+cm.targetLabel+'.');
      return;
    }
    movingOnly=null;movingFromCodes=[];chainMove=null;closeBooking();await loadAll();showPage('map',document.querySelector('[data-p="map"]'));return;
  }
'''
if save_marker not in s:
    raise SystemExit('saveBooking non trovata')
s=s.replace(save_marker,move_save,1)

# Espone le funzioni dal modulo ES.
m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m:
    raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
for name in ['moveBookingTable','handleMoveTableClick']:
    if name not in items: items=items.rstrip()+','+name
repl='Object.assign(window,{'+items+'});'
s=s[:m.start()]+repl+s[m.end():]

css='''<style id="marino-manual-table-move">
.moveTableNotice{margin:0 0 10px;padding:10px 12px;border:2px solid #d8a52f;border-radius:12px;background:#fff8e8;color:#102c45;font-size:13px;line-height:1.35}
.moveTableNotice b{display:block;color:#063f78;margin-bottom:3px}
.moveTableBtn{font-weight:900}
@media(max-width:720px){[data-move-booking]{min-height:38px}.moveTableNotice{font-size:12px;padding:9px 10px}}
</style>'''
if 'id="marino-manual-table-move"' not in s:
    if '</head>' not in s: raise SystemExit('head non trovato')
    s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
