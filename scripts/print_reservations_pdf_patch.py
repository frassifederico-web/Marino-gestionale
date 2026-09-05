from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

patch=r'''
function marinoPrintEsc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function ensureReservationsPrintButton(){
  const host=$('bookingList');if(!host||document.getElementById('downloadReservationsPdfBtn'))return;
  const bar=document.createElement('div');bar.className='reservationsPrintBar';
  bar.innerHTML='<button id="downloadReservationsPdfBtn" type="button" class="primary reservationsPrintBtn">⬇ Scarica lista prenotazioni</button><span>PDF/stampa con tavolo assegnato da compilare a mano</span>';
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
  const fs=n>28?7.2:n>22?8:n>16?8.8:9.6;
  const pad=n>28?3:n>20?4:5;
  const body=rows.map((r,i)=>{
    const note=String(r.notes||'').trim();
    return '<tr><td class="n">'+(i+1)+'</td><td class="ora">'+marinoPrintEsc(hhmm(r.arrival_time))+'</td><td class="nome"><b>'+marinoPrintEsc(r.guest_name||'')+'</b></td><td class="cop">'+Number(r.party_size||0)+'</td><td class="note">'+(note?marinoPrintEsc(note):'')+'</td><td class="tavolo"></td></tr>';
  }).join('');
  const html='<!doctype html><html><head><meta charset="utf-8"><title>MARINO - Lista prenotazioni '+date+'</title><style>'+
    '@page{size:A4 portrait;margin:7mm}*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#102c45}.head{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #063f78;padding-bottom:5px;margin-bottom:6px}.brand{font-size:18px;font-weight:900;letter-spacing:.08em;color:#063f78}.date{font-size:11px;font-weight:800;text-transform:capitalize}.tot{font-size:9px;margin-top:2px;color:#4d5c67}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:'+fs+'pt}th,td{border:1px solid #9aa8b3;padding:'+pad+'px 4px;vertical-align:middle;line-height:1.15}th{background:#eef5fb;color:#063f78;font-size:'+(fs-.4)+'pt;text-transform:uppercase;letter-spacing:.02em}.n{width:5%;text-align:center}.ora{width:10%;text-align:center;font-weight:800}.nome{width:26%}.cop{width:8%;text-align:center;font-weight:800}.note{width:31%;font-weight:650}.tavolo{width:20%;min-height:20px}.foot{margin-top:5px;font-size:7.5pt;color:#5b6770;display:flex;justify-content:space-between}.noRows{padding:30px;text-align:center;border:1px solid #ccd6dd}'+
    '</style></head><body><div class="head"><div><div class="brand">MARINO</div><div class="date">Lista prenotazioni · '+marinoPrintEsc(label)+'</div></div><div style="text-align:right"><div><b>'+rows.length+' prenotazioni</b></div><div class="tot">'+covers+' coperti totali</div></div></div>'+
    (rows.length?'<table><thead><tr><th class="n">#</th><th class="ora">Ora</th><th class="nome">Prenotazione</th><th class="cop">Cop.</th><th class="note">Note</th><th class="tavolo">Tavolo assegnato</th></tr></thead><tbody>'+body+'</tbody></table>':'<div class="noRows">Nessuna prenotazione per il servizio.</div>')+
    '<div class="foot"><span>Colonna “Tavolo assegnato” lasciata libera per compilazione manuale.</span><span>MARINO · uso interno sala</span></div><script>window.onload=()=>setTimeout(()=>window.print(),180)<\/script></body></html>';
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

p.write_text(s)
