from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Mostra chiaramente sui singoli tavoli Quadrato la capienza standard e la forzatura a 4.
# Patch volutamente minima: modifica soltanto il testo della capienza nel picker,
# così resta compatibile con gli altri aggiornamenti del layout.
old="<div class=\"coverRange\">'+mn+'–'+mx+' coperti</div>"
new="<div class=\"coverRange\">'+((t.group_name==='quadrati'&&Number(t.single_max_covers||0)===3)?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti'))+'</div>"
if old not in s:
    raise SystemExit('Testo capienza renderPicker non trovato')
s=s.replace(old,new,1)

# Conferma immediata e specifica per 4 coperti su un singolo Quadrato.
if 'Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?' not in s:
    s,n=re.subn(
        r"async\s+function\s+saveBooking\s*\(\s*force\s*\)\s*\{",
        "async function saveBooking(force){if(!force&&selected.length===1&&selected[0].startsWith('PQ')&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?'))return saveBooking(true);return;}",
        s,count=1
    )
    if n!=1:
        raise SystemExit('saveBooking non trovato')

# Riepilogo ancora più esplicito quando viene selezionato un Quadrato con 4 coperti.
s=s.replace("⚠ 4 persone su un solo Quadrato richiedono conferma di forzatura.","⚠ 4 coperti su un solo Quadrato: forzatura consentita con conferma.",1)

# Sincronizzazione forte tra data/servizio e orari prenotazione.
# Impedisce che un orario pranzo resti selezionato passando a un servizio cena (e viceversa).
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

m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m: raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
for name in ['refreshBookingTimesForService','arrivalMatchesService']:
    if name not in items: items=items.rstrip()+','+name
s=s[:m.start()]+'Object.assign(window,{'+items+'});'+s[m.end():]

css='''<style id="marino-square-force-4">\n#picker .coverRange{line-height:1.2}\n@media(max-width:720px){#picker .coverRange{font-size:11px}}\n</style><style id="marino-service-time-sync">\n#arrival,#endTime{font-variant-numeric:tabular-nums}\n</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
