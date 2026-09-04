from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('Punto inserimento dettaglio occupazione modifica non trovato')

patch=r'''
function ensureEditOccupancyLegend(){
  if($('editOccupancyLegend'))return $('editOccupancyLegend');
  const picker=$('picker');if(!picker||!picker.parentElement)return null;
  const box=document.createElement('div');
  box.id='editOccupancyLegend';
  box.className='editOccupancyLegend';
  picker.parentElement.insertBefore(box,picker);
  return box;
}
function editOccNotes(r){
  const note=String(r?.notes||'').trim();
  return note?'<div class="editOccNotes"><b>NOTE:</b> '+esc(note)+'</div>':'';
}
function renderEditOccupancyLegend(){
  const box=ensureEditOccupancyLegend();if(!box)return;
  if(!editing){box.innerHTML='';box.style.display='none';return}
  const room=$('room')?.value||'';
  const occupied=[];
  allTables.filter(t=>t.active&&t.area===room).forEach(t=>{
    const rs=links.filter(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==editing)
      .map(x=>reservations.find(r=>r.id===x.reservation_id))
      .filter(r=>r&&r.status==='confermata')
      .sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));
    rs.forEach(r=>occupied.push({t,r}));
  });
  if(!occupied.length){
    box.style.display='block';
    box.innerHTML='<div class="editOccTitle">Tavoli occupati nel servizio</div><div class="muted">Nessun altro tavolo occupato.</div>';
    return;
  }
  box.style.display='block';
  box.innerHTML='<div class="editOccTitle">Tavoli occupati nel servizio</div><div class="editOccGrid">'+occupied.map(x=>'<div class="editOccRow"><div class="editOccMain"><b>'+esc(x.t.label||x.t.code)+'</b><span>'+esc(x.r.guest_name||'—')+'</span><span>'+Number(x.r.party_size||0)+' cop.</span><span>'+esc(hhmm(x.r.arrival_time))+'</span></div>'+editOccNotes(x.r)+'</div>').join('')+'</div>';
}

const _renderPickerOccBase=renderPicker;
renderPicker=function(){
  const out=_renderPickerOccBase();
  if(editing){
    const room=$('room')?.value,start=tm($('arrival')?.value),endVal=$('endTime')?.value;
    const forceEnd=effEnd($('arrival')?.value,endVal,90);
    allTables.filter(t=>t.area===room&&t.active).forEach(t=>{
      const card=[...$('picker').querySelectorAll('[data-table-code],.table')].find(el=>{
        const txt=(el.textContent||'').trim();
        const label=String(t.label||'').trim(),code=String(t.code||'').trim();
        return txt.startsWith(label)||txt.startsWith(code);
      });
      if(!card)return;
      const rs=links.filter(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==editing)
        .map(x=>reservations.find(r=>r.id===x.reservation_id)).filter(Boolean)
        .filter(r=>overlapsM(start,forceEnd,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,90)));
      card.querySelectorAll('.editOccInline').forEach(x=>x.remove());
      if(rs.length){
        const d=document.createElement('div');d.className='editOccInline';
        d.innerHTML=rs.map(r=>'<div class="editOccInlineBooking"><div><b>'+esc(r.guest_name||'—')+'</b> · '+Number(r.party_size||0)+' cop. · '+esc(hhmm(r.arrival_time))+'</div>'+editOccNotes(r)+'</div>').join('');
        card.appendChild(d);
      }
    });
  }
  renderEditOccupancyLegend();
  return out;
};

const _editBookingOccBase=editBooking;
editBooking=function(id){
  const out=_editBookingOccBase(id);
  setTimeout(()=>{renderPicker();renderEditOccupancyLegend()},0);
  return out;
};
'''

s=s.replace(marker,patch+'\n'+marker,1)

css=r'''<style id="marino-edit-occupancy">
.editOccupancyLegend{display:none;margin:0 0 10px;padding:10px;border:1px solid #dfe8ef;border-radius:11px;background:#f8fbfd}
.editOccTitle{font-weight:900;color:#063f78;margin-bottom:6px;font-size:12px}
.editOccGrid{display:grid;gap:5px}
.editOccRow{display:block;padding:7px;border-radius:8px;background:#fff;border:1px solid #e5edf3;font-size:11px;color:#102c45}
.editOccMain{display:grid;grid-template-columns:minmax(70px,1fr) minmax(100px,2fr) auto auto;gap:7px;align-items:center}
.editOccNotes{margin-top:5px;padding:5px 7px;border-radius:7px;background:#fff4d8;border:1px solid #edd38a;color:#6d4c00;font-size:10px;line-height:1.3;font-weight:750;white-space:normal;overflow-wrap:anywhere}
.editOccNotes b{font-weight:950}
.editOccInline{margin-top:5px;padding-top:4px;border-top:1px solid rgba(185,50,50,.25);font-size:9px;line-height:1.2;color:#8f2424;font-weight:700}
.editOccInlineBooking+.editOccInlineBooking{margin-top:5px;padding-top:5px;border-top:1px dashed rgba(185,50,50,.25)}
.editOccInline .editOccNotes{font-size:8.5px;margin-top:3px;padding:4px 5px;background:#fff4d8;color:#6d4c00;border-color:#edd38a}
@media(max-width:720px){.editOccMain{grid-template-columns:1fr 1.6fr auto;font-size:10px}.editOccMain span:last-child{grid-column:1/-1;color:#526574}.editOccupancyLegend{padding:8px}.editOccNotes{font-size:9.5px}}
</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato per dettaglio occupazione modifica')
s=s.replace('</head>',css+'</head>',1)

if 'editOccupancyLegend' not in s or 'editOccInline' not in s or 'Tavoli occupati nel servizio' not in s or 'editOccNotes' not in s or '<b>NOTE:</b>' not in s:
    raise SystemExit('Dettaglio occupazione/note modifica non inserito')

p.write_text(s)
