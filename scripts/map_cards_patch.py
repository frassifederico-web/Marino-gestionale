from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Rinomina la renderMap originale e la avvolge senza alterarne la logica.
needle='function renderMap(){'
if needle not in s:
    raise SystemExit('renderMap non trovata')
s=s.replace(needle,'function _renderMapBase(){',1)

start=s.find('function _renderMapBase(){')
next_fn=re.search(r'\nfunction\s+([A-Za-z0-9_$]+)\s*\(',s[start+1:])
if not next_fn:
    raise SystemExit('funzione successiva a renderMap non trovata')
pos=start+1+next_fn.start()

wrapper=r'''
function enhanceMapBookings(){
  try{
    const active=document.querySelector('.page.active')||document;
    const candidates=[...active.querySelectorAll('.table,button')].filter(el=>!el.closest('#picker')&&!el.closest('.modal'));
    allTables.forEach(t=>{
      const rs=links
        .filter(x=>x.restaurant_tables?.code===t.code)
        .map(x=>reservations.find(r=>r.id===x.reservation_id))
        .filter(Boolean)
        .sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));
      if(!rs.length)return;
      let card=candidates.find(el=>{
        const txt=(el.textContent||'').trim();
        return txt===String(t.label||'').trim()||txt===String(t.code||'').trim()||txt.startsWith(String(t.label||'').trim()+' ')||txt.startsWith(String(t.code||'').trim()+' ');
      });
      if(!card)return;
      card.classList.add('mapBookingCard');
      card.querySelectorAll('.mapBookingSlots').forEach(x=>x.remove());
      const slots=document.createElement('div');
      slots.className='mapBookingSlots '+(rs.length>1?'multiTurn':'singleTurn');
      rs.slice(0,2).forEach(r=>{
        const slot=document.createElement('div');
        slot.className='mapBookingSlot';
        slot.innerHTML='<div class="mapBookingTime">'+esc(hhmm(r.arrival_time))+'</div><div class="mapBookingName">'+esc(r.guest_name||'—')+'</div><div class="mapBookingCovers">'+Number(r.party_size||0)+' cop.</div>';
        slots.appendChild(slot);
      });
      card.appendChild(slots);
    });
  }catch(e){console.warn('Mappa prenotazioni:',e)}
}
function renderMap(){
  _renderMapBase();
  requestAnimationFrame(enhanceMapBookings);
}
'''
s=s[:pos]+wrapper+s[pos:]

css=r'''
<style id="marino-map-bookings">
.mapBookingCard{position:relative!important;overflow:hidden!important;min-height:92px!important;padding-bottom:56px!important}
.mapBookingSlots{position:absolute;left:0;right:0;bottom:0;display:grid;grid-template-columns:1fr;background:rgba(255,255,255,.88);border-top:1px solid rgba(6,63,120,.25);min-height:52px}
.mapBookingSlots.multiTurn{grid-template-columns:1fr 1fr}
.mapBookingSlot{min-width:0;padding:5px 5px 4px;text-align:center;line-height:1.08;color:#102c45;background:rgba(255,255,255,.9)}
.mapBookingSlots.multiTurn .mapBookingSlot+ .mapBookingSlot{border-left:2px solid #063f78}
.mapBookingTime{font-size:12px;font-weight:950;color:#063f78}
.mapBookingName{font-size:10px;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
.mapBookingCovers{font-size:9px;font-weight:800;margin-top:2px;color:#42586a}
@media(max-width:720px){.mapBookingCard{min-height:96px!important;padding-bottom:58px!important}.mapBookingTime{font-size:11px}.mapBookingName{font-size:9.5px}.mapBookingCovers{font-size:9px}.mapBookingSlot{padding-left:3px;padding-right:3px}}
</style>
'''
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
