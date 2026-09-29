from pathlib import Path
import re

p = Path('_site/index.html')
s = p.read_text()

# Dal 6 ottobre 2026: selezione esplicita tra dehors interno e dehors esterno.
# I tavoli esterni sono D7-D18 (etichette 61-66 e 71-76); gli altri 12 restano interni.
s = s.replace(
    '<option value="dehors">Dehors</option>',
    '<option value="dehors">Dehors interno</option><option value="dehors_esterno">Dehors esterno</option>',
    1
)

helper = r'''
const MARINO_DEHORS_OUTDOOR_CODES=new Set(['D7','D8','D9','D10','D11','D12','D13','D14','D15','D16','D17','D18']);
const MARINO_DEHORS_ZONE_START='2026-10-06';
function marinoBookingZoneDate(){return $('bookingDay')?.value||$('date')?.value||''}
function marinoDehorsZonesEnabled(){return marinoBookingZoneDate()>=MARINO_DEHORS_ZONE_START}
function marinoStorageArea(room){return room==='dehors_esterno'?'dehors':room}
function marinoIsOutdoorDehorsTable(t){return !!t&&t.area==='dehors'&&MARINO_DEHORS_OUTDOOR_CODES.has(String(t.code||''))}
function marinoTableMatchesBookingRoom(t,room){
  if(!t||t.area!==marinoStorageArea(room))return false;
  if(t.area!=='dehors'||!marinoDehorsZonesEnabled())return true;
  return room==='dehors_esterno'?marinoIsOutdoorDehorsTable(t):!marinoIsOutdoorDehorsTable(t);
}
function refreshDehorsZoneMenu(){
  const el=$('room');if(!el)return;
  let internal=[...el.options].find(o=>o.value==='dehors');
  if(internal)internal.textContent=marinoDehorsZonesEnabled()?'Dehors interno':'Dehors';
  let outdoor=[...el.options].find(o=>o.value==='dehors_esterno');
  if(!outdoor){outdoor=document.createElement('option');outdoor.value='dehors_esterno';outdoor.textContent='Dehors esterno';const after=internal?.nextSibling;if(after)el.insertBefore(outdoor,after);else el.appendChild(outdoor)}
  outdoor.disabled=!marinoDehorsZonesEnabled();
  if(!marinoDehorsZonesEnabled()&&el.value==='dehors_esterno')el.value='dehors';
}
function marinoPickerCardForTable(t){
  const picker=$('picker');if(!picker)return null;
  const label=String(t?.label||'').trim(),code=String(t?.code||'').trim();
  return [...picker.querySelectorAll('.table')].find(el=>{
    const txt=(el.textContent||'').trim();
    return (label&&txt.startsWith(label))||(code&&txt.startsWith(code));
  })||null;
}

const _renderPickerDehorsZonesBase=renderPicker;
renderPicker=function(){
  const roomEl=$('room'),chosen=roomEl?.value||'interno';
  if(chosen==='dehors_esterno')roomEl.value='dehors';
  const out=_renderPickerDehorsZonesBase();
  if(roomEl)roomEl.value=chosen;
  refreshDehorsZoneMenu();
  if(marinoDehorsZonesEnabled()&&(chosen==='dehors'||chosen==='dehors_esterno')){
    allTables.filter(t=>t.area==='dehors').forEach(t=>{
      const card=marinoPickerCardForTable(t);if(card)card.style.display=marinoTableMatchesBookingRoom(t,chosen)?'':'none';
    });
  }
  return out;
};

const _syncNewBookingRoomToPrimaryAreaZonesBase=syncNewBookingRoomToPrimaryArea;
syncNewBookingRoomToPrimaryArea=async function(){
  const out=await _syncNewBookingRoomToPrimaryAreaZonesBase();
  refreshDehorsZoneMenu();
  if(!editing&&marinoDehorsZonesEnabled()){
    $('room').value='dehors';
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
      else if(codes.some(c=>String(c).startsWith('D')))$('room').value='dehors';
      renderPicker();
    }
  },0);
  return out;
};

const _saveBookingDehorsZonesBase=saveBooking;
saveBooking=async function(force){
  if($('room')?.value==='dehors_esterno'&&!marinoDehorsZonesEnabled()){
    return alert('Il dehors esterno è prenotabile dal 6 ottobre 2026.');
  }
  if($('room')?.value==='dehors_esterno'){
    const selectedTables=allTables.filter(t=>selected.includes(t.code));
    if(!selectedTables.length||selectedTables.some(t=>!marinoIsOutdoorDehorsTable(t))){
      return alert('Per il dehors esterno seleziona esclusivamente i tavoli 61–66 e 71–76.');
    }
  }
  return _saveBookingDehorsZonesBase(force);
};

if($('room')){
  $('room').addEventListener('change',()=>{selected=[];refreshDehorsZoneMenu();renderPicker()});
}
if($('bookingDay'))$('bookingDay').addEventListener('change',()=>{refreshDehorsZoneMenu()});
if($('date'))$('date').addEventListener('change',()=>{refreshDehorsZoneMenu()});
refreshDehorsZoneMenu();
'''

marker = 'function _renderMapBase'
if marker not in s:
    raise SystemExit('Punto inserimento regole zone dehors non trovato')
if 'MARINO_DEHORS_OUTDOOR_CODES' not in s:
    s = s.replace(marker, helper + '\n' + marker, 1)

# La colonna area nel DB resta l'enum esistente (interno/dehors): la scelta esterno
# distingue i tavoli, ma viene salvata come area dehors.
if "p_area:$('room').value" in s:
    s = s.replace("p_area:$('room').value", "p_area:marinoStorageArea($('room').value)", 1)
elif "p_area:marinoStorageArea($('room').value)" not in s:
    raise SystemExit('Campo p_area non trovato per normalizzazione dehors esterno')

checks = [
    'Dehors interno', 'Dehors esterno', '2026-10-06',
    'D7','D18','marinoStorageArea($(' + "'room').value)",
    'Per il dehors esterno seleziona esclusivamente i tavoli 61–66 e 71–76.',
    'MARINO_DEHORS_OUTDOOR_CODES'
]
for item in checks:
    if item not in s:
        raise SystemExit('Verifica zone dehors mancante: '+item)

p.write_text(s)
