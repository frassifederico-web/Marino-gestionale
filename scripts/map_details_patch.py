from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

new_fn=r'''function enhanceMapBookings(){
  try{
    const map=document.getElementById('tableMap');
    if(!map)return;
    const cards=[...map.querySelectorAll('.table')];
    allTables.filter(t=>t.area===mapRoom&&t.active).forEach(t=>{
      const rs=links
        .filter(x=>x.restaurant_tables?.code===t.code)
        .map(x=>reservations.find(r=>r.id===x.reservation_id))
        .filter(r=>r&&r.status==='confermata')
        .sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time))||String(a.created_at||'').localeCompare(String(b.created_at||'')));
      const card=cards.find(el=>{
        const b=el.querySelector('b');
        const txt=(b?.textContent||el.textContent||'').trim();
        return txt===String(t.label||'').trim()||txt===String(t.code||'').trim();
      });
      if(!card)return;
      card.classList.toggle('mapBookingCard',rs.length>0);
      card.querySelectorAll('.mapBookingSlots').forEach(x=>x.remove());
      if(!rs.length)return;
      const slots=document.createElement('div');
      slots.className='mapBookingSlots '+(rs.length>1?'multiTurn':'singleTurn');
      rs.slice(0,2).forEach(r=>{
        const slot=document.createElement('div');
        slot.className='mapBookingSlot'+(r.arrived_at?' customerArrived':'');
        slot.innerHTML=(r.arrived_at?'<span class="arrivedCross" aria-label="Cliente arrivato">×</span>':'')+
          '<div class="mapBookingNo">Pren. #'+reservationDisplayNo(r)+'</div>'+
          '<div class="mapBookingMain"><span class="mapBookingTime">'+esc(hhmm(r.arrival_time))+'</span><span class="mapBookingName">'+esc(r.guest_name||'—')+'</span></div>'+
          '<div class="mapBookingCovers">'+Number(r.party_size||0)+' coperti</div>';
        slots.appendChild(slot);
      });
      card.appendChild(slots);
    });
  }catch(e){console.warn('Mappa prenotazioni:',e)}
}'''

s,n=re.subn(r"function enhanceMapBookings\(\)\{.*?\n\}
function renderMap\(\)",new_fn+'\nfunction renderMap()',s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'enhanceMapBookings non sostituita: {n}')

css=r'''<style id="marino-map-details-v2">
#tableMap .mapBookingCard{padding:10px 8px 0!important;min-height:132px!important;display:flex!important;flex-direction:column!important;overflow:hidden!important}
#tableMap .mapBookingCard>b{font-size:16px!important;text-align:center;margin-bottom:5px}
#tableMap .mapBookingCard>.muted{font-size:10px!important;text-align:center;margin-bottom:6px}
#tableMap .mapBookingSlots{position:static!important;inset:auto!important;margin:0 -8px 0!important;margin-top:auto!important;width:calc(100% + 16px)!important;display:grid!important;grid-template-columns:1fr!important;min-height:70px!important;background:rgba(255,255,255,.94)!important;border-top:2px solid rgba(6,63,120,.35)!important}
#tableMap .mapBookingSlots.multiTurn{grid-template-columns:1fr 1fr!important}
#tableMap .mapBookingSlot{position:relative!important;min-width:0!important;padding:7px 5px 6px!important;text-align:center!important;background:rgba(255,255,255,.9)!important;color:#102c45!important;overflow:hidden!important}
#tableMap .mapBookingSlots.multiTurn .mapBookingSlot+.mapBookingSlot{border-left:2px solid #063f78!important}
#tableMap .mapBookingNo{font-size:10px!important;font-weight:950!important;color:#805d00!important;line-height:1.1!important;margin-bottom:3px!important}
#tableMap .mapBookingMain{display:flex!important;align-items:center!important;justify-content:center!important;gap:5px!important;min-width:0!important}
#tableMap .mapBookingTime{font-size:13px!important;font-weight:950!important;color:#063f78!important;white-space:nowrap!important}
#tableMap .mapBookingName{font-size:12px!important;font-weight:900!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;min-width:0!important}
#tableMap .mapBookingCovers{font-size:11px!important;font-weight:850!important;color:#304b61!important;margin-top:3px!important}
#tableMap .mapBookingSlot.customerArrived{background:#dfe3e6!important}
#tableMap .arrivedCross{font-size:54px!important;color:rgba(70,78,85,.35)!important}
@media(max-width:720px){
 #tableMap{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:9px!important}
 #tableMap .mapBookingCard{min-height:136px!important;padding-left:6px!important;padding-right:6px!important}
 #tableMap .mapBookingSlots{margin-left:-6px!important;margin-right:-6px!important;width:calc(100% + 12px)!important}
 #tableMap .mapBookingSlot{padding:7px 3px 6px!important}
 #tableMap .mapBookingNo{font-size:9px!important}
 #tableMap .mapBookingTime{font-size:12px!important}
 #tableMap .mapBookingName{font-size:10.5px!important}
 #tableMap .mapBookingCovers{font-size:10px!important}
}
</style>'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
