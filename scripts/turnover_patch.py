from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

new_bookings=r'''function renderBookings(){
  let ordered=[...reservations].sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));
  const TURN=15,STD=105;
  const mins=v=>{let x=hhmm(v).split(':');return x.length===2?Number(x[0])*60+Number(x[1]):null};
  const fmt=m=>String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
  function shared(a,b){let ac=tableCodesForRes(a.id),bc=tableCodesForRes(b.id);return ac.filter(x=>bc.includes(x))}
  function availableFrom(r,code){
    let start=mins(r.arrival_time);
    let end=Math.max(mins(r.expected_end_time)||0,start+STD);
    return '<div class="availabilityWindow"><b>'+esc(code)+'</b> · Tavolo prenotabile dalle ore <b>'+fmt(end+TURN)+'</b></div>';
  }
  $('bookingList').innerHTML=ordered.map((r,i)=>{
    let prev=null,next=null,prevTables=[],nextTables=[];
    for(let j=i-1;j>=0;j--){let sh=shared(r,ordered[j]);if(sh.length){prev=ordered[j];prevTables=sh;break}}
    for(let j=i+1;j<ordered.length;j++){let sh=shared(r,ordered[j]);if(sh.length){next=ordered[j];nextTables=sh;break}}
    let chain='';
    if(prev)chain+='<div class="turnLink prevTurn">← Turno precedente '+hhmm(prev.arrival_time)+' · '+esc(prev.guest_name)+' · '+esc(prevTables.join(', '))+'</div>';
    if(next){let gap=tm(next.arrival_time)-tm(r.arrival_time),forced=gap>=105&&gap<120;chain+='<div class="turnLink '+(forced?'forcedTurnLink':'nextTurn')+'">→ Prossimo '+hhmm(next.arrival_time)+' · '+esc(next.guest_name)+' · '+esc(nextTables.join(', '))+(forced?' · 1h30 + 15 min riassetto':'')+'</div>'}
    let windows=tableCodesForRes(r.id).map(c=>availableFrom(r,c)).join('');
    return '<div class="row bookingRow"><div><b><span class="bookingTime">'+hhmm(r.arrival_time)+'</span> · '+esc(r.guest_name)+' · '+r.party_size+' coperti'+(r.forced?' · ⚠ FORZATA':'')+'</b><div class="muted">'+(r.expected_end_time?'Fine '+hhmm(r.expected_end_time)+' · ':'')+esc(tableLabelsForRes(r.id))+' · '+r.area+'</div>'+chain+windows+'</div><div class="actions"><button class="secondary" data-edit-booking="'+esc(r.id)+'">Modifica</button><button class="danger" data-delete-booking="'+esc(r.id)+'">Elimina</button></div></div>'
  }).join('')||'<div class="muted">Nessuna prenotazione.</div>';
  $('bookingList').querySelectorAll('[data-edit-booking]').forEach(b=>b.addEventListener('click',()=>editBooking(b.dataset.editBooking)));
  $('bookingList').querySelectorAll('[data-delete-booking]').forEach(b=>b.addEventListener('click',()=>delBooking(b.dataset.deleteBooking)));
}'''
s,n=re.subn(r"function renderBookings\(\)\{.*?\}\s*function renderMap",new_bookings+'\nfunction renderMap',s,count=1,flags=re.S)
if n!=1: raise SystemExit('renderBookings turnover non sostituito')

new_picker=r'''function renderPicker(){
  let room=$('room').value,start=tm($('arrival').value),endVal=$('endTime').value,party=Number($('party').value||0),TURN=15;
  let stdOccEnd=effEnd($('arrival').value,endVal,105),forceOccEnd=effEnd($('arrival').value,endVal,90);
  let stdBlockEnd=stdOccEnd==null?null:stdOccEnd+TURN,forceBlockEnd=forceOccEnd==null?null:forceOccEnd+TURN;
  let roomTables=allTables.filter(t=>t.area===room&&t.active).map(t=>{
    let rs=links.filter(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==editing).map(x=>reservations.find(r=>r.id===x.reservation_id)).filter(Boolean);
    let stdConflict=rs.filter(r=>overlapsM(start,stdBlockEnd,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,105)+TURN));
    let forceConflict=rs.filter(r=>overlapsM(start,forceBlockEnd,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,90)+TURN));
    let forceOnly=stdConflict.length>0&&forceConflict.length===0,busy=forceConflict.length>0,used=rs.length>0;
    let mn=Number(t.single_min_covers||1),mx=Number(t.single_max_covers||1),fit=party>=mn&&party<=mx,oversize=party>0&&party<mn;
    let score=(busy?1000:0)+(forceOnly?200:0)+(fit?0:oversize?80+(mn-party):40+Math.abs(party-mx));
    return {t,busy,forceOnly,used,mn,mx,fit,oversize,score}
  }).sort((a,b)=>a.score-b.score||a.t.sort_order-b.t.sort_order);
  $('picker').innerHTML=roomTables.map(o=>{
    let {t,busy,forceOnly,used,mn,mx,fit,oversize}=o;
    let cl=busy?'busy':forceOnly?'forceTurn':used?'rebook':'free';if(selected.includes(t.code))cl+=' selected';if(fit&&!busy)cl+=' idealTable';
    let state=busy?'Occupato / riassetto':forceOnly?'Forzabile: 1h30 + 15 min':used?'Rimpiazzabile: 1h45 + 15 min':'Libero';
    let advice=fit?'IDEALE':oversize?'Tavolo grande':'Disponibile';
    return '<button type="button" class="table '+cl+'" '+(busy?'disabled aria-disabled="true"':'data-table-code="'+esc(t.code)+'"')+'><b>'+esc(t.label)+'</b><div class="coverRange">'+mn+'–'+mx+' coperti</div><div class="tableAdvice">'+advice+'</div><div class="muted">'+state+'</div></button>'
  }).join('');
  $('picker').querySelectorAll('[data-table-code]').forEach(b=>b.addEventListener('click',()=>toggleTable(b.dataset.tableCode)));
  renderSelectionSummary();
}'''
s,n=re.subn(r"function renderPicker\(\)\{.*?\}\s*function toggleTable",new_picker+'\nfunction toggleTable',s,count=1,flags=re.S)
if n!=1: raise SystemExit('renderPicker turnover non sostituito')

css='''<style id="marino-turnover-ui">
.availabilityWindow{margin-top:7px;padding:7px 9px;border-radius:9px;background:#eef7f0;border-left:4px solid #2f8b4c;color:#244c31;font-size:11px;font-weight:700;line-height:1.35}
@media(max-width:720px){.availabilityWindow{font-size:11px;padding:8px 9px;margin-top:7px}}
</style>'''
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
