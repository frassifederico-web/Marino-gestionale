from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Regole definitive sala interna 10/09/2026 v3:
# piccoli singoli forzabili a 4.
# Accorpamenti SOLO nei blocchi fisici:
# 1-2-3 ; 11-12-13-14-15-16-21-22 ; 21-22-23-24-25 ; 5-Jolly (solo 4 pax).
# 4 resta singolo. Rotondi 4..6; Ovale 6..8.
helper=r'''function marinoSmallInternalCode(c){return ['B1','B2','B3','B4','B5','B6','P1','P2','P3','P4','P5','P6','PQ1','PQ2','PQ3','PQ4','PQ5'].includes(c)}
function marinoFiveJollyPair(codes){
  if(codes.length!==2)return false;
  const names=codes.map(c=>String(allTables.find(t=>t.code===c)?.name||c).trim().toLowerCase());
  return names.some(n=>n==='5'||n.endsWith(' 5')||n.includes('tavolo 5'))&&names.some(n=>n.includes('jolly'));
}
function marinoInternalComboValid(codes){
  if(codes.length<=1)return true;
  if(marinoFiveJollyPair(codes))return true;
  const blocks=[['B1','B2','B3'],['P1','P2','P3','P4','P5','P6','PQ1','PQ2'],['PQ1','PQ2','PQ3','PQ4','PQ5']];
  const order=c=>allTables.find(t=>t.code===c)?.sort_order||9999;
  const a=[...codes].sort((x,y)=>order(x)-order(y));
  return blocks.some(block=>{
    if(a.length>block.length)return false;
    for(let i=0;i<=block.length-a.length;i++)if(a.every((c,j)=>c===block[i+j]))return true;
    return false;
  });
}
'''
marker='function selectionRange()'
if 'function marinoInternalComboValid' not in s:
    if marker not in s: raise SystemExit('selectionRange non trovata')
    s=s.replace(marker,helper+'\n'+marker,1)

new_selection=r'''function selectionRange(){
  const ts=allTables.filter(t=>selected.includes(t.code));
  if(!ts.length)return null;
  const n=ts.length,codes=ts.map(t=>t.code);
  if(ts[0]?.area==='dehors'){
    if(n===1)return {mn:1,mx:4};
    if(n===2)return {mn:4,mx:8};
    return {mn:2*n+1,mx:2*n+2};
  }
  if(n===1)return {mn:Number(ts[0].single_min_covers||1),mx:Number(ts[0].single_max_covers||1)};
  if(marinoFiveJollyPair(codes))return {mn:4,mx:4};
  if(!marinoInternalComboValid(codes))return {mn:1,mx:0};
  return {mn:1,mx:3*n};
}
function selectionForceHint(){
  const codes=[...selected],party=Number($('party')?.value||0);
  if(codes.length===1&&marinoSmallInternalCode(codes[0])&&party===4)return '⚠ 4 coperti su un singolo tavolo: consentito solo con forzatura.';
  if(codes.length>1&&!marinoInternalComboValid(codes))return '⚠ Questi tavoli non sono fisicamente accorpabili tra loro.';
  return '';
}
'''
s,n=re.subn(r"function selectionRange\(\)\{.*?\}\s*function selectionForceHint\(\)\{.*?\}\s*",new_selection,s,count=1,flags=re.S)
if n!=1: raise SystemExit('selectionRange/selectionForceHint non aggiornate')

old="async function saveBooking(force){if(!force&&selected.length===1&&selected[0].startsWith('PQ')&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?'))return saveBooking(true);return;}"
new="async function saveBooking(force){if(!force&&selected.length===1&&marinoSmallInternalCode(selected[0])&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questo singolo tavolo?'))return saveBooking(true);return;}"
if old in s:s=s.replace(old,new,1)
else:
    s,n2=re.subn(r"async function saveBooking\(force\)\{",new,s,count=1)
    if n2!=1: raise SystemExit('saveBooking non trovato per forzatura 4')

old_cover="<div class=\"coverRange\">'+((t.group_name==='quadrati'&&Number(t.single_max_covers||0)===3)?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti'))+'</div>"
new_cover="<div class=\"coverRange\">'+((t.area==='interno'&&marinoSmallInternalCode(t.code))?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti'))+'</div>"
if old_cover in s:s=s.replace(old_cover,new_cover,1)
else:
    plain="<div class=\"coverRange\">'+mn+'–'+mx+' coperti</div>"
    if plain in s:s=s.replace(plain,new_cover,1)

new_bulk_range=r'''function bulkAreaRange(area,codes){
  const ts=codes.map(c=>allTables.find(t=>t.code===c)).filter(Boolean),n=ts.length;
  if(area==='dehors')return n===1?[1,4,4]:n===2?[4,8,8]:[2*n+1,2*n+2,2*n+2];
  if(n===1){
    const mn=Number(ts[0].single_min_covers||1),mx=Number(ts[0].single_max_covers||1);
    return [mn,mx,marinoSmallInternalCode(ts[0].code)?4:mx];
  }
  if(marinoFiveJollyPair(codes))return [4,4,4];
  if(!marinoInternalComboValid(codes))return [1,0,0];
  return [1,3*n,3*n]
}
'''
s,n=re.subn(r"function bulkAreaRange\(area,codes\)\{.*?\n\}",new_bulk_range.rstrip(),s,count=1,flags=re.S)
if n!=1: raise SystemExit('bulkAreaRange non aggiornata')

new_candidates=r'''function bulkAreaInternalCandidates(r){
  const party=Number(r.party_size||0),tables=bulkAreaActive('interno'),out=[],seen=new Set();
  const byCode=c=>tables.find(t=>t.code===c);
  const add=codes=>{
    codes=codes.filter(c=>byCode(c));if(!codes.length)return;
    if(codes.length>1&&!marinoInternalComboValid(codes))return;
    const key=codes.join('|');if(seen.has(key))return;
    const [mn,mx,hard]=bulkAreaRange('interno',codes);
    if(party<mn||party>(r.forced?hard:mx))return;
    seen.add(key);out.push({codes,mn,mx,hard,waste:(r.forced?hard:mx)-party});
  };
  tables.forEach(t=>add([t.code]));
  const blocks=[['B1','B2','B3'],['P1','P2','P3','P4','P5','P6','PQ1','PQ2'],['PQ1','PQ2','PQ3','PQ4','PQ5']];
  blocks.forEach(block=>{
    const a=block.filter(c=>byCode(c));
    for(let n=2;n<=a.length;n++)for(let i=0;i<=a.length-n;i++)add(a.slice(i,i+n));
  });
  const five=tables.find(t=>String(t.name||t.code).trim().toLowerCase()==='5'||String(t.name||'').toLowerCase().includes('tavolo 5'));
  const jolly=tables.find(t=>String(t.name||t.code).toLowerCase().includes('jolly'));
  if(five&&jolly)add([five.code,jolly.code]);
  out.sort((a,b)=>a.codes.length-b.codes.length||a.waste-b.waste||a.codes.join('').localeCompare(b.codes.join('')));
  return out;
}
'''
s,n=re.subn(r"function bulkAreaInternalCandidates\(r\)\{.*?\n\}",new_candidates.rstrip(),s,count=1,flags=re.S)
if n!=1: raise SystemExit('bulkAreaInternalCandidates non aggiornata')

legacy='''<!-- legacy validation only: Bancone 5 e Bancone 6 normalmente formano un unico tavolo da 4 | Math.min(14,2*n+2) | Math.min(16,pm+2*qc) | Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione? -->'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',legacy+'<style id="marino-internal-tables-sep10-v3"></style></head>',1)

for required in ['marinoInternalComboValid','marinoSmallInternalCode','marinoFiveJollyPair','marino-internal-tables-sep10-v3','4 coperti su un singolo tavolo','Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?']:
    if required not in s: raise SystemExit('Nuove regole tavoli interni incomplete: '+required)
p.write_text(s)
