from pathlib import Path

p = Path('_site/index.html')
s = p.read_text()

s = s.replace(
    '<option value="dehors">Dehors</option>',
    '<option value="dehors_esterno">Dehors esterno</option>',
    1
)

helper = r'''
const MARINO_DEHORS_OUTDOOR_CODES=new Set(['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12']);
const MARINO_DEHORS_ZONE_START='2026-10-06';
function marinoBookingZoneDate(){return $('bookingDay')?.value||$('date')?.value||''}
function marinoDehorsZonesEnabled(){return true}
function marinoStorageArea(room){return room==='dehors_esterno'?'dehors':room}
function marinoIsOutdoorDehorsTable(t){return !!t&&t.area==='dehors'&&MARINO_DEHORS_OUTDOOR_CODES.has(String(t.code||''))}
function marinoTableGroup(t){if(t.area==='interno')return 'interno';if(marinoIsOutdoorDehorsTable(t))return 'dehors_esterno';return null}
function marinoOutdoorMinTables(party){return Math.max(1,Math.ceil(Number(party||0)/3))}
function marinoOutdoorSelected(){return selected.filter(c=>MARINO_DEHORS_OUTDOOR_CODES.has(String(c)))}
function marinoOutdoorCodesContiguous(codes){
  if(codes.length<=1)return true;
  const nums=codes.map(c=>Number((allTables.find(t=>String(t.code)===String(c))||{}).label)).filter(Number.isFinite).sort((a,b)=>a-b);
  if(nums.length!==codes.length)return false;
  for(let i=1;i<nums.length;i++)if(nums[i]!==nums[i-1]+1)return false;
  return true;
}
function marinoPickerSection(title,subtitle,items,kind){
  const wrap=document.createElement('div');wrap.className='marino-picker-section '+kind;
  const h=document.createElement('div');h.className='marino-picker-section-head';h.innerHTML='<b>'+title+'</b><span>'+subtitle+'</span>';wrap.appendChild(h);
  const grid=document.createElement('div');grid.className='tables';
  const start=tm($('arrival')?.value),end=start==null?null:start+120;
  grid.innerHTML=items.map(t=>{
    const bookings=links.filter(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==editing).map(x=>reservations.find(r=>r.id===x.reservation_id)).filter(r=>r&&r.status==='confermata');
    const std=bookings.some(r=>overlapsM(start,end,tm(r.arrival_time),tm(r.arrival_time)+120));
    const forced=bookings.some(r=>overlapsM(start,start==null?null:start+105,tm(r.arrival_time),tm(r.arrival_time)+105));
    let cl=forced?'busy':std?'forceTurn':bookings.length?'rebook':'free';
    if(selected.includes(t.code))cl+=' selected';
    const status=forced?'Occupato':std?'Forzabile':bookings.length?'Rimpiazzabile':'Libero';
    return '<button type="button" class="table '+cl+'" '+(forced?'disabled aria-disabled="true"':'data-marino-code="'+esc(t.code)+'"')+'><b>'+esc(t.label)+'</b><div class="muted">'+status+'</div></button>';
  }).join('');
  grid.querySelectorAll('[data-marino-code]').forEach(btn=>btn.addEventListener('click',()=>{
    const code=btn.dataset.marinoCode,clicked=allTables.find(t=>String(t.code)===String(code)),clickedGroup=marinoTableGroup(clicked);
    const selectedGroups=selected.map(sc=>marinoTableGroup(allTables.find(t=>String(t.code)===String(sc)))).filter(Boolean);
    if(!selected.includes(code)&&selectedGroups.length&&selectedGroups.some(g=>g!==clickedGroup))return alert('Non puoi unire tavoli Interno e Dehors esterno nella stessa prenotazione.');
    toggleTable(code);
  }));wrap.appendChild(grid);return wrap;
}
function marinoRenderAllBookingTables(){
  const picker=$('picker');if(!picker)return;picker.innerHTML='';const groups={interno:[],dehors_esterno:[]};
  allTables.filter(t=>t.active).forEach(t=>{const g=marinoTableGroup(t);if(g&&groups[g])groups[g].push(t)});
  const layout=document.createElement('div');layout.className='marino-picker-two-zones';
  layout.appendChild(marinoPickerSection('INTERNO','Tavoli interni',groups.interno,'marino-picker-interno'));
  if(marinoDehorsZonesEnabled())layout.appendChild(marinoPickerSection('DEHORS ESTERNO','Tavoli 51–56 · 61–66',groups.dehors_esterno,'marino-picker-dehors-esterno'));
  picker.appendChild(layout);
}
const _renderPickerDehorsZonesBase=renderPicker;
renderPicker=function(){const roomEl=$('room'),chosen=roomEl?.value||'interno';if(roomEl&&chosen==='dehors_esterno')roomEl.value='dehors';if(marinoDehorsZonesEnabled()){marinoRenderAllBookingTables();if(roomEl)roomEl.value=chosen;return}const out=_renderPickerDehorsZonesBase();if(roomEl)roomEl.value=chosen;return out};
const _saveBookingDehorsZonesBase=saveBooking;
saveBooking=async function(force){
  const party=Number($('party')?.value||$('partySize')?.value||$('covers')?.value||0),out=marinoOutdoorSelected();
  if(out.length){
    const need=marinoOutdoorMinTables(party);
    if(out.length<need)return alert('Per '+party+' coperti nel Dehors esterno servono almeno '+need+' tavoli uniti. Hai selezionato '+out.length+' tavoli.');
    if(!marinoOutdoorCodesContiguous(out))return alert('Nel Dehors esterno seleziona tavoli consecutivi e unibili lungo lo stesso lato.');
    if($('room'))$('room').value='dehors';
  }
  return _saveBookingDehorsZonesBase(force);
};
'''
marker='function _renderMapBase'
if marker not in s: raise SystemExit('Punto inserimento regole zone dehors non trovato')
if 'MARINO_DEHORS_OUTDOOR_CODES' not in s:s=s.replace(marker,helper+chr(10)+marker,1)
if "p_area:$('room').value" in s:s=s.replace("p_area:$('room').value","p_area:marinoStorageArea($('room').value)",1)
css=r'''<style id="marino-booking-zones-ui">
.marino-picker-two-zones{display:grid;grid-template-columns:minmax(0,2fr) minmax(260px,1fr);gap:12px;align-items:start}.marino-picker-section{margin-top:12px;padding:10px;border-radius:14px;border:1px solid #c8d7df;background:#f7fbf5}.marino-picker-section-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-bottom:8px}.marino-picker-interno .table.free{background:var(--greenbg);border-color:#8ab86d;color:var(--green)}.marino-picker-dehors-esterno{background:#e5eef7;border-color:#7198bd}.marino-picker-dehors-esterno .table.free{background:#b9d9f5!important;border-color:#397bb8!important;color:#063f78!important}.marino-picker-dehors-esterno .table.busy{background:#f1d4cf;border-color:#b86d61;color:#7d241b}@media(max-width:720px){.marino-picker-two-zones{grid-template-columns:1fr}}
</style>'''
if 'marino-booking-zones-ui' not in s:s=s.replace('</head>',css+'</head>',1)
for item in ['marinoOutdoorMinTables','marinoOutdoorCodesContiguous','DEHORS ESTERNO','Tavoli 51–56 · 61–66']:
    if item not in s:raise SystemExit('Verifica mancante: '+item)
p.write_text(s)
