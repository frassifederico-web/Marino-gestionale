from pathlib import Path

p = Path('_site/index.html')
s = p.read_text()

# Dal 6 ottobre 2026:
# - le nuove prenotazioni partono sempre da Interno (20 tavoli);
# - il Dehors esterno è opzionale e mostra solo 61-66 e 71-76 (12 tavoli);
# - il vecchio valore "dehors" resta disponibile solo per modificare prenotazioni storiche.
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
  let internal=[...el.options].find(o=>o.value==='dehors');
  let outdoor=[...el.options].find(o=>o.value==='dehors_esterno');
  if(!outdoor){
    outdoor=document.createElement('option');
    outdoor.value='dehors_esterno';
    outdoor.textContent='Dehors esterno';
    if(internal)el.insertBefore(outdoor,internal.nextSibling);else el.appendChild(outdoor);
  }
  outdoor.disabled=!marinoDehorsZonesEnabled();
  if(internal)internal.textContent='Dehors interno';
  // Dal 6/10 il vecchio Dehors non è una destinazione per le nuove prenotazioni:
  // resta selezionabile solo quando si sta modificando una prenotazione storica.
  if(!marinoDehorsZonesEnabled()){
    if(internal)internal.hidden=false;
  }else if(!editing&&internal){
    internal.hidden=true;
    if(el.value==='dehors')el.value='interno';
  }
}
function marinoTableMatchesBookingRoom(t,room){
  if(!t)return false;
  if(room==='dehors_esterno')return marinoIsOutdoorDehorsTable(t);
  if(room==='dehors')return t.area==='dehors'&&!marinoIsOutdoorDehorsTable(t);
  return t.area===room;
}

const _renderPickerDehorsZonesBase=renderPicker;
renderPicker=function(){
  const roomEl=$('room'),chosen=roomEl?.value||'interno';
  const renderRoom=(chosen==='dehors_esterno')?'dehors':chosen;
  if(roomEl)roomEl.value=renderRoom;
  const out=_renderPickerDehorsZonesBase();
  if(roomEl)roomEl.value=chosen;
  refreshDehorsZoneMenu();
  if(marinoDehorsZonesEnabled()&&(chosen==='dehors'||chosen==='dehors_esterno')){
    allTables.filter(t=>t.area==='dehors').forEach(t=>{
      const card=marinoPickerCardForTable(t);
      if(card)card.style.display=marinoTableMatchesBookingRoom(t,chosen)?'':'none';
    });
  }
  return out;
};

const _syncNewBookingRoomToPrimaryAreaZonesBase=syncNewBookingRoomToPrimaryArea;
syncNewBookingRoomToPrimaryArea=async function(){
  const out=await _syncNewBookingRoomToPrimaryAreaZonesBase();
  refreshDehorsZoneMenu();
  if(!editing&&marinoDehorsZonesEnabled()){
    $('room').value='interno';
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
      if(codes.length&&codes.every(c=>MARINO_DEHORS_OUTDOOR_CODES.has(String(c)))){
        $('room').value='dehors_esterno';
      }else if(codes.some(c=>String(c).startsWith('D'))){
        $('room').value='dehors';
        const old=[...$('room').options].find(o=>o.value==='dehors');if(old)old.hidden=false;
      }
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
  if(room==='dehors_esterno'){
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

if "p_area:$('room').value" in s:
    s = s.replace("p_area:$('room').value", "p_area:marinoStorageArea($('room').value)", 1)
elif "p_area:marinoStorageArea($('room').value)" not in s:
    raise SystemExit('Campo p_area non trovato per normalizzazione dehors esterno')

checks = [
    'Dehors interno', 'Dehors esterno', '2026-10-06',
    "room').value='interno",
    'D7','D18','marinoStorageArea',
    'Per il dehors esterno seleziona esclusivamente i tavoli 61–66 e 71–76.',
    'MARINO_DEHORS_OUTDOOR_CODES'
]
for item in checks:
    if item not in s:
        raise SystemExit('Verifica zone dehors mancante: '+item)

p.write_text(s)
