from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Aggiunge il comando esplicito di spostamento alla riga azioni della prenotazione.
edit_action="actions+='<button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button>';"
move_action="actions+='<button class=\"secondary moveTableBtn\" data-move-booking=\"'+esc(r.id)+'\">Sposta tavolo</button>';\n      "+edit_action
if edit_action in s:
    s=s.replace(edit_action,move_action,1)
else:
    old="<button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button><button class=\"danger\" data-delete-booking=\"'+esc(r.id)+'\">Elimina</button>"
    new="<button class=\"secondary moveTableBtn\" data-move-booking=\"'+esc(r.id)+'\">Sposta tavolo</button><button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button><button class=\"danger\" data-delete-booking=\"'+esc(r.id)+'\">Elimina</button>"
    if old not in s:
        raise SystemExit('Punto inserimento pulsante Sposta tavolo non trovato')
    s=s.replace(old,new,1)

old_listener="$('bookingList').querySelectorAll('[data-edit-booking]').forEach(b=>b.addEventListener('click',()=>editBooking(b.dataset.editBooking)));"
new_listener="$('bookingList').querySelectorAll('[data-move-booking]').forEach(b=>b.addEventListener('click',()=>moveBookingTable(b.dataset.moveBooking)));\n  "+old_listener
if old_listener not in s:
    raise SystemExit('Listener modifica prenotazione non trovato')
s=s.replace(old_listener,new_listener,1)

# Stato dedicato allo spostamento. La modifica normale continua a usare il flusso esistente.
# IMPORTANTE: appena si entra in Sposta tavolo la selezione viene azzerata.
# In questo modo il tavolo precedente NON resta selezionato insieme al nuovo:
# l'utente sceglie da zero la nuova destinazione e il salvataggio sostituisce l'associazione.
marker="function renderMap(){"
fn=r'''let movingOnly=null;
function moveBookingTable(id){
  const r=reservations.find(x=>x.id===id);
  if(!r){alert('Prenotazione non trovata.');return}
  const current=tableLabelsForRes(id)||'tavolo attuale';
  editBooking(id);
  movingOnly=id;
  $('room').disabled=true;
  selected=[];
  renderPicker();
  setTimeout(()=>{
    try{
      const summary=document.getElementById('tableSelectionSummary');
      if(summary){
        summary.querySelectorAll('.moveTableNotice').forEach(x=>x.remove());
        const note=document.createElement('div');
        note.className='moveTableNotice';
        note.innerHTML='<b>Spostamento tavolo</b><div>Attuale: '+esc(current)+'. Scegli il nuovo tavolo e premi Salva prenotazione. Il tavolo precedente verrà liberato automaticamente e la prenotazione resterà una sola.</div>';
        summary.prepend(note);
      }
      const picker=document.getElementById('picker');
      if(picker)picker.scrollIntoView({behavior:'smooth',block:'center'});
    }catch(e){console.warn('Spostamento tavolo:',e)}
  },80);
}'''
if 'function moveBookingTable(id)' not in s:
    if marker not in s:
        raise SystemExit('renderMap non trovato')
    s=s.replace(marker,fn+'\n'+marker,1)

# Nuova prenotazione / modifica normale: escono sempre dalla modalità spostamento.
s=s.replace('function openBooking(){','function openBooking(){movingOnly=null;if($(\'room\'))$(\'room\').disabled=false;',1)
s=s.replace('function editBooking(id){','function editBooking(id){movingOnly=null;if($(\'room\'))$(\'room\').disabled=false;',1)
s=s.replace("function closeBooking(){$('modal').classList.remove('open')}","function closeBooking(){movingOnly=null;if($('room'))$('room').disabled=false;$('modal').classList.remove('open')}",1)

# In modalità spostamento usa un RPC dedicato: conserva tutti i dati della prenotazione
# e cambia soltanto l'associazione ai tavoli. Il backend riusa tutte le verifiche di
# capienza, sovrapposizione, rimpiazzo e forzatura del salvataggio normale.
save_marker='async function saveBooking(force){'
move_save=r'''async function saveBooking(force){
  $('saveMsg').style.display='none';
  if(movingOnly&&editing===movingOnly){
    if(!selected.length)return alert('Seleziona il nuovo tavolo.');
    let q=await db.rpc('move_reservation_tables',{p_reservation_id:editing,p_table_codes:selected,p_forced:force});
    if(q.error){
      let t=q.error.message||'';
      if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura')||t.toLowerCase().includes('non sono consecutivi')||t.toLowerCase().includes('associarli comunque'))){
        let ask=(t.toLowerCase().includes('non sono consecutivi')||t.toLowerCase().includes('associarli comunque'))?'I tavoli selezionati non sono consecutivi. Vuoi associarli comunque?':t+'\n\nVuoi comunque forzare questo spostamento?';
        if(confirm(ask))return saveBooking(true);
      }
      $('saveMsg').style.display='block';$('saveMsg').textContent=t;return;
    }
    movingOnly=null;closeBooking();await loadAll();showPage('map',document.querySelector('[data-p="map"]'));return;
  }
'''
if save_marker not in s:
    raise SystemExit('saveBooking non trovata')
s=s.replace(save_marker,move_save,1)

# Espone la funzione dal modulo ES senza dipendere dall'ordine esatto degli handler.
m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m:
    raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
if 'moveBookingTable' not in items:
    repl='Object.assign(window,{'+items.rstrip()+',moveBookingTable});'
    s=s[:m.start()]+repl+s[m.end():]

css='''<style id="marino-manual-table-move">
.moveTableNotice{margin:0 0 10px;padding:10px 12px;border:2px solid #d8a52f;border-radius:12px;background:#fff8e8;color:#102c45;font-size:13px;line-height:1.35}
.moveTableNotice b{display:block;color:#063f78;margin-bottom:3px}
.moveTableBtn{font-weight:900}
@media(max-width:720px){[data-move-booking]{min-height:42px}.moveTableNotice{font-size:12px}}
</style>'''
if 'id="marino-manual-table-move"' not in s:
    if '</head>' not in s: raise SystemExit('head non trovato')
    s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
