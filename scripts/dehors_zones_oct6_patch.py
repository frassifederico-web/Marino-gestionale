from pathlib import Path

p = Path('_site/index.html')
s = p.read_text()

s = s.replace(
    '<option value="dehors">Dehors</option>',
    '<option value="dehors_esterno">Dehors esterno</option>',
    1
)

helper = r'''
const MARINO_DEHORS_OUTDOOR_CODES=new Set(['D7','D8','D9','D10','D11','D12','D13','D14','D15','D16','D17','D18']);
const MARINO_DEHORS_ZONE_START='2026-10-06';
function marinoBookingZoneDate(){return $('bookingDay')?.value||$('date')?.value||''}
function marinoDehorsZonesEnabled(){return marinoBookingZoneDate()>=MARINO_DEHORS_ZONE_START}
function marinoStorageArea(room){return room==='dehors_esterno'?'dehors':room}
function marinoIsOutdoorDehorsTable(t){return !!t&&t.area==='dehors'&&MARINO_DEHORS_OUTDOOR_CODES.has(String(t.code||''))}
function marinoTableGroup(t){
  if(t.area==='interno')return 'interno';
  if(marinoIsOutdoorDehorsTable(t))return 'dehors_esterno';
  return null;
}
function marinoPickerCardForTable(t){
  const picker=$('picker');if(!picker)return null;
  const label=String(t?.label||'').trim(),code=String(t?.code||'').trim();
  return [...picker.querySelectorAll('.table')].find(el=>{
    const txt=(el.textContent||'').trim();
    return (label&&txt.startsWith(label))||(code&&txt.startsWith(code));
  })||null;
}
function refreshDehorsZoneMenu(){
  const el=$('room');if(!el)return;
  let outdoor=[...el.options].find(o=>o.value==='dehors_esterno');
  if(!outdoor){
    outdoor=document.createElement('option');
    outdoor.value='dehors_esterno';
    outdoor.textContent='Dehors esterno';
    el.appendChild(outdoor);
  }
  outdoor.disabled=!marinoDehorsZonesEnabled();
  const internal=[...el.options].find(o=>o.value==='dehors');
  if(internal)internal.textContent='Dehors interno';
  if(!marinoDehorsZonesEnabled()&&el.value==='dehors_esterno')el.value='dehors';
}
function marinoPickerSection(title,subtitle,items,kind){
  const wrap=document.createElement('div');
  wrap.className='marino-picker-section '+kind;
  const h=document.createElement('div');
  h.className='marino-picker-section-head';
  h.innerHTML='<b>'+title+'</b><span>'+subtitle+'</span>';
  wrap.appendChild(h);
  const grid=document.createElement('div');
  grid.className='tables';
  grid.innerHTML=items.map(t=>{
    const count=links.filter(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==editing).length;
    let cl=count?'busy':'free';
    if(selected.includes(t.code))cl+=' selected';
    return '<button type="button" class="table '+cl+'" data-marino-code="'+esc(t.code)+'"><b>'+esc(t.label)+'</b><div class="muted">'+(count?'Già usato nella serata':'Libero')+'</div></button>';
  }).join('');
  grid.querySelectorAll('[data-marino-code]').forEach(btn=>btn.addEventListener('click',()=>toggleTable(btn.dataset.marinoCode)));
  wrap.appendChild(grid);
  return wrap;
}
function marinoRenderAllBookingTables(){
  const picker=$('picker');if(!picker)return;
  picker.innerHTML='';
  const groups={interno:[],dehors_esterno:[]};
  allTables.filter(t=>t.active).forEach(t=>{
    const g=marinoTableGroup(t);
    if(groups[g])groups[g].push(t);
  });
  picker.appendChild(marinoPickerSection('INTERNO','20 tavoli',groups.interno,'marino-picker-interno'));
  picker.appendChild(marinoPickerSection('DEHORS INTERNO','Tavoli del dehors principale',groups.dehors_interno,'marino-picker-dehors-interno'));
  if(marinoDehorsZonesEnabled()){
    picker.appendChild(marinoPickerSection('DEHORS ESTERNO','12 tavoli · opzionale dal 6 ottobre',groups.dehors_esterno,'marino-picker-dehors-esterno'));
  }
}
const _renderPickerDehorsZonesBase=renderPicker;
renderPicker=function(){
  const roomEl=$('room'),chosen=roomEl?.value||'interno';
  if(roomEl&&chosen==='dehors_esterno')roomEl.value='dehors';
  if(marinoDehorsZonesEnabled()){
    marinoRenderAllBookingTables();
    if(roomEl)roomEl.value=chosen;
    refreshDehorsZoneMenu();
    return;
  }
  const out=_renderPickerDehorsZonesBase();
  if(roomEl)roomEl.value=chosen;
  refreshDehorsZoneMenu();
  return out;
};
const _syncNewBookingRoomToPrimaryAreaZonesBase=syncNewBookingRoomToPrimaryArea;
syncNewBookingRoomToPrimaryArea=async function(){
  const out=await _syncNewBookingRoomToPrimaryAreaZonesBase();
  refreshDehorsZoneMenu();
  if(!editing&&marinoDehorsZonesEnabled()){
    $('room').value=$('primaryArea')?.value||'interno';
    selected=[];
    renderPicker();
  }
  return out;
};
const _editBookingDehorsZonesBase=editBooking;
editBooking=function(id){
  const out=_editBookingDehorsZonesBase(id);
  setTimeout(()=>{
    refreshDehorsZoneMenu();
    if(marinoDehorsZonesEnabled()){
      const codes=tableCodesForRes(id)||[];
      if(codes.length&&codes.every(c=>MARINO_DEHORS_OUTDOOR_CODES.has(String(c))))$('room').value='dehors_esterno';
      else if(codes.some(c=>String(c).startsWith('D')))$('room').value='interno';
      renderPicker();
    }
  },0);
  return out;
};
const _saveBookingDehorsZonesBase=saveBooking;
saveBooking=async function(force){
  const room=$('room')?.value||'';
  if(room==='dehors_esterno'&&!marinoDehorsZonesEnabled()){
    return alert('Il dehors esterno è prenotabile dal 6 ottobre 2026.');
  }
  if(room==='dehors_esterno')$('room').value='dehors';
  const out=await _saveBookingDehorsZonesBase(force);
  if(room==='dehors_esterno'&&$('room'))$('room').value='dehors';
  return out;
};
if($('room'))$('room').addEventListener('change',()=>{selected=[];refreshDehorsZoneMenu();renderPicker()});
if($('bookingDay'))$('bookingDay').addEventListener('change',()=>{refreshDehorsZoneMenu()});
if($('date'))$('date').addEventListener('change',()=>{refreshDehorsZoneMenu()});
refreshDehorsZoneMenu();
'''
marker='function _renderMapBase'
if marker not in s: raise SystemExit('Punto inserimento regole zone dehors non trovato')
if 'MARINO_DEHORS_OUTDOOR_CODES' not in s:s=s.replace(marker,helper+chr(10)+marker,1)
if "p_area:$('room').value" in s:s=s.replace("p_area:$('room').value","p_area:marinoStorageArea($('room').value)",1)
elif "p_area:marinoStorageArea($('room').value)" not in s:raise SystemExit('Campo p_area non trovato')
css=r'''<style id="marino-booking-zones-ui">
.marino-picker-section{margin-top:12px;padding:10px;border-radius:14px;border:1px solid #c8d7df;background:#f7fbf5}
.marino-picker-section-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-bottom:8px;color:#245b2d}
.marino-picker-section-head b{font-size:13px;letter-spacing:.04em}.marino-picker-section-head span{font-size:11px;color:#64756a}
.marino-picker-dehors-interno{background:#edf7e9;border-color:#9cc18d}.marino-picker-dehors-interno .marino-picker-section-head{color:#2f6b38}
.marino-picker-dehors-esterno{background:#e5eef7;border-color:#7198bd}.marino-picker-dehors-esterno .marino-picker-section-head{color:#063f78}
.marino-picker-dehors-esterno .table.free{background:#d7e7f5;border-color:#7198bd;color:#063f78}
.marino-picker-dehors-esterno .table.busy{background:#f1d4cf;border-color:#b86d61;color:#7d241b}
@media(max-width:720px){.marino-picker-section{padding:8px}.marino-picker-section-head{flex-direction:column;gap:2px}}
</style>'''
if 'marino-booking-zones-ui' not in s:
    if '</head>' not in s: raise SystemExit('head non trovato')
    s=s.replace('</head>',css+'</head>',1)
for item in ['marinoRenderAllBookingTables','DEHORS ESTERNO','12 tavoli · opzionale dal 6 ottobre','marino-picker-dehors-esterno']:
    if item not in s: raise SystemExit('Verifica mancante: '+item)
p.write_text(s)
