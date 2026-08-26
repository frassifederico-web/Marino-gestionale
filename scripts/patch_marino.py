from pathlib import Path
import re

p = Path('_site/index.html')
s = p.read_text()

# Correzioni sintattiche residue del sorgente della Edge Function.
s=s.replace("onclick=\"editBooking(''+r.id+'')\"", "onclick=\"editBooking(\\''+r.id+'\\')\"")
s=s.replace("onclick=\"delBooking(''+r.id+'')\"", "onclick=\"delBooking(\\''+r.id+'\\')\"")
s=s.replace("onclick=\"toggleTable(''+t.code+'')\"", "onclick=\"toggleTable(\\''+t.code+'\\')\"")
s=s.replace("onclick=\"deleteMenu(''+x.id+'')\"", "onclick=\"deleteMenu(\\''+x.id+'\\')\"")
s=s.replace("onclick=\"toggleMenu(''+x.id+'','+(!x.active)+')\"", "onclick=\"toggleMenu(\\''+x.id+'\\','+(!x.active)+')\"")
s=s.replace("if(confirm(t+'\n\nVuoi comunque forzare questa prenotazione?'))", "if(confirm(t+'\\n\\nVuoi comunque forzare questa prenotazione?'))")

# Prenotazioni: sempre cronologiche e con catena di rimpiazzo precedente/successivo.
new_bookings = r'''function renderBookings(){
  let ordered=[...reservations].sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time)));
  function shared(a,b){let ac=tableCodesForRes(a.id),bc=tableCodesForRes(b.id);return ac.filter(x=>bc.includes(x))}
  $('bookingList').innerHTML=ordered.map((r,i)=>{
    let prev=null,next=null,prevTables=[],nextTables=[];
    for(let j=i-1;j>=0;j--){let sh=shared(r,ordered[j]);if(sh.length){prev=ordered[j];prevTables=sh;break}}
    for(let j=i+1;j<ordered.length;j++){let sh=shared(r,ordered[j]);if(sh.length){next=ordered[j];nextTables=sh;break}}
    let chain='';
    if(prev)chain+='<div class="turnLink prevTurn">← Da '+hhmm(prev.arrival_time)+' · '+esc(prev.guest_name)+' · '+esc(prevTables.join(', '))+'</div>';
    if(next){let gap=tm(next.arrival_time)-tm(r.arrival_time),forced=gap>=90&&gap<105;chain+='<div class="turnLink '+(forced?'forcedTurnLink':'nextTurn')+'">→ Prossimo '+hhmm(next.arrival_time)+' · '+esc(next.guest_name)+' · '+esc(nextTables.join(', '))+(forced?' · FORZATO 1h30':'')+'</div>'}
    return '<div class="row bookingRow"><div><b><span class="bookingTime">'+hhmm(r.arrival_time)+'</span> · '+esc(r.guest_name)+' · '+r.party_size+' coperti'+(r.forced?' · ⚠ FORZATA':'')+'</b><div class="muted">'+(r.expected_end_time?'Fine '+hhmm(r.expected_end_time)+' · ':'')+esc(tableLabelsForRes(r.id))+' · '+r.area+'</div>'+chain+'</div><div class="actions"><button class="secondary" onclick="editBooking(\\''+r.id+'\\')">Modifica</button><button class="danger" onclick="delBooking(\\''+r.id+'\\')">Elimina</button></div></div>'
  }).join('')||'<div class="muted">Nessuna prenotazione.</div>'
}'''
s,n=re.subn(r"function renderBookings\(\)\{.*?\}function renderMap", new_bookings+'\nfunction renderMap', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'renderBookings non sostituito: {n}')

# Tavoli: compatibilità temporale 1h45 / 1h30 + capacità visibile + priorità intelligente.
new_picker = r'''function hhmm(v){return v?String(v).slice(0,5):''}
function tm(v){let x=hhmm(v).split(':');return x.length===2?Number(x[0])*60+Number(x[1]):null}
function effEnd(start,end,minDur){let a=tm(start),e=tm(end);if(a==null)return null;return Math.max(e==null?a+minDur:e,a+minDur)}
function overlapsM(aStart,aEnd,bStart,bEnd){return aStart<bEnd&&bStart<aEnd}
function selectionRange(){
  let ts=allTables.filter(t=>selected.includes(t.code));
  if(!ts.length)return null;
  let mn=ts.reduce((a,t)=>a+Number(t.single_min_covers||1),0);
  let mx=ts.reduce((a,t)=>a+Number(t.single_max_covers||1),0);
  if(ts.length>1) mx=ts.reduce((a,t)=>a+Math.min(Number(t.single_max_covers||1),3),0);
  return {mn,mx};
}
function renderSelectionSummary(){
  let el=$('tableSelectionSummary');if(!el)return;
  let r=selectionRange(),party=Number($('party').value||0);
  if(!r){el.innerHTML='<b>'+party+' coperti richiesti</b><div class="muted">Scegli un tavolo tra quelli consigliati.</div>';return}
  let ok=party>=r.mn&&party<=r.mx;
  el.innerHTML='<div class="selectionLine"><b>'+selected.map(c=>{let t=allTables.find(x=>x.code===c);return esc(t?.label||c)}).join(' + ')+'</b><span class="badge">'+r.mn+'–'+r.mx+' coperti</span></div><div class="'+(ok?'ok':'warn')+'">'+(ok?'Configurazione adatta ai '+party+' coperti richiesti.':'Configurazione selezionata non ideale per '+party+' coperti: puoi modificare i tavoli o salvare con la forzatura prevista dalle regole.')+'</div>'
}
function renderPicker(){
  let room=$('room').value,start=tm($('arrival').value),endVal=$('endTime').value,stdEnd=effEnd($('arrival').value,endVal,105),forceEnd=effEnd($('arrival').value,endVal,90),party=Number($('party').value||0);
  let roomTables=allTables.filter(t=>t.area===room&&t.active).map(t=>{
    let rs=links.filter(x=>x.restaurant_tables?.code===t.code&&x.reservation_id!==editing).map(x=>reservations.find(r=>r.id===x.reservation_id)).filter(Boolean);
    let stdConflict=rs.filter(r=>overlapsM(start,stdEnd,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,105)));
    let forceConflict=rs.filter(r=>overlapsM(start,forceEnd,tm(r.arrival_time),effEnd(r.arrival_time,r.expected_end_time,90)));
    let forceOnly=stdConflict.length>0&&forceConflict.length===0,busy=forceConflict.length>0,used=rs.length>0;
    let mn=Number(t.single_min_covers||1),mx=Number(t.single_max_covers||1),fit=party>=mn&&party<=mx,oversize=party>0&&party<mn;
    let score=(busy?1000:0)+(forceOnly?200:0)+(fit?0:oversize?80+mn-party:40+Math.abs(party-mx));
    return {t,rs,busy,forceOnly,used,mn,mx,fit,oversize,score}
  }).sort((a,b)=>a.score-b.score||a.t.sort_order-b.t.sort_order);
  $('picker').innerHTML=roomTables.map(o=>{
    let {t,busy,forceOnly,used,mn,mx,fit,oversize}=o;
    let cl=busy?'busy':forceOnly?'forceTurn':used?'rebook':'free';if(selected.includes(t.code))cl+=' selected';if(fit&&!busy)cl+=' idealTable';
    let state=busy?'Occupato':forceOnly?'Forzabile 1h30':used?'Rimpiazzabile 1h45':'Libero';
    let advice=fit?'IDEALE':oversize?'Tavolo grande':'Disponibile';
    return '<button type="button" class="table '+cl+'" '+(busy?'disabled aria-disabled="true"':'data-table-code="'+esc(t.code)+'"')+'><b>'+esc(t.label)+'</b><div class="coverRange">'+mn+'–'+mx+' coperti</div><div class="tableAdvice">'+advice+'</div><div class="muted">'+state+'</div></button>'
  }).join('');
  $('picker').querySelectorAll('[data-table-code]').forEach(b=>b.addEventListener('click',()=>toggleTable(b.dataset.tableCode)));
  renderSelectionSummary();
}function toggleTable'''
s,n=re.subn(r"function hhmm\(v\).*?function toggleTable", new_picker, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'renderPicker non sostituito: {n}')

# Riepilogo tavoli nella modale.
needle='<div id="picker" class="tables"></div><div id="saveMsg"'
repl='<div id="tableSelectionSummary" class="selectionSummary"></div><div id="picker" class="tables"></div><div id="saveMsg"'
if needle not in s:
    raise SystemExit('Punto inserimento riepilogo tavoli non trovato')
s=s.replace(needle,repl,1)

# Aggiorna picker anche cambiando coperti.
expose_marker="$('arrival').addEventListener('change',renderPicker);\n$('endTime').addEventListener('change',renderPicker);"
if expose_marker in s:
    s=s.replace(expose_marker, expose_marker+"\n$('party').addEventListener('input',renderPicker);",1)

# Nuova prenotazione anche dalla pagina Prenotazioni.
old='<section id="bookings" class="page"><div class="card"><h3>Prenotazioni</h3><div id="bookingList"></div></div></section>'
new='<section id="bookings" class="page"><div class="card"><div class="actions bookingHead"><h3>Prenotazioni</h3><button class="primary" onclick="openBooking()">+ Nuova prenotazione</button></div><div class="muted" style="margin:5px 0 10px">Ordine cronologico · i rimpiazzi dello stesso tavolo sono indicati sotto ogni prenotazione.</div><div id="bookingList"></div></div></section>'
if old in s:s=s.replace(old,new,1)

# Menu consultazione / gestione principal.
s=s.replace('<section id="menu" class="page"><div class="card"><h3>Menu di servizio</h3>', '<section id="menu" class="page"><div class="card" id="menuEditor"><h3>Gestione menu</h3>',1)
s=s.replace('<section id="access" class="page"><div class="card"><h3>Accessi</h3>', '<section id="access" class="page"><div class="card"><h3>Accessi e amministrazione</h3><div id="menuAdminSlot"></div>',1)

new_render_menu="""function renderMenu(){let cats=['Antipasto','Primo','Secondo','Dolce','Altro'];let visible=menuItems.filter(x=>x.active);$('menuList').innerHTML='<div class=\"card menuIntro\"><h3>Menu disponibile</h3><div class=\"muted\">Consultazione rapida per telefonate, allergeni e intolleranze.</div></div>'+cats.map(c=>{let a=visible.filter(x=>x.category===c);if(!a.length)return'';return '<div class=\"card menuSection\"><h3>'+c+'</h3>'+a.map(x=>'<div class=\"row menuDish\"><div><div class=\"dishHead\"><b>'+esc(x.name)+'</b><span class=\"dishPrice\">'+(x.price==null?'—':Number(x.price).toFixed(2).replace('.',',')+' €')+'</span></div><div class=\"muted\">'+esc(x.description||'')+(x.allergens?.length?' · Allergeni: '+esc(x.allergens.join(', ')):'')+(x.dietary_tags?.length?' · '+esc(x.dietary_tags.join(', ')):'')+'</div></div></div>').join('')+'</div>'}).join('');renderMenuAdmin()}"""
s,n=re.subn(r"function renderMenu\(\)\{.*?\}\nasync function addMenu",new_render_menu+'\nasync function addMenu',s,count=1,flags=re.S)
if n != 1: raise SystemExit(f'renderMenu non sostituito: {n}')

admin_fn="""function renderMenuAdmin(){let editor=$('menuEditor'),slot=$('menuAdminSlot');if(!editor||!slot)return;if(profile?.role==='principal'){editor.style.display='block';if(editor.parentElement!==slot)slot.appendChild(editor);let old=$('menuAdminList');if(old)old.remove();let box=document.createElement('div');box.id='menuAdminList';box.className='card';box.innerHTML='<h3>Piatti caricati</h3>'+menuItems.map(x=>'<div class=\"row\"><div><b>'+esc(x.name)+'</b><div class=\"muted\">'+esc(x.category)+' · '+(x.active?'VISIBILE':'NASCOSTO')+'</div></div><div class=\"actions\"><button class=\"secondary\" data-menu-toggle=\"'+esc(x.id)+'\" data-active=\"'+(!x.active)+'\">'+(x.active?'Nascondi':'Mostra')+'</button><button class=\"danger\" data-menu-delete=\"'+esc(x.id)+'\">Elimina</button></div></div>').join('');slot.appendChild(box);box.querySelectorAll('[data-menu-toggle]').forEach(b=>b.addEventListener('click',()=>toggleMenu(b.dataset.menuToggle,b.dataset.active==='true')));box.querySelectorAll('[data-menu-delete]').forEach(b=>b.addEventListener('click',()=>deleteMenu(b.dataset.menuDelete)))}else{editor.style.display='none';let old=$('menuAdminList');if(old)old.remove()}}"""
s=s.replace('async function addMenu',admin_fn+'\nasync function addMenu',1)

# Supabase ESM per Safari.
old='<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script><script>'
new='''<script type="module">\nimport { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";\n'''
if old not in s: raise SystemExit('Tag Supabase atteso non trovato')
s=s.replace(old,new,1)
s=s.replace('const db=supabase.createClient(URL,KEY,','const db=createClient(URL,KEY,',1)

expose="""\nObject.assign(window,{login,signup,logout,showPage,dayChanged,loadAll,saveServiceSettings,openBooking,closeBooking,setMapRoom,editBooking,toggleTable,saveBooking,delBooking,addMenu,toggleMenu,deleteMenu,inviteAdmin});\n$('arrival').addEventListener('change',renderPicker);\n$('endTime').addEventListener('change',renderPicker);\n$('party').addEventListener('input',renderPicker);\n"""
marker='(async()=>{let s=(await db.auth.getSession()).data.session;if(s)afterAuth(s)})();'
if marker not in s: raise SystemExit('Marker bootstrap non trovato')
s=s.replace(marker,expose+marker,1)

# Forzatura temporale backend.
s=s.replace("if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata'))){", "if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura'))){",1)
s=s.replace("Seleziona liberamente i tavoli. Un tavolo rosso può essere riutilizzato se l'orario non si sovrappone; in tal caso diventa viola nella mappa della serata.", "Rimpiazzo standard: almeno 1h45 tra gli utilizzi dello stesso tavolo. Tra 1h30 e 1h44 il tavolo è forzabile con conferma. Sotto 1h30 resta incompatibile.",1)

# Diagnostica runtime.
diag="""\nwindow.addEventListener('error',e=>{const m=document.getElementById('authmsg');if(m){m.style.display='block';m.textContent='Errore app: '+(e.message||'errore JavaScript');}});\nwindow.addEventListener('unhandledrejection',e=>{const m=document.getElementById('authmsg');if(m){m.style.display='block';m.textContent='Errore app: '+(e.reason?.message||String(e.reason||'promessa non gestita'));}});\n"""
s=s.replace('const URL=',diag+'const URL=',1)

css=r'''
<style id="marino-final-ui">
:root{--shadow-card:0 5px 18px rgba(6,63,120,.07)}
.card{box-shadow:var(--shadow-card)}button{transition:transform .12s ease,box-shadow .12s ease}button:active{transform:scale(.98)}
.forceTurn{background:#fff0d4;border-color:#d79a45;color:#7c430e}.idealTable{box-shadow:inset 0 0 0 2px rgba(47,107,56,.25)}
.coverRange{font-size:13px;font-weight:900;margin-top:4px}.tableAdvice{display:inline-block;margin:5px 0 2px;padding:3px 6px;border-radius:999px;background:#fff8d9;font-size:9px;font-weight:900;letter-spacing:.04em}
.selectionSummary{margin:10px 0;padding:10px;border:1px solid var(--gold);border-radius:13px;background:#fff8d9}.selectionLine{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:7px}
.bookingHead{justify-content:space-between;align-items:center}.bookingHead h3{margin:0}.bookingTime{font-size:17px}.turnLink{margin-top:6px;padding:6px 8px;border-radius:9px;font-size:11px;font-weight:700}.prevTurn{background:#eef3f8}.nextTurn{background:var(--purplebg);color:var(--purple)}.forcedTurnLink{background:#fff0d4;color:#7c430e}
.dishHead{display:flex;justify-content:space-between;gap:12px;align-items:baseline}.dishPrice{white-space:nowrap;font-weight:900}.menuDish>div{width:100%}.menuSection>h3{border-bottom:1px solid var(--gold);padding-bottom:8px}
@media(max-width:720px){
 body{font-size:15px}.wrap{padding:9px 9px 94px}.card{padding:12px;border-radius:16px;margin-bottom:10px}header{min-height:68px;padding:9px 10px}header h1{font-size:20px}
 input,select,textarea{min-height:46px;padding:10px 11px;border-radius:12px;font-size:16px}.tabs{gap:4px;padding:6px 5px max(6px,env(safe-area-inset-bottom));box-shadow:0 -6px 20px rgba(6,63,120,.08)}.tabs button{border-radius:11px;font-size:10.5px;min-height:42px;padding:7px 4px}
 #bookingList .bookingRow{display:grid;grid-template-columns:1fr;gap:8px;padding:12px 2px}#bookingList .bookingRow .actions{justify-content:flex-end}.bookingHead .primary{padding:9px 11px;font-size:13px}
 #menuList .menuIntro{background:transparent;border:0;box-shadow:none;padding:4px 2px 8px}.menuIntro h3{font-size:22px;margin:0 0 4px}.menuSection{padding:13px}.menuDish{padding:11px 0;align-items:flex-start}
 .modal{padding:0;align-items:stretch;justify-content:stretch}.modal.open{display:block}.modal .box{width:100%;height:100dvh;max-height:none;border-radius:0;border-left:0;border-right:0;padding:12px 10px 110px;overflow-y:auto;-webkit-overflow-scrolling:touch}.modal .grid{grid-template-columns:1fr}.modal .full{grid-column:1}
 #picker{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:8px!important;max-height:none!important;overflow:visible!important}#picker .table{min-height:105px!important;padding:10px 7px!important}#picker .table b{display:block;font-size:15px}
 .modal .box>button.primary[onclick*="saveBooking"]{position:sticky;bottom:10px;z-index:6;width:100%;min-height:52px;font-size:17px;box-shadow:0 8px 20px rgba(6,63,120,.18)}
}
@media(max-width:390px){.grid4{grid-template-columns:1fr 1fr}.wrap{padding-left:7px;padding-right:7px}.dishHead{gap:7px}}
</style>
'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)

scripts=re.findall(r'<script type="module">(.*?)</script>',s,re.S)
if len(scripts)!=1: raise SystemExit(f'Atteso 1 script module, trovati {len(scripts)}')
Path('/tmp/marino-module.mjs').write_text(scripts[0])
