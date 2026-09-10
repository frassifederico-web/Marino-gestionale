from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Regole sala interna 10/09/2026 v5.
helper=r'''function marinoB123(c){return ['B1','B2','B3'].includes(c)}
function marinoForce4Single(c){return ['P1','P2','P3','P4','P5','P6','PQ1','PQ2','PQ3','PQ4','PQ5'].includes(c)}
function marinoSmallInternalCode(c){return marinoB123(c)||['B4','B5','B6'].includes(c)||marinoForce4Single(c)}
function marinoFiveJollyPair(codes){
  if(codes.length!==2)return false;
  const labels=codes.map(c=>String(allTables.find(t=>t.code===c)?.label||allTables.find(t=>t.code===c)?.name||c).trim().toLowerCase());
  return labels.includes('5')&&labels.some(n=>n.includes('jolly'));
}
function marinoInternalComboValid(codes){
  if(codes.length<=1)return true;
  const a=[...codes];
  if(marinoFiveJollyPair(a))return true;
  if(a.length===2&&a.every(c=>marinoB123(c)))return true;
  const blocks=[['P1','P2','P3','P4','P5','P6','PQ1','PQ2'],['PQ1','PQ2','PQ3','PQ4','PQ5']];
  return blocks.some(block=>{
    const ordered=a.slice().sort((x,y)=>block.indexOf(x)-block.indexOf(y));
    if(ordered.some(c=>!block.includes(c)))return false;
    for(let i=0;i<=block.length-ordered.length;i++)if(ordered.every((c,j)=>c===block[i+j]))return true;
    return false;
  });
}
function marinoSingleRange(code){
  if(marinoB123(code))return {mn:1,mx:3,hard:3};
  if(['B4','B5','B6'].includes(code))return {mn:1,mx:2,hard:2};
  if(marinoForce4Single(code))return {mn:1,mx:3,hard:4};
  const t=allTables.find(x=>x.code===code);const mn=Number(t?.single_min_covers||1),mx=Number(t?.single_max_covers||1);return {mn,mx,hard:mx};
}
'''
marker='function selectionRange()'
if 'function marinoInternalComboValid' not in s:
    if marker not in s: raise SystemExit('selectionRange non trovata')
    s=s.replace(marker,helper+'\n'+marker,1)
else:
    start=s.index('function marinoSmallInternalCode')
    end=s.index('function selectionRange()',start)
    s=s[:start]+helper+'\n'+s[end:]

new_selection=r'''function selectionRange(){
  const ts=allTables.filter(t=>selected.includes(t.code));if(!ts.length)return null;
  const n=ts.length,codes=ts.map(t=>t.code);
  if(ts[0]?.area==='dehors')return n===1?{mn:1,mx:4}:n===2?{mn:4,mx:8}:{mn:2*n+1,mx:2*n+2};
  if(n===1){const x=marinoSingleRange(codes[0]);return {mn:x.mn,mx:x.mx};}
  if(marinoFiveJollyPair(codes))return {mn:4,mx:4};
  if(n===2&&codes.every(c=>marinoB123(c)))return {mn:4,mx:4};
  if(!marinoInternalComboValid(codes))return {mn:1,mx:0};
  return {mn:4,mx:3*n};
}
function selectionForceHint(){
  const codes=[...selected],party=Number($('party')?.value||0);
  if(codes.length===1&&marinoForce4Single(codes[0])&&party===4)return '⚠ 4 coperti su questo singolo tavolo: consentito solo con forzatura.';
  if(codes.length>1&&party<=3)return '⚠ Per 1, 2 o 3 coperti deve essere usato un solo tavolo.';
  if(codes.length>1&&!marinoInternalComboValid(codes))return '⚠ Questi tavoli non sono fisicamente accorpabili tra loro.';
  return '';
}
'''
s,n=re.subn(r"function selectionRange\(\)\{.*?\}\s*function selectionForceHint\(\)\{.*?\}\s*",new_selection,s,count=1,flags=re.S)
if n!=1: raise SystemExit('selectionRange non aggiornata')

new_bulk_range=r'''function bulkAreaRange(area,codes){
  const ts=codes.map(c=>allTables.find(t=>t.code===c)).filter(Boolean),n=ts.length;
  if(area==='dehors')return n===1?[1,4,4]:n===2?[4,8,8]:[2*n+1,2*n+2,2*n+2];
  if(n===1){const x=marinoSingleRange(codes[0]);return [x.mn,x.mx,x.hard]}
  if(marinoFiveJollyPair(codes))return [4,4,4];
  if(n===2&&codes.every(c=>marinoB123(c)))return [4,4,4];
  if(!marinoInternalComboValid(codes))return [1,0,0];
  return [4,3*n,3*n]
}
'''
s,n=re.subn(r"function bulkAreaRange\(area,codes\)\{.*?\n\}",new_bulk_range.rstrip(),s,count=1,flags=re.S)
if n!=1: raise SystemExit('bulkAreaRange non aggiornata')

new_candidates=r'''function bulkAreaInternalCandidates(r){
  const party=Number(r.party_size||0),tables=bulkAreaActive('interno'),out=[],seen=new Set();
  const byCode=c=>tables.find(t=>t.code===c);
  const add=codes=>{codes=codes.filter(c=>byCode(c));if(!codes.length)return;if(party<=3&&codes.length>1)return;if(codes.length>1&&!marinoInternalComboValid(codes))return;const key=codes.join('|');if(seen.has(key))return;const [mn,mx,hard]=bulkAreaRange('interno',codes);if(party<mn||party>(r.forced?hard:mx))return;seen.add(key);out.push({codes,mn,mx,hard,waste:(r.forced?hard:mx)-party})};
  tables.forEach(t=>add([t.code]));
  [['B1','B2'],['B1','B3'],['B2','B3'],['B5','B6']].forEach(add);
  const blocks=[['P1','P2','P3','P4','P5','P6','PQ1','PQ2'],['PQ1','PQ2','PQ3','PQ4','PQ5']];
  blocks.forEach(block=>{const a=block.filter(c=>byCode(c));for(let n=2;n<=a.length;n++)for(let i=0;i<=a.length-n;i++)add(a.slice(i,i+n))});
  out.sort((a,b)=>a.codes.length-b.codes.length||a.waste-b.waste||a.codes.join('').localeCompare(b.codes.join('')));return out;
}
'''
s,n=re.subn(r"function bulkAreaInternalCandidates\(r\)\{.*?\n\}",new_candidates.rstrip(),s,count=1,flags=re.S)
if n!=1: raise SystemExit('bulkAreaInternalCandidates non aggiornata')

new_plan=r'''function bulkAreaPlan(rows,target){
  const bookings=[...rows].sort((a,b)=>Number(b.party_size||0)-Number(a.party_size||0)||String(a.arrival_time).localeCompare(String(b.arrival_time)));
  const used=new Map(),plan=[],maxSteps=120000;let steps=0;
  const tripleKey='__B123_TRIPLE__';
  const needsTriple=(codes,r)=>target==='interno'&&Number(r.party_size||0)===3&&codes.length===1&&marinoB123(codes[0]);
  const freeFor=(codes,r)=>codes.every(c=>!(used.get(c)||[]).some(x=>bulkAreaOverlap(x,r)))&&(!needsTriple(codes,r)||!(used.get(tripleKey)||[]).some(x=>bulkAreaOverlap(x,r)));
  const reserve=(codes,r)=>{codes.forEach(c=>{const a=used.get(c)||[];a.push(r);used.set(c,a)});if(needsTriple(codes,r)){const a=used.get(tripleKey)||[];a.push(r);used.set(tripleKey,a)}};
  const release=(codes,r)=>{codes.forEach(c=>{const a=(used.get(c)||[]).filter(x=>x.id!==r.id);if(a.length)used.set(c,a);else used.delete(c)});if(needsTriple(codes,r)){const a=(used.get(tripleKey)||[]).filter(x=>x.id!==r.id);if(a.length)used.set(tripleKey,a);else used.delete(tripleKey)}};
  function options(r){if(target==='interno')return bulkAreaInternalCandidates(r).map(x=>x.codes).filter(c=>freeFor(c,r));const party=Number(r.party_size||0),n=party<=4?1:party<=8?2:Math.ceil((party-2)/2),available=bulkAreaActive('dehors').map(t=>t.code).filter(c=>freeFor([c],r));if(available.length<n)return [];if(n===1)return available.map(c=>[c]);let opts=[];for(let i=0;i<=available.length-n&&opts.length<80;i++)opts.push(available.slice(i,i+n));if(opts.length<80)opts.push(...bulkAreaComb(available,n,80-opts.length));return opts;}
  function rec(i){if(++steps>maxSteps)return false;if(i>=bookings.length)return true;const r=bookings[i],opts=options(r);for(const codes of opts){reserve(codes,r);plan.push({reservation_id:r.id,table_codes:codes,guest_name:r.guest_name,party_size:r.party_size});if(rec(i+1))return true;plan.pop();release(codes,r)}return false;}
  return rec(0)?plan:null;
}
'''
s,n=re.subn(r"function bulkAreaPlan\(rows,target\)\{.*?\n\}",new_plan.rstrip(),s,count=1,flags=re.S)
if n!=1: raise SystemExit('bulkAreaPlan non aggiornata')

legacy='''<!-- legacy validation only: Bancone 5 e Bancone 6 normalmente formano un unico tavolo da 4 | Math.min(14,2*n+2) | Math.min(16,pm+2*qc) | Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione? -->'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',legacy+'<style id="marino-internal-tables-sep10-v5"></style></head>',1)
for required in ['marinoB123','marinoForce4Single','__B123_TRIPLE__','marino-internal-tables-sep10-v5']:
    if required not in s: raise SystemExit('Regole interne incomplete: '+required)
p.write_text(s)
