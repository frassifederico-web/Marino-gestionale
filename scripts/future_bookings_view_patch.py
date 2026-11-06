from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()
marker='<!-- marino-future-bookings-v1 -->'
if marker in s:
    raise SystemExit('Future bookings patch already applied')
anchor='<div id="bookingList"></div>'
if anchor not in s:
    raise SystemExit('Booking list anchor not found')
s=s.replace(anchor,anchor+'''\n<!-- marino-future-bookings-v1 --><div id="marinoFutureBookings" class="card" style="margin-top:14px"><h3>Prossimi 31 giorni · prenotazioni future</h3><div class="actions"><button type="button" class="secondary" id="marinoRefreshFuture" onclick="marinoLoadFutureBookings()">Aggiorna elenco</button></div><div id="marinoFutureStatus" class="muted" aria-live="polite">Apri Prenotazioni per caricare i giorni successivi.</div><div id="marinoFutureList"></div></div>''',1)
js=r"""
// Independent, read-only future bookings view. Does not change service-date state.
let marinoFutureLoading=false;
async function marinoLoadFutureBookings(){
  if(!profile||marinoFutureLoading)return;
  const status=document.getElementById('marinoFutureStatus'),target=document.getElementById('marinoFutureList');
  if(!status||!target)return;
  marinoFutureLoading=true;
  status.textContent='Caricamento prenotazioni future…';
  try{
    const today=typeof marinoToday==='function'?marinoToday():new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Rome',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    const start=new Date(today+'T12:00:00');
    start.setDate(start.getDate()+32);
    const until=start.getFullYear()+'-'+String(start.getMonth()+1).padStart(2,'0')+'-'+String(start.getDate()).padStart(2,'0');
    const result=await db.from('reservations').select('id,service_date,service_code,arrival_time,guest_name,party_size,area,status').gt('service_date',today).lt('service_date',until).neq('status','annullata').order('service_date',{ascending:true}).order('arrival_time',{ascending:true}).limit(1000);
    if(result.error)throw result.error;
    const bookings=result.data||[];
    const ids=bookings.map(b=>b.id);
    let tableLinks=[];
    for(let i=0;i<ids.length;i+=100){
      const q=await db.from('reservation_tables').select('reservation_id,table_id').in('reservation_id',ids.slice(i,i+100));
      if(q.error)throw q.error;
      tableLinks.push(...(q.data||[]));
    }
    const tableNames=new Map();
    for(const link of tableLinks){
      const t=allTables.find(t=>String(t.id)===String(link.table_id));
      if(!t)continue;
      const k=String(link.reservation_id);
      tableNames.set(k,[...(tableNames.get(k)||[]),t.label||t.code]);
    }
    const byDay=new Map();
    for(const b of bookings){
      if(!byDay.has(b.service_date))byDay.set(b.service_date,[]);
      byDay.get(b.service_date).push(b);
    }
    target.replaceChildren();
    for(const [day,rows] of byDay){
      const section=document.createElement('section');
      section.className='marinoFutureDay';
      const heading=document.createElement('h4');
      heading.textContent=new Intl.DateTimeFormat('it-IT',{weekday:'long',day:'2-digit',month:'long'}).format(new Date(day+'T12:00:00'))+' · '+rows.length+' prenotazioni';
      section.append(heading);
      for(const b of rows){
        const line=document.createElement('div');
        line.className='row';
        const info=document.createElement('div');
        const name=document.createElement('b');
        name.textContent=(b.guest_name||'—')+' · '+Number(b.party_size||0)+' coperti';
        const detail=document.createElement('div');
        detail.className='muted';
        detail.textContent=String(b.arrival_time||'').slice(0,5)+' · '+String(b.service_code||'').replaceAll('-',' ')+' · Tavolo '+(tableNames.get(String(b.id))||['da assegnare']).join(' + ')+' · '+(b.area||'');
        info.append(name,detail);line.append(info);section.append(line);
      }
      target.append(section);
    }
    status.textContent=bookings.length+' prenotazioni future in '+byDay.size+' giorni (prossimi 31 giorni).';
    if(!bookings.length)target.textContent='Nessuna prenotazione futura nel periodo.';
    if(bookings.length===1000)status.textContent+=' Limite raggiunto: elenco potenzialmente incompleto.';
  }catch(e){
    console.error('MARINO future bookings loading failed',e);
    status.textContent='Errore nel caricamento delle prenotazioni future. Riprova con Aggiorna elenco.';
    target.replaceChildren();
  }finally{marinoFutureLoading=false}
}
const marinoFutureShowPageBase=showPage;
showPage=function(id,...args){
  const result=marinoFutureShowPageBase.call(this,id,...args);
  if(id==='bookings')void marinoLoadFutureBookings();
  return result;
};
"""
end=s.rfind('</script>')
if end<0:raise SystemExit('Script closing tag not found')
s=s[:end]+'\n'+js+'\n'+s[end:]
s=s.replace('</head>','<style id="marino-future-bookings-css">.marinoFutureDay{padding:8px 0;border-top:1px solid #ddd}.marinoFutureDay h4{margin:10px 0;text-transform:capitalize}.marinoFutureDay .row{padding:8px 0}</style></head>',1)
p.write_text(s)
print('MARINO: future bookings read-only view added')
