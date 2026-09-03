from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('Punto inserimento menu giorno prenotazione non trovato')

patch=r'''
function marinoDateLabel(iso){
  try{return new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long',day:'2-digit',month:'2-digit'}).format(new Date(iso+'T12:00:00'))}
  catch(e){return iso}
}
function marinoNextBookingDates(days=31){
  const out=[];
  const base=new Date(marinoToday()+'T12:00:00');
  for(let i=0;i<days;i++){
    const d=new Date(base);d.setDate(base.getDate()+i);
    const iso=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
    out.push(iso);
  }
  return out;
}
async function syncNewBookingRoomToPrimaryArea(){
  if(editing)return;
  const date=$('date')?.value,service=$('service')?.value;
  if(!date||!service||!$('room'))return;
  const q=await db.from('service_settings').select('primary_area').eq('service_date',date).eq('service_code',service).maybeSingle();
  if(q.error){console.warn('Sala principale:',q.error.message);return}
  const area=q.data?.primary_area;
  if(area&&['interno','dehors'].includes(area)){
    $('room').value=area;
    selected=[];
    renderPicker();
  }
}
function ensureBookingDayField(){
  if($('bookingDay'))return $('bookingDay');
  const guest=$('guest');
  if(!guest)return null;
  const host=guest.closest('label')||guest.parentElement;
  if(!host||!host.parentElement)return null;
  const wrap=document.createElement('label');
  wrap.id='bookingDayWrap';
  wrap.className='bookingDayWrap';
  wrap.innerHTML='<span>Giorno prenotazione</span><select id="bookingDay" aria-label="Giorno prenotazione"></select>';
  host.parentElement.insertBefore(wrap,host);
  $('bookingDay').addEventListener('change',async()=>{
    if(editing)return;
    const target=$('bookingDay').value;
    if(!target)return;
    $('date').value=target;
    const previous=$('service')?.value||'';
    serviceOptions();
    if($('service')){
      const values=[...$('service').options].map(o=>o.value);
      if(values.includes(previous))$('service').value=previous;
      else{
        const dinner=values.find(v=>String(v).includes('cena'));
        if(dinner)$('service').value=dinner;
      }
    }
    if(typeof refreshBookingTimesForService==='function')refreshBookingTimesForService(true);
    selected=[];
    await loadAll();
    await syncNewBookingRoomToPrimaryArea();
    renderPicker();
  });
  return $('bookingDay');
}
function fillBookingDayField(date,locked=false){
  const el=ensureBookingDayField();if(!el)return;
  const dates=marinoNextBookingDates(31);
  const wanted=date||$('date')?.value||marinoToday();
  if(wanted&&!dates.includes(wanted))dates.unshift(wanted);
  el.innerHTML=dates.map(iso=>'<option value="'+iso+'">'+marinoDateLabel(iso)+'</option>').join('');
  el.value=wanted;
  el.disabled=locked;
  const wrap=$('bookingDayWrap');
  if(wrap)wrap.classList.toggle('bookingDayLocked',locked);
}

const _openBookingDayBase=openBooking;
openBooking=function(){
  marinoEditingServiceDate=null;
  marinoEditingServiceCode=null;
  const out=_openBookingDayBase();
  setTimeout(async()=>{fillBookingDayField($('date')?.value||marinoToday(),false);await syncNewBookingRoomToPrimaryArea();renderPicker()},0);
  return out;
};

const _editBookingDayBase=editBooking;
editBooking=function(id){
  const r=reservations.find(x=>x.id===id);
  const out=_editBookingDayBase(id);
  setTimeout(()=>fillBookingDayField(r?.service_date||$('date')?.value||marinoToday(),true),0);
  return out;
};

const _saveBookingDayBase=saveBooking;
saveBooking=async function(force){
  if(!editing){
    const chosen=$('bookingDay')?.value||$('date')?.value;
    if(!chosen)return alert('Seleziona il giorno della prenotazione.');
    if(chosen<marinoToday())return alert('Non puoi inserire una prenotazione in una data passata.');
    if($('date').value!==chosen){
      $('date').value=chosen;
      serviceOptions();
      if(typeof refreshBookingTimesForService==='function')refreshBookingTimesForService(true);
      selected=[];
      await loadAll();
      await syncNewBookingRoomToPrimaryArea();
      renderPicker();
      return alert('Ho aggiornato il giorno della prenotazione. Seleziona il tavolo per '+marinoDateLabel(chosen)+' e salva di nuovo.');
    }
  }
  return _saveBookingDayBase(force);
};
'''

s=s.replace(marker,patch+'\n'+marker,1)

css=r'''<style id="marino-booking-day-dropdown">
.bookingDayWrap{display:block;margin-bottom:10px;font-weight:800;color:#102c45}
.bookingDayWrap>span{display:block;margin-bottom:5px;font-size:12px;color:#526574}
#bookingDay{width:100%;min-height:42px;border:1px solid #cbd9e3;border-radius:10px;background:#fff;padding:8px 10px;font-size:14px;font-weight:800;color:#063f78}
.bookingDayLocked #bookingDay{background:#f3f5f7;color:#526574}
@media(max-width:720px){.bookingDayWrap{margin-bottom:8px}#bookingDay{min-height:40px;font-size:13px;padding:7px 9px}}
</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato per menu giorno prenotazione')
s=s.replace('</head>',css+'</head>',1)

if 'id="bookingDay"' not in s or 'fillBookingDayField' not in s or '_saveBookingDayBase' not in s or 'syncNewBookingRoomToPrimaryArea' not in s:
    raise SystemExit('Menu giorno prenotazione non inserito')

p.write_text(s)
