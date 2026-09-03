from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('Punto inserimento regole dehors/filtro tavoli non trovato')

patch=r'''
const _selectionRangeDehorsBase=selectionRange;
selectionRange=function(){
  const ts=allTables.filter(t=>selected.includes(t.code));
  if(ts.length&&$('room')?.value==='dehors'){
    const n=ts.length;
    if(n===1)return {mn:1,mx:4};
    if(n===2)return {mn:4,mx:8};
    return {mn:2*n+1,mx:2*n+2};
  }
  return _selectionRangeDehorsBase();
};

let marinoMapTableFilter='all';
function mapDayUsedCodes(){
  const valid=new Set(reservations.filter(r=>r&&(r.status==='confermata'||r.status==='completata')).map(r=>r.id));
  return new Set(links.filter(x=>valid.has(x.reservation_id)&&x.restaurant_tables?.code).map(x=>x.restaurant_tables.code));
}
function mapCardForTable(t){
  const page=$('map')||document;
  const candidates=[...page.querySelectorAll('.table,button')].filter(el=>!el.closest('#picker')&&!el.closest('.modal')&&!el.closest('#mapDayTableFilterWrap'));
  return candidates.find(el=>{
    const txt=(el.textContent||'').trim();
    const label=String(t.label||'').trim(),code=String(t.code||'').trim();
    return txt===label||txt===code||txt.startsWith(label+' ')||txt.startsWith(code+' ');
  })||null;
}
function ensureMapDayTableFilter(){
  if($('mapDayTableFilter'))return;
  const page=$('map');if(!page)return;
  const card=page.querySelector('.card')||page;
  const wrap=document.createElement('div');
  wrap.id='mapDayTableFilterWrap';
  wrap.className='mapDayTableFilterWrap';
  wrap.innerHTML='<label><span>Visualizza tavoli del giorno</span><select id="mapDayTableFilter"><option value="all">Tutti i tavoli</option><option value="occupied">Solo occupati</option><option value="free">Solo liberi</option></select></label><div id="mapDayTableFilterSummary" class="muted"></div>';
  card.insertBefore(wrap,card.firstChild);
  $('mapDayTableFilter').value=marinoMapTableFilter;
  $('mapDayTableFilter').addEventListener('change',()=>{marinoMapTableFilter=$('mapDayTableFilter').value;applyMapDayTableFilter()});
}
function applyMapDayTableFilter(){
  ensureMapDayTableFilter();
  const used=mapDayUsedCodes();
  let shown=0,total=0;
  allTables.filter(t=>t.active).forEach(t=>{
    const card=mapCardForTable(t);if(!card)return;
    total++;
    const occupied=used.has(t.code);
    const visible=marinoMapTableFilter==='all'||(marinoMapTableFilter==='occupied'&&occupied)||(marinoMapTableFilter==='free'&&!occupied);
    card.style.display=visible?'':'none';
    if(visible)shown++;
  });
  const summary=$('mapDayTableFilterSummary');
  if(summary){
    const date=$('date')?.value||'';
    const occupied=[...used].length;
    const active=allTables.filter(t=>t.active).length;
    summary.textContent=(date?marinoDateLabel(date)+' · ':'')+occupied+' occupati · '+Math.max(0,active-occupied)+' liberi'+(marinoMapTableFilter==='all'?'':' · '+shown+' visualizzati');
  }
}

const _renderMapDayFilterBase=renderMap;
renderMap=function(){
  const out=_renderMapDayFilterBase();
  requestAnimationFrame(()=>{ensureMapDayTableFilter();applyMapDayTableFilter()});
  return out;
};
'''

s=s.replace(marker,patch+'\n'+marker,1)

css=r'''<style id="marino-map-day-filter">
.mapDayTableFilterWrap{display:flex;align-items:end;justify-content:space-between;gap:10px;margin:0 0 12px;padding:10px 12px;border:1px solid #dfe8ef;border-radius:12px;background:#f7fafc}
.mapDayTableFilterWrap label{display:block;min-width:190px;font-weight:800;color:#102c45}
.mapDayTableFilterWrap label>span{display:block;margin-bottom:4px;font-size:11px;color:#526574}
#mapDayTableFilter{min-height:38px;border:1px solid #cbd9e3;border-radius:9px;background:#fff;padding:6px 9px;font-weight:800;color:#063f78}
#mapDayTableFilterSummary{font-size:11px;font-weight:750;text-align:right}
@media(max-width:720px){.mapDayTableFilterWrap{align-items:stretch;flex-direction:column;padding:8px 9px}.mapDayTableFilterWrap label{min-width:0}#mapDayTableFilter{width:100%}#mapDayTableFilterSummary{text-align:left;font-size:10px}}
</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato per filtro tavoli')
s=s.replace('</head>',css+'</head>',1)

if 'mapDayTableFilter' not in s or 'Solo occupati' not in s or 'n===2)return {mn:4,mx:8}' not in s:
    raise SystemExit('Filtro tavoli/regola dehors non inseriti')

p.write_text(s)
