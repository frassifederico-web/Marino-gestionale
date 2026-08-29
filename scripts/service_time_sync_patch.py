from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

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
if helper not in s:
    if marker not in s: raise SystemExit('serviceOptions non trovata')
    s=s.replace(marker,helper+'\n'+marker,1)

# Cambio data: riallinea sempre la tendina Arrivo al servizio appena selezionato.
s,n=re.subn(r"function dayChanged\(\)\{serviceOptions\(\);loadAll\(\)\}","function dayChanged(){serviceOptions();refreshBookingTimesForService(true);loadAll()}",s,count=1)
if n!=1: raise SystemExit('dayChanged non trovata')

# Cambio manuale servizio (sabato pranzo/cena): stesso riallineamento.
s=s.replace('id="service" onchange="loadAll()"','id="service" onchange="refreshBookingTimesForService(true);loadAll()"',1)
if 'onchange="refreshBookingTimesForService(true);loadAll()"' not in s:
    raise SystemExit('select servizio non aggiornato')

# Boot: dopo aver popolato le opzioni generiche, limita subito al servizio corrente.
s=s.replace("$('endTime').innerHTML='<option value=\"\">Non indicata</option>'+t.map(x=>'<option>'+x+'</option>').join('');await loadAll()}","$('endTime').innerHTML='<option value=\"\">Non indicata</option>'+t.map(x=>'<option>'+x+'</option>').join('');refreshBookingTimesForService(true);await loadAll()}",1)
if 'refreshBookingTimesForService(true);await loadAll()' not in s:
    raise SystemExit('boot non aggiornato')

# Nuova prenotazione: ricostruisce la tendina corretta prima di impostare il default.
old="$('notes').value='';$('arrival').value=$('service').value.includes('pranzo')?'12:30':'19:30';$('endTime').value='';$('modal').classList.add('open');renderPicker()"
new="$('notes').value='';refreshBookingTimesForService(true);$('arrival').value=$('service').value.includes('pranzo')?'12:30':'19:30';$('endTime').value='';$('modal').classList.add('open');renderPicker()"
if old not in s: raise SystemExit('openBooking non trovata')
s=s.replace(old,new,1)

# Modifica: garantisce che le opzioni del select appartengano al servizio prima di rimettere l'orario salvato.
old="$('notes').value=r.notes||'';$('arrival').value=String(r.arrival_time).slice(0,5);"
new="$('notes').value=r.notes||'';refreshBookingTimesForService(false);$('arrival').value=String(r.arrival_time).slice(0,5);"
if old not in s: raise SystemExit('editBooking non trovata')
s=s.replace(old,new,1)

# Ultima difesa prima del salvataggio: impossibile inviare al backend un orario pranzo su cena o viceversa.
needle="$('saveMsg').style.display='none';if(!$('guest').value.trim()||Number($('party').value)<1||!selected.length)return alert('Completa nome, coperti e tavoli.');"
repl="$('saveMsg').style.display='none';if(!arrivalMatchesService()){refreshBookingTimesForService(true);return alert('L’orario è stato riallineato al servizio selezionato. Controllalo e salva di nuovo.')}if(!$('guest').value.trim()||Number($('party').value)<1||!selected.length)return alert('Completa nome, coperti e tavoli.');"
if needle not in s: raise SystemExit('guardia saveBooking non trovata')
s=s.replace(needle,repl,1)

# Espone le funzioni perché il select HTML le usa tramite onchange.
m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m: raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
for name in ['refreshBookingTimesForService','arrivalMatchesService']:
    if name not in items: items=items.rstrip()+','+name
s=s[:m.start()]+'Object.assign(window,{'+items+'});'+s[m.end():]

css='''<style id="marino-service-time-sync">\n#arrival,#endTime{font-variant-numeric:tabular-nums}\n</style>'''
if 'id="marino-service-time-sync"' not in s:
    s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
