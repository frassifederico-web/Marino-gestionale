from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

marker='function _renderMapBase'
if marker not in s:
    raise SystemExit('Punto inserimento guardia data modifica non trovato')

patch=r'''
let marinoEditingServiceDate=null;
let marinoEditingServiceCode=null;
const _editBookingDateSafeBase=editBooking;
editBooking=function(id){
  const r=reservations.find(x=>x.id===id);
  if(r){
    marinoEditingServiceDate=r.service_date||null;
    marinoEditingServiceCode=r.service_code||null;
    if(marinoEditingServiceDate&&$('date')?.value!==marinoEditingServiceDate){
      $('date').value=marinoEditingServiceDate;
      serviceOptions();
    }
    if(marinoEditingServiceCode&&$('service')&&[...$('service').options].some(o=>o.value===marinoEditingServiceCode)){
      $('service').value=marinoEditingServiceCode;
    }
  }
  return _editBookingDateSafeBase(id);
};

const _saveBookingDateSafeBase=saveBooking;
saveBooking=async function(force){
  if(editing&&marinoEditingServiceDate){
    if($('date')?.value!==marinoEditingServiceDate){
      $('date').value=marinoEditingServiceDate;
      serviceOptions();
    }
    if(marinoEditingServiceCode&&$('service')&&[...$('service').options].some(o=>o.value===marinoEditingServiceCode)){
      $('service').value=marinoEditingServiceCode;
    }
  }
  return _saveBookingDateSafeBase(force);
};
'''

s=s.replace(marker,patch+'\n'+marker,1)

if 'marinoEditingServiceDate' not in s or '_saveBookingDateSafeBase' not in s:
    raise SystemExit('Guardia data modifica non inserita')

p.write_text(s)
