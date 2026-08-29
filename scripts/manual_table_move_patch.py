from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Aggiunge un comando esplicito di spostamento accanto a Modifica.
old="<button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button><button class=\"danger\" data-delete-booking=\"'+esc(r.id)+'\">Elimina</button>"
new="<button class=\"secondary\" data-move-booking=\"'+esc(r.id)+'\">Sposta tavolo</button><button class=\"secondary\" data-edit-booking=\"'+esc(r.id)+'\">Modifica</button><button class=\"danger\" data-delete-booking=\"'+esc(r.id)+'\">Elimina</button>"
if old not in s:
    raise SystemExit('Pulsanti prenotazione non trovati')
s=s.replace(old,new,1)

old_listener="$('bookingList').querySelectorAll('[data-edit-booking]').forEach(b=>b.addEventListener('click',()=>editBooking(b.dataset.editBooking)));"
new_listener="$('bookingList').querySelectorAll('[data-move-booking]').forEach(b=>b.addEventListener('click',()=>moveBookingTable(b.dataset.moveBooking)));"+old_listener
if old_listener not in s:
    raise SystemExit('Listener modifica prenotazione non trovato')
s=s.replace(old_listener,new_listener,1)

marker="function renderMap()"
fn=r'''function moveBookingTable(id){
  const r=reservations.find(x=>x.id===id);
  if(!r){alert('Prenotazione non trovata.');return}
  editBooking(id);
  setTimeout(()=>{
    try{
      const current=tableLabelsForRes(id)||'tavolo attuale';
      const summary=document.getElementById('tableSelectionSummary');
      if(summary){
        const note=document.createElement('div');
        note.className='moveTableNotice';
        note.innerHTML='<b>Spostamento tavolo</b><div>Attuale: '+esc(current)+'. Tocca il nuovo tavolo e poi premi Salva. Cambia solo questa prenotazione: il layout generale resta invariato.</div>';
        summary.prepend(note);
      }
      const picker=document.getElementById('picker');
      if(picker)picker.scrollIntoView({behavior:'smooth',block:'center'});
    }catch(e){console.warn('Spostamento tavolo:',e)}
  },60);
}'''
if marker not in s:
    raise SystemExit('renderMap non trovato')
s=s.replace(marker,fn+'\n'+marker,1)

# Espone la funzione dal modulo ES.
old_expose='Object.assign(window,{login,signup,logout,showPage,dayChanged,loadAll,saveServiceSettings,openBooking,closeBooking,setMapRoom,editBooking,toggleTable,saveBooking,delBooking,addMenu,toggleMenu,deleteMenu,inviteAdmin'
if old_expose not in s:
    raise SystemExit('Object.assign non trovato')
s=s.replace(old_expose,old_expose+',moveBookingTable',1)

css='''<style id="marino-manual-table-move">
.moveTableNotice{margin:0 0 10px;padding:10px 12px;border:2px solid #d8a52f;border-radius:12px;background:#fff8e8;color:#102c45;font-size:13px;line-height:1.35}
.moveTableNotice b{display:block;color:#063f78;margin-bottom:3px}
@media(max-width:720px){[data-move-booking]{min-height:42px}.moveTableNotice{font-size:12px}}
</style>'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
