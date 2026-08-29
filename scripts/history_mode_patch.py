from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Riepilogo storico nella pagina Giorno.
if 'id="historySummary"' not in s:
    marker='<div class="grid4">'
    if marker not in s:
        raise SystemExit('Griglia statistiche Giorno non trovata')
    s=s.replace(marker,'<div id="historySummary" class="historySummary" style="display:none"></div>'+marker,1)

helpers=r'''function marinoToday(){
  const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Rome',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const m=Object.fromEntries(parts.map(x=>[x.type,x.value]));
  return m.year+'-'+m.month+'-'+m.day;
}
function isPastServiceDate(){return Boolean($('date')?.value&&$('date').value<marinoToday())}
function renderHistoryMode(){
  const past=isPastServiceDate(),box=$('historySummary');
  document.querySelectorAll('button[onclick="openBooking()"]').forEach(b=>{b.disabled=past;b.title=past?'Archivio storico: non è possibile creare prenotazioni retroattive':''});
  if(!box)return;
  if(!past){box.style.display='none';box.innerHTML='';return}
  const used=[...new Set(links.filter(x=>x.restaurant_tables?.code).map(x=>x.restaurant_tables.code))];
  const inside=[...new Set(links.filter(x=>x.restaurant_tables?.code&&allTables.find(t=>t.code===x.restaurant_tables.code)?.area==='interno').map(x=>x.restaurant_tables.code))];
  const outside=[...new Set(links.filter(x=>x.restaurant_tables?.code&&allTables.find(t=>t.code===x.restaurant_tables.code)?.area==='dehors').map(x=>x.restaurant_tables.code))];
  const covers=reservations.reduce((a,r)=>a+Number(r.party_size||0),0);
  box.style.display='block';
  box.innerHTML='<b>ARCHIVIO STORICO · sola consultazione</b><div>'+reservations.length+' prenotazioni · '+covers+' coperti · '+used.length+' tavoli utilizzati</div><div class="muted">Interno: '+inside.length+' tavoli · Dehors: '+outside.length+' tavoli. Apri la sezione Tavoli per vedere dove erano seduti.</div>';
}
'''
marker='function serviceOptions()'
if marker not in s:
    raise SystemExit('serviceOptions non trovata')
s=s.replace(marker,helpers+'\n'+marker,1)

# All'apertura dell'app seleziona sempre la data odierna in Italia.
s,n=re.subn(r"function boot\(\)\{if\(!\$\('date'\)\.value\)\$\('date'\)\.value=new Date\(\)\.toISOString\(\)\.slice\(0,10\);", "function boot(){$('date').value=marinoToday();", s, count=1)
if n!=1:
    raise SystemExit('Inizializzazione data in boot non trovata')

# Blocca il form Nuova prenotazione sulle date passate, lasciando libera la consultazione.
s,n=re.subn(r"function openBooking\(\)\{editing=null;", "function openBooking(){if(isPastServiceDate()){alert('Questa data è in archivio storico. Puoi consultare prenotazioni e tavoli, ma non creare nuove prenotazioni retroattive.');return}editing=null;", s, count=1)
if n!=1:
    raise SystemExit('openBooking non trovata')

# Aggiorna il riepilogo storico dopo ogni caricamento della giornata.
s=s.replace('renderUsers(u.data||[]);applySettings(s.data)}','renderUsers(u.data||[]);applySettings(s.data);renderHistoryMode()}',1)
if 'renderHistoryMode()}' not in s:
    raise SystemExit('renderHistoryMode non collegata a loadAll')

# Nello storico mostra in mappa anche le prenotazioni completate; annullate sono già escluse da loadAll.
s=s.replace(".filter(r=>r&&r.status==='confermata')", ".filter(r=>r&&(r.status==='confermata'||isPastServiceDate()))")
s=s.replace("links.filter(x=>reservations.find(r=>r.id===x.reservation_id)?.status==='confermata').forEach", "links.filter(x=>{let r=reservations.find(r=>r.id===x.reservation_id);return r&&(r.status==='confermata'||isPastServiceDate())}).forEach")

# Se si tenta comunque di salvare una nuova prenotazione su data passata, blocco anche lato UI.
s,n=re.subn(r"async function saveBooking\(force\)\{\$\('saveMsg'\)\.style\.display='none';", "async function saveBooking(force){$('saveMsg').style.display='none';if(!editing&&isPastServiceDate()){alert('Non è possibile creare prenotazioni per una data precedente a oggi.');return}", s, count=1)
if n!=1:
    raise SystemExit('saveBooking non trovata')

css=r'''<style id="marino-history-mode">
.historySummary{margin:0 0 12px;padding:12px 14px;border:2px solid #063f78;border-radius:14px;background:#eef5fb;color:#102c45;line-height:1.4}
.historySummary>b{display:block;color:#063f78;margin-bottom:4px}
button[disabled]{opacity:.48;cursor:not-allowed!important}
@media(max-width:720px){.historySummary{font-size:13px;padding:10px 12px}}
</style>'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
