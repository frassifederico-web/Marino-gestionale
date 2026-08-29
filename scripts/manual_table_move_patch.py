from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Aggiunge il comando esplicito di spostamento alla riga azioni della prenotazione.
# La build attuale costruisce i pulsanti tramite la variabile `actions`, quindi
# interveniamo lì senza toccare il layout generale della sala.
edit_action="actions+='<button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button>';"
move_action="actions+='<button class=\"secondary moveTableBtn\" data-move-booking=\"'+esc(r.id)+'\">Sposta tavolo</button>';\n      "+edit_action
if edit_action in s:
    s=s.replace(edit_action,move_action,1)
else:
    # Fallback per eventuali versioni future in cui Modifica/Elimina tornano contigui.
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

# Modalità dedicata: apre la prenotazione esistente con i tavoli attuali selezionati.
# L'utente tocca il nuovo tavolo e salva: viene aggiornata solo l'associazione
# reservation_tables della prenotazione, non la configurazione restaurant_tables.
marker="function renderMap(){"
fn=r'''function moveBookingTable(id){
  const r=reservations.find(x=>x.id===id);
  if(!r){alert('Prenotazione non trovata.');return}
  editBooking(id);
  setTimeout(()=>{
    try{
      const current=tableLabelsForRes(id)||'tavolo attuale';
      const summary=document.getElementById('tableSelectionSummary');
      if(summary){
        summary.querySelectorAll('.moveTableNotice').forEach(x=>x.remove());
        const note=document.createElement('div');
        note.className='moveTableNotice';
        note.innerHTML='<b>Spostamento tavolo</b><div>Attuale: '+esc(current)+'. Deseleziona il tavolo attuale, scegli il nuovo tavolo e premi Salva prenotazione. Cambia solo questa prenotazione: il layout generale resta invariato.</div>';
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
