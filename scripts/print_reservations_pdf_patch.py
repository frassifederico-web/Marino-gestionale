from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

patch=r'''
function marinoPrintEsc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function ensureReservationsPrintButton(){
  const host=$('bookingList');if(!host||document.getElementById('downloadReservationsPdfBtn'))return;
  const bar=document.createElement('div');bar.className='reservationsPrintBar';
  bar.innerHTML='<button id="downloadReservationsPdfBtn" type="button" class="primary reservationsPrintBtn">⬇ Scarica lista prenotazioni</button><span>A4 verticale · tavolo da assegnare a mano · 5 righe libere finali</span>';
  host.parentNode.insertBefore(bar,host);
  bar.querySelector('button').addEventListener('click',printTodayReservationsSheet);
}
async function printTodayReservationsSheet(){
  const popup=window.open('','_blank');
  if(!popup){alert('Il browser ha bloccato la finestra di stampa. Consenti i popup e riprova.');return}
  popup.document.write('<!doctype html><html><head><meta charset="utf-8"><title>MARINO - Lista prenotazioni</title></head><body style="font-family:Arial,sans-serif;padding:24px">Preparazione lista prenotazioni…</body></html>');
  popup.document.close();
  const date=marinoToday();
  let rq=await db.from('reservations').select('*').eq('service_date',date).eq('status','confermata').order('arrival_time');
  if(rq.error){popup.close();alert(rq.error.message);return}
  let rows=(rq.data||[]);
  let dinner=rows.filter(r=>String(r.service_code||'').includes('cena'));
  if(dinner.length)rows=dinner;
  const covers=rows.reduce((a,r)=>a+Number(r.party_size||0),0);
  const label=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long',day:'2-digit',month:'long',year:'numeric'}).format(new Date(date+'T12:00:00'));
  const n=rows.length;
  const fs=n>28?7.4:n>22?8.1:n>16?8.8:9.6;
  const pad=n>28?3:n>20?4:5;
  const body=rows.map(r=>{
    const note=String(r.notes||'').trim();
    return '<tr><td class="tavolo"></td><td class="ora">'+marinoPrintEsc(hhmm(r.arrival_time))+'</td><td class="nome"><b>'+marinoPrintEsc(r.guest_name||'')+'</b></td><td class="cop">'+Number(r.party_size||0)+'</td><td class="note">'+(note?marinoPrintEsc(note):'')+'</td></tr>';
  }).join('');
  const emptyRows=Array.from({length:5}).map(()=>'<tr class="manualRow"><td class="tavolo"></td><td class="ora"></td><td class="nome"></td><td class="cop"></td><td class="note"></td></tr>').join('');
  const logo='<div class="logoWrap"><img src="icon.svg" alt="MARINO"><div><div class="brand">MARINO</div><div class="subtitle">TRATTORIA DI PESCE</div></div></div>';
  const html='<!doctype html><html><head><meta charset="utf-8"><title>MARINO - Lista prenotazioni '+date+'</title><style>'+
    '@page{size:A4 portrait;margin:8mm}*{box-sizing:border-box}html,body{width:100%;min-height:100%;margin:0}body{font-family:Arial,Helvetica,sans-serif;color:#102c45;background:#fff}.sheet{min-height:279mm;display:flex;flex-direction:column}.head{display:flex;justify-content:space-between;align-items:center;border:2px solid #063f78;border-radius:10px;padding:7px 10px;background:#fff9e7;margin-bottom:7px}.logoWrap{display:flex;align-items:center;gap:9px}.logoWrap img{width:42px;height:42px;display:block}.brand{font-size:20px;font-weight:900;letter-spacing:.08em;color:#063f78;line-height:1}.subtitle{font-size:7.5pt;font-weight:800;letter-spacing:.12em;color:#c65300;margin-top:3px}.dateBlock{text-align:right}.date{font-size:10.5pt;font-weight:900;text-transform:capitalize;color:#063f78}.tot{font-size:8pt;margin-top:3px;color:#526574;font-weight:700}.rule{height:4px;background:#c65300;border-radius:99px;margin:0 0 7px}table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:'+fs+'pt;border:1.5px solid #063f78;border-radius:9px;overflow:hidden}th,td{border-right:1px solid #9fb2c2;border-bottom:1px solid #b8c5cf;padding:'+pad+'px 5px;vertical-align:middle;line-height:1.16}th:last-child,td:last-child{border-right:0}tbody tr:last-child td{border-bottom:0}th{background:#063f78;color:#fff;font-size:'+(fs-.2)+'pt;text-transform:uppercase;letter-spacing:.025em;font-weight:900}.tavolo{width:18%;text-align:center;font-weight:900}.ora{width:11%;text-align:center;font-weight:900}.nome{width:29%}.cop{width:9%;text-align:center;font-weight:900}.note{width:33%;font-weight:650}.manualRow td{height:'+(n>24?'20':'25')+'px;background:#fffdf6}.manualRow .nome:after{content:""}.footerSpace{flex:1;min-height:5mm}.foot{margin-top:7px;padding:6px 8px;border-top:2px solid #063f78;font-size:7.5pt;color:#526574;display:flex;justify-content:space-between;gap:10px}.hint{font-weight:800;color:#063f78}.noRows{padding:30px;text-align:center;border:2px solid #063f78;border-radius:9px;background:#fff9e7}'+
    '</style></head><body><div class="sheet"><div class="head">'+logo+'<div class="dateBlock"><div class="date">Lista prenotazioni · '+marinoPrintEsc(label)+'</div><div class="tot">'+rows.length+' prenotazioni · '+covers+' coperti totali</div></div></div><div class="rule"></div>'+
    (rows.length?'<table><thead><tr><th class="tavolo">Tavolo assegnato</th><th class="ora">Ora</th><th class="nome">Prenotazione</th><th class="cop">Cop.</th><th class="note">Note</th></tr></thead><tbody>'+body+emptyRows+'</tbody></table>':'<div class="noRows">Nessuna prenotazione per il servizio.</div>')+
    '<div class="footerSpace"></div><div class="foot"><span class="hint">Le ultime 5 righe sono libere per osservazioni o prenotazioni prese sul momento.</span><span>MARINO · uso interno sala</span></div></div><script>window.onload=()=>setTimeout(()=>window.print(),220)<\/script></body></html>';
  popup.document.open();popup.document.write(html);popup.document.close();
}
const _renderBookingsPrintBase=renderBookings;
renderBookings=async function(){const out=await _renderBookingsPrintBase();ensureReservationsPrintButton();return out};
'''

marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('_renderMapBase non trovata per stampa prenotazioni')
s=s.replace(marker,patch+'\n'+marker,1)

m=re.search(r'Object\.assign\(window,\{([^}]*)\}\);',s)
if not m:
    raise SystemExit('Object.assign(window,...) non trovato')
items=m.group(1)
for name in ['printTodayReservationsSheet','ensureReservationsPrintButton']:
    if name not in items: items=items.rstrip()+','+name
s=s[:m.start()]+'Object.assign(window,{'+items+'});'+s[m.end():]

css=r'''<style id="marino-reservations-print">
.reservationsPrintBar{display:flex;align-items:center;gap:10px;margin:0 0 10px;padding:9px 10px;border:1px solid #d7e1ea;border-radius:12px;background:#f4f8fb}.reservationsPrintBar span{font-size:11px;color:#526574;font-weight:700}.reservationsPrintBtn{min-height:40px;font-weight:900;white-space:nowrap}
@media(max-width:720px){.reservationsPrintBar{align-items:stretch;flex-direction:column;gap:5px}.reservationsPrintBtn{width:100%}.reservationsPrintBar span{font-size:10px;text-align:center}}
</style>'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)

if 'Tavolo assegnato' not in s or 'Array.from({length:5})' not in s or '@page{size:A4 portrait' not in s or 'TRATTORIA DI PESCE' not in s:
    raise SystemExit('Lista prenotazioni A4 Marino non aggiornata correttamente')

p.write_text(s)
