from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('Punto inserimento selettore giorno Tavoli non trovato')

patch=r'''
let marinoMapSelectedDate=null;
function ensureMapDaySelector(){
  const wrap=$('mapDayTableFilterWrap');
  if(!wrap)return;
  if($('mapDaySelector'))return;
  const dayLabel=document.createElement('label');
  dayLabel.id='mapDaySelectorWrap';
  dayLabel.className='mapDaySelectorWrap';
  dayLabel.innerHTML='<span>Giorno tavoli</span><select id="mapDaySelector" aria-label="Giorno tavoli"></select>';
  wrap.insertBefore(dayLabel,wrap.firstChild);
  $('mapDaySelector').addEventListener('change',async()=>{
    const target=$('mapDaySelector').value;
    if(!target||target===$('date')?.value)return;
    marinoMapSelectedDate=target;
    $('date').value=target;
    const oldService=$('service')?.value||'';
    serviceOptions();
    if($('service')){
      const values=[...$('service').options].map(o=>o.value);
      if(values.includes(oldService))$('service').value=oldService;
      else{
        const dinner=values.find(v=>String(v).includes('cena'));
        $('service').value=dinner||values[0]||'';
      }
    }
    if(typeof refreshBookingTimesForService==='function')refreshBookingTimesForService(true);
    await loadAll();
    renderMap();
  });
}
function fillMapDaySelector(){
  ensureMapDaySelector();
  const el=$('mapDaySelector');if(!el)return;
  const current=$('date')?.value||marinoMapSelectedDate||marinoToday();
  const dates=(typeof marinoNextBookingDates==='function')?marinoNextBookingDates(31):[current];
  if(current&&!dates.includes(current))dates.unshift(current);
  el.innerHTML=dates.map(iso=>'<option value="'+iso+'">'+((typeof marinoDateLabel==='function')?marinoDateLabel(iso):iso)+'</option>').join('');
  el.value=current;
  marinoMapSelectedDate=current;
}

const _renderMapDaySelectorBase=renderMap;
renderMap=function(){
  const out=_renderMapDaySelectorBase();
  requestAnimationFrame(()=>{
    fillMapDaySelector();
    if(typeof applyMapDayTableFilter==='function')applyMapDayTableFilter();
  });
  return out;
};
'''

s=s.replace(marker,patch+'\n'+marker,1)

css=r'''<style id="marino-map-day-selector">
#mapDaySelectorWrap{display:block;min-width:210px;font-weight:800;color:#102c45}
#mapDaySelectorWrap>span{display:block;margin-bottom:4px;font-size:11px;color:#526574}
#mapDaySelector{min-height:38px;width:100%;border:1px solid #cbd9e3;border-radius:9px;background:#fff;padding:6px 9px;font-weight:900;color:#063f78}
@media(max-width:720px){#mapDaySelectorWrap{min-width:0;width:100%}#mapDaySelector{min-height:40px;font-size:13px}}
</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato per selettore giorno Tavoli')
s=s.replace('</head>',css+'</head>',1)

if 'id="mapDaySelector"' not in s or 'fillMapDaySelector' not in s or 'marino-map-day-selector' not in s:
    raise SystemExit('Selettore giorno Tavoli non inserito')

p.write_text(s)
