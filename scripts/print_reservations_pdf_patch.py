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
  popup.document.write('<!doctype html><html><head><meta charset="utf-8"><title>MARINO - Lista prenotazioni</title></head><body>Preparazione lista prenotazioni…</body></html>');popup.document.close();
  const date=marinoToday();
  let rq=await db.from('reservations').select('*').eq('service_date',date).eq('status','confermata').order('arrival_time');
  if(rq.error){popup.close();alert(rq.error.message);return}
  let rows=(rq.data||[]);let dinner=rows.filter(r=>String(r.service_code||'').includes('cena'));if(dinner.length)rows=dinner;
  const covers=rows.reduce((a,r)=>a+Number(r.party_size||0),0);
  const label=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long',day:'2-digit',month:'long',year:'numeric'}).format(new Date(date+'T12:00:00'));
  const n=rows.length;
  const fs=n>28?12:n>23?13:n>18?14:n>13?15:16;
  const rowH=n>28?8.0:n>23?8.8:n>18?9.8:n>13?11.2:12.5;
  const body=rows.map(r=>{const note=String(r.notes||'').trim();return '<tr><td class="tavolo"></td><td class="ora">'+marinoPrintEsc(hhmm(r.arrival_time))+'</td><td class="nome"><b>'+marinoPrintEsc(r.guest_name||'')+'</b></td><td class="cop">'+Number(r.party_size||0)+'</td><td class="note">'+(note?marinoPrintEsc(note):'')+'</td></tr>'}).join('');
  const emptyRows=Array.from({length:5}).map(()=>'<tr class="manualRow"><td class="tavolo"></td><td class="ora"></td><td class="nome"></td><td class="cop"></td><td class="note"></td></tr>').join('');
  const logo='<div class="logoWrap"><img src="icon.svg" alt="MARINO"><div><div class="brand">MARINO</div><div class="subtitle">TRATTORIA DI PESCE</div></div></div>';
  const html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MARINO - Lista prenotazioni '+date+'</title><style>'+
  '@page{size:210mm 297mm;margin:7mm 8mm}*{box-sizing:border-box}html,body{margin:0!important;padding:0!important;width:194mm!important;max-width:194mm!important;background:#fff!important}body{font-family:Arial,Helvetica,sans-serif;color:#102c45}.sheet{width:194mm;min-height:283mm;display:flex;flex-direction:column;overflow:hidden}.head{height:29mm;display:flex;justify-content:space-between;align-items:center;border:2.2px solid #063f78;border-radius:3mm;padding:3mm 4mm;background:#fff7dc;margin-bottom:2.5mm}.logoWrap{display:flex;align-items:center;gap:3mm}.logoWrap img{width:19mm;height:19mm}.brand{font-size:30px;font-weight:900;letter-spacing:.07em;color:#063f78;line-height:.9}.subtitle{font-size:13px;font-weight:900;letter-spacing:.1em;color:#c65300;margin-top:2mm}.dateBlock{text-align:right;max-width:92mm}.date{font-size:18px;font-weight:900;text-transform:capitalize;color:#063f78;line-height:1.15}.tot{font-size:14px;margin-top:2mm;color:#526574;font-weight:800}.rule{height:2mm;background:#c65300;border-radius:9mm;margin-bottom:2.5mm}table{width:194mm!important;max-width:194mm!important;border-collapse:collapse;table-layout:fixed;font-size:'+fs+'px;border:2px solid #063f78}th,td{border:1px solid #9fb2c2;padding:1.5mm 1.3mm;vertical-align:middle;line-height:1.12;height:'+rowH+'mm;overflow-wrap:anywhere}th{height:10mm;background:#063f78!important;color:#fff!important;-webkit-print-color-adjust:exact;print-color-adjust:exact;font-size:'+(fs-1)+'px;text-transform:uppercase;font-weight:900}.tavolo{width:18%;text-align:center;font-weight:900}.ora{width:12%;text-align:center;font-weight:900}.nome{width:27%}.cop{width:10%;text-align:center;font-weight:900}.note{width:33%;font-weight:700}.manualRow td{height:12mm;background:#fffdf6!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}.footerSpace{flex:1}.foot{margin-top:2mm;padding-top:2mm;border-top:2px solid #063f78;font-size:11px;color:#526574;display:flex;justify-content:space-between;gap:4mm}.hint{font-weight:800;color:#063f78}.noRows{font-size:20px;padding:15mm;text-align:center;border:2px solid #063f78}@media print{html,body{width:194mm!important;height:auto!important}.sheet{width:194mm!important;transform:none!important}table{width:194mm!important}thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}}'+
  '</style></head><body><div class="sheet"><div class="head">'+logo+'<div class="dateBlock"><div class="date">Lista prenotazioni<br>'+marinoPrintEsc(label)+'</div><div class="tot">'+rows.length+' prenotazioni · '+covers+' coperti totali</div></div></div><div class="rule"></div>'+(rows.length?'<table><thead><tr><th class="tavolo">Tavolo<br>assegnato</th><th class="ora">Ora</th><th class="nome">Prenotazione</th><th class="cop">Cop.</th><th class="note">Note</th></tr></thead><tbody>'+body+emptyRows+'</tbody></table>':'<div class="noRows">Nessuna prenotazione per il servizio.</div>')+'<div class="footerSpace"></div><div class="foot"><span class="hint">5 righe libere per prenotazioni o osservazioni dell’ultimo momento.</span><span>MARINO · uso interno sala</span></div></div><script>window.onload=()=>setTimeout(()=>window.print(),250)<\/script></body></html>';
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
    if name not in items:
        items=items.rstrip()+','+name
s=s[:m.start()]+'Object.assign(window,{'+items+'});'+s[m.end():]

css=r'''<style id="marino-reservations-print">.reservationsPrintBar{display:flex;align-items:center;gap:10px;margin:0 0 10px;padding:9px 10px;border:1px solid #d7e1ea;border-radius:12px;background:#f4f8fb}.reservationsPrintBar span{font-size:11px;color:#526574;font-weight:700}.reservationsPrintBtn{min-height:40px;font-weight:900;white-space:nowrap}@media(max-width:720px){.reservationsPrintBar{align-items:stretch;flex-direction:column;gap:5px}.reservationsPrintBtn{width:100%}.reservationsPrintBar span{font-size:10px;text-align:center}}</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)

if 'size:210mm 297mm' not in s or 'width:194mm' not in s or 'font-size:30px' not in s or 'Array.from({length:5})' not in s:
    raise SystemExit('Formato A4 verticale grande non inserito')

p.write_text(s)
