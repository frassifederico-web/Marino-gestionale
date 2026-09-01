from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

old="<div class=\"coverRange\">'+mn+'–'+mx+' coperti</div>"
new="<div class=\"coverRange\">'+((t.group_name==='quadrati'&&Number(t.single_max_covers||0)===3)?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti'))+'</div>"
if old not in s:
    raise SystemExit('Testo capienza renderPicker non trovato')
s=s.replace(old,new,1)

if 'Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?' not in s:
    s,n=re.subn(
        r"async\s+function\s+saveBooking\s*\(\s*force\s*\)\s*\{",
        "async function saveBooking(force){if(!force&&selected.length===1&&selected[0].startsWith('PQ')&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?'))return saveBooking(true);return;}",
        s,count=1
    )
    if n!=1:
        raise SystemExit('saveBooking non trovato')

s=s.replace("⚠ 4 persone su un solo Quadrato richiedono conferma di forzatura.","⚠ 4 coperti su un solo Quadrato: forzatura consentita con conferma.",1)

helper=r'''function refreshBookingTimesForService(resetArrival=false){
  const code=$('service')?.value||'';
  const dinner=code.includes('cena'), lunch=code.includes('pranzo');
  if(!dinner&&!lunch)return;
  const all=qTimes();
  const valid=all.filter(x=>{const h=Number(x.slice(0,2));return dinner?(h>=19&&h<=23):(h>=12&&h<=15)});
  const arrival=$('arrival'), end=$('endTime');
  if(!arrival)return;
  const oldArrival=arrival.value;
  const oldEnd=end?.value||'';
  arrival.innerHTML=valid.map(x=>'<option value="'+x+'">'+x+'</option>').join('');
  const fallback=dinner?'19:30':'12:30';
  arrival.value=(!resetArrival&&valid.includes(oldArrival))?oldArrival:(valid.includes(fallback)?fallback:valid[0]);
  if(end){
    end.innerHTML='<option value="">Non indicata</option>'+valid.map(x=>'<option value="'+x+'">'+x+'</option>').join('');
    if(!resetArrival&&valid.includes(oldEnd)&&oldEnd>arrival.value)end.value=oldEnd;else end.value='';
  }
}
function arrivalMatchesService(){
  const code=$('service')?.value||'',v=$('arrival')?.value||'';
  const h=Number(v.slice(0,2));
  return code.includes('cena')?(h>=19&&h<=23):code.includes('pranzo')?(h>=12&&h<=15):false;
}
'''
marker='function serviceOptions()'
if 'function refreshBookingTimesForService' not in s:
    if marker not in s: raise SystemExit('serviceOptions non trovata')
    s=s.replace(marker,helper+'\n'+marker,1)

s,n=re.subn(r"function dayChanged\(\)\{serviceOptions\(\);loadAll\(\)\}","function dayChanged(){serviceOptions();refreshBookingTimesForService(true);loadAll()}",s,count=1)
if n!=1: raise SystemExit('dayChanged non trovata')

s=s.replace('id="service" onchange="loadAll()"','id="service" onchange="refreshBookingTimesForService(true);loadAll()"',1)
if 'onchange="refreshBookingTimesForService(true);loadAll()"' not in s:
    raise SystemExit('select servizio non aggiornato')

boot_old="$('endTime').innerHTML='<option value=\"\">Non indicata</option>'+t.map(x=>'<option>'+x+'</option>').join('');await loadAll()}"
boot_new="$('endTime').innerHTML='<option value=\"\">Non indicata</option>'+t.map(x=>'<option>'+x+'</option>').join('');refreshBookingTimesForService(true);await loadAll()}"
if boot_old not in s: raise SystemExit('boot orari non trovato')
s=s.replace(boot_old,boot_new,1)

open_old="$('notes').value='';$('arrival').value=$('service').value.includes('pranzo')?'12:30':'19:30';$('endTime').value='';$('modal').classList.add('open');renderPicker()"
open_new="$('notes').value='';refreshBookingTimesForService(true);$('arrival').value=$('service').value.includes('pranzo')?'12:30':'19:30';$('endTime').value='';$('modal').classList.add('open');renderPicker()"
if open_old not in s: raise SystemExit('openBooking orari non trovato')
s=s.replace(open_old,open_new,1)

edit_old="$('notes').value=r.notes||'';$('arrival').value=String(r.arrival_time).slice(0,5);"
edit_new="$('notes').value=r.notes||'';refreshBookingTimesForService(false);$('arrival').value=String(r.arrival_time).slice(0,5);"
if edit_old not in s: raise SystemExit('editBooking orari non trovato')
s=s.replace(edit_old,edit_new,1)

save_needle="$('saveMsg').style.display='none';if(!$('guest').value.trim()||Number($('party').value)<1||!selected.length)return alert('Completa nome, coperti e tavoli.');"
save_repl="$('saveMsg').style.display='none';if(!arrivalMatchesService()){refreshBookingTimesForService(true);return alert('L’orario è stato riallineato al servizio selezionato. Controllalo e salva di nuovo.')}if(!$('guest').value.trim()||Number($('party').value)<1||!selected.length)return alert('Completa nome, coperti e tavoli.');"
if save_needle not in s: raise SystemExit('guardia saveBooking non trovata')
s=s.replace(save_needle,save_repl,1)

manage=r'''function serviceCodeForMovedDate(date,currentCode){
  const wd=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long'}).format(new Date(date+'T12:00:00')).toLowerCase();
  if(wd==='domenica')return 'domenica-pranzo';
  if(wd==='sabato')return String(currentCode||'').includes('pranzo')?'sabato-pranzo':'sabato-cena';
  const map={lunedi:'lunedi-cena','lunedì':'lunedi-cena',martedi:'martedi-cena','martedì':'martedi-cena',mercoledi:'mercoledi-cena','mercoledì':'mercoledi-cena',giovedi:'giovedi-cena','giovedì':'giovedi-cena',venerdi:'venerdi-cena','venerdì':'venerdi-cena'};
  return map[wd]||null;
}
async function reservationForManagement(id){
  let r=reservations.find(x=>x.id===id);if(r)return r;
  let q=await db.from('reservations').select('*').eq('id',id).single();
  if(q.error)throw q.error;
  return q.data;
}
async function tableCodesForManagement(id){
  let local=tableCodesForRes(id);if(local.length)return local;
  let q=await db.from('reservation_tables').select('restaurant_tables(code)').eq('reservation_id',id);
  if(q.error)throw q.error;
  return (q.data||[]).map(x=>x.restaurant_tables?.code).filter(Boolean);
}
async function changeBookingDate(id,force=false,newDate=null){
  let r;try{r=await reservationForManagement(id)}catch(e){return alert(e.message||'Prenotazione non trovata.');}
  const target=newDate||prompt('Inserisci la nuova data della prenotazione (AAAA-MM-GG):',r.service_date);
  if(!target)return;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(target))return alert('Data non valida. Usa il formato AAAA-MM-GG.');
  if(target<marinoToday())return alert('Non puoi spostare una prenotazione in una data già passata.');
  if(target===r.service_date)return alert('La prenotazione è già in questa data.');
  const code=serviceCodeForMovedDate(target,r.service_code);
  if(!code)return alert('Servizio non disponibile per la data scelta.');
  const dinner=code.includes('cena');
  let arrival=hhmm(r.arrival_time),h=Number(arrival.slice(0,2));
  if((dinner&&(h<19||h>23))||(!dinner&&(h<12||h>15)))arrival=dinner?'19:30':'12:30';
  let end=r.expected_end_time?hhmm(r.expected_end_time):null;
  if(end){let eh=Number(end.slice(0,2));if((dinner&&(eh<19||eh>23))||(!dinner&&(eh<12||eh>15))||end<=arrival)end=null;}
  let tableCodes;try{tableCodes=await tableCodesForManagement(id)}catch(e){return alert(e.message||'Errore tavoli prenotazione.');}
  const label=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(target+'T12:00:00'));
  if(!force&&!confirm('Spostare la prenotazione di '+r.guest_name+' al '+label+'?\n\nIl tavolo attuale verrà mantenuto se disponibile.'))return;
  const p={p_reservation_id:id,p_service_date:target,p_service_code:code,p_guest_name:r.guest_name,p_party_size:Number(r.party_size),p_arrival_time:arrival,p_expected_end_time:end,p_source:r.source,p_area:r.area,p_status:'confermata',p_notes:r.notes||null,p_forced:force||Boolean(r.forced),p_table_codes:tableCodes};
  const q=await db.rpc('save_reservation_with_tables',p);
  if(q.error){
    const t=q.error.message||'';
    if(!force&&(t.toLowerCase().includes('forzatura')||t.toLowerCase().includes('capienza')||t.toLowerCase().includes('consecutivi'))){
      if(confirm(t+'\n\nVuoi comunque forzare lo spostamento?'))return changeBookingDate(id,true,target);
    }
    return alert(t);
  }
  alert('Prenotazione spostata correttamente al '+label+'.');
  await loadAll();
}
async function cancelBookingFromList(id){
  if(!confirm('Cancellare definitivamente questa prenotazione? Il tavolo verrà liberato.'))return;
  let q=await db.from('reservations').delete().eq('id',id);
  if(q.error)return alert(q.error.message);
  await loadAll();
}
async function openMoveTableFromList(id,date,service){
  if(date&&$('date').value!==date){$('date').value=date;serviceOptions();}
  if(service&&[...$('service').options].some(o=>o.value===service))$('service').value=service;
  if(date||service)await loadAll();
  moveBookingTable(id);
}
function decorateBookingManagementButtons(){
  const host=$('bookingList');if(!host)return;
  host.querySelectorAll('[data-delete-booking]').forEach(b=>{b.textContent='Cancella';b.onclick=null;});
  host.querySelectorAll('[data-edit-booking],[data-open-chrono]').forEach(anchor=>{
    const id=anchor.dataset.editBooking||anchor.dataset.openChrono;if(!id)return;
    const box=anchor.parentElement;if(!box)return;
    const date=anchor.dataset.date||null,service=anchor.dataset.service||null;
    if(!box.querySelector('[data-move-booking="'+id+'"]')){
      const m=document.createElement('button');m.className='secondary moveTableBtn';m.textContent='Modifica tavolo';m.dataset.moveBooking=id;
      m.addEventListener('click',()=>openMoveTableFromList(id,date,service));
      box.insertBefore(m,anchor);
    }
    if(!box.querySelector('[data-change-day-booking="'+id+'"]')){
      const c=document.createElement('button');c.className='secondary changeDayBtn';c.textContent='Cambia giorno';c.dataset.changeDayBooking=id;c.addEventListener('click',()=>changeBookingDate(id));
      box.insertBefore(c,anchor.nextSibling);
    }
    if(!box.querySelector('[data-delete-booking]')){const d=document.createElement('button');d.className='danger';d.textContent='Cancella';d.dataset.deleteBooking=id;d.addEventListener('click',()=>cancelBookingFromList(id));box.appendChild(d);}
  });
  host.querySelectorAll('[data-change-day-booking]').forEach(b=>{if(!b.dataset.boundChangeDay){b.dataset.boundChangeDay='1';b.addEventListener('click',()=>changeBookingDate(b.dataset.changeDayBooking));}});
}
'''
marker_del='async function delBooking(id){'
if marker_del not in s: raise SystemExit('delBooking non trovata')
s=s.replace(marker_del,manage+'\n'+marker_del,1)
s=s.replace("if(!confirm('Eliminare la prenotazione?'))return;","if(!confirm('Cancellare definitivamente questa prenotazione? Il tavolo verrà liberato.'))return;",1)

wrap=r'''const _renderBookingsManagementBase=renderBookings;
renderBookings=async function(){
  const out=await _renderBookingsManagementBase();
  decorateBookingManagementButtons();
  return out;
};
'''
marker_render='function _renderMapBase'
if marker_render not in s: raise SystemExit('_renderMapBase non trovata')
s=s.replace(marker_render,wrap+'\n'+marker_render,1)

m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m: raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
for name in ['refreshBookingTimesForService','arrivalMatchesService','changeBookingDate','cancelBookingFromList','openMoveTableFromList']:
    if name not in items: items=items.rstrip()+','+name
s=s[:m.start()]+'Object.assign(window,{'+items+'});'+s[m.end():]

css='''<style id="marino-square-force-4">\n#picker .coverRange{line-height:1.2}\n@media(max-width:720px){#picker .coverRange{font-size:11px}}\n</style><style id="marino-service-time-sync">\n#arrival,#endTime{font-variant-numeric:tabular-nums}\n.changeDayBtn{white-space:nowrap}\n@media(max-width:720px){.changeDayBtn,.moveTableBtn{min-height:38px}}\n</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
