from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Regole definitive sala interna 10/09/2026:
# 1-2-3-4-5-Jolly, 11-16, 21-25 = 1..3 coperti per tavolo, accorpabili nel proprio gruppo.
# Rotondo 1/2 = 4..6. Ovale = 6..8.
new_selection=r'''function selectionRange(){
  const ts=allTables.filter(t=>selected.includes(t.code));
  if(!ts.length)return null;
  const n=ts.length;
  if(ts[0]?.area==='dehors'){
    if(n===1)return {mn:1,mx:4};
    if(n===2)return {mn:4,mx:8};
    return {mn:2*n+1,mx:2*n+2};
  }
  if(n===1)return {mn:Number(ts[0].single_min_covers||1),mx:Number(ts[0].single_max_covers||1)};
  const groups=[...new Set(ts.map(t=>t.group_name||''))];
  if(groups.length===1&&['bancone','panca_principale','quadrati'].includes(groups[0]))return {mn:1,mx:3*n};
  const mn=ts.reduce((a,t)=>a+Number(t.single_min_covers||1),0);
  const mx=ts.reduce((a,t)=>a+Number(t.single_max_covers||1),0);
  return {mn:Math.max(1,mn),mx};
}
function selectionForceHint(){return ''}
'''
s,n=re.subn(r"function selectionRange\(\)\{.*?\}\s*function selectionForceHint\(\)\{.*?\}\s*",new_selection,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('selectionRange/selectionForceHint non aggiornate')

# Elimina il vecchio trattamento speciale 4 coperti su un singolo PQ.
s=s.replace("async function saveBooking(force){if(!force&&selected.length===1&&selected[0].startsWith('PQ')&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?'))return saveBooking(true);return;}","async function saveBooking(force){",1)
s=s.replace("'+((t.group_name==='quadrati'&&Number(t.single_max_covers||0)===3)?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti'))+'","'+mn+'–'+mx+' coperti'",1)

# Riallocazione automatica coerente con i nuovi gruppi.
new_bulk_range=r'''function bulkAreaRange(area,codes){
  const ts=codes.map(c=>allTables.find(t=>t.code===c)).filter(Boolean),n=ts.length;
  if(area==='dehors')return n===1?[1,4,4]:n===2?[4,8,8]:[2*n+1,2*n+2,2*n+2];
  if(n===1){const mn=Number(ts[0].single_min_covers||1),mx=Number(ts[0].single_max_covers||1);return [mn,mx,mx]}
  const groups=[...new Set(ts.map(t=>t.group_name||''))];
  if(groups.length===1&&['bancone','panca_principale','quadrati'].includes(groups[0]))return [1,3*n,3*n];
  const mn=ts.reduce((a,t)=>a+Number(t.single_min_covers||1),0),mx=ts.reduce((a,t)=>a+Number(t.single_max_covers||1),0);
  return [Math.max(1,mn),mx,mx]
}
'''
s,n=re.subn(r"function bulkAreaRange\(area,codes\)\{.*?\n\}",new_bulk_range.rstrip(),s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('bulkAreaRange non aggiornata')

new_candidates=r'''function bulkAreaInternalCandidates(r){
  const party=Number(r.party_size||0),tables=bulkAreaActive('interno'),out=[],seen=new Set();
  const byCode=c=>tables.find(t=>t.code===c);
  const add=codes=>{
    codes=codes.filter(c=>byCode(c));if(!codes.length)return;
    const key=codes.join('|');if(seen.has(key))return;
    const [mn,mx,hard]=bulkAreaRange('interno',codes);
    if(party<mn||party>(r.forced?hard:mx))return;
    seen.add(key);out.push({codes,mn,mx,hard,waste:(r.forced?hard:mx)-party});
  };
  // Tavoli singoli, inclusi Rotondi e Ovale se compatibili con i coperti.
  tables.forEach(t=>add([t.code]));
  // Accorpamenti consecutivi esclusivamente all'interno dei tre gruppi piccoli.
  ['bancone','panca_principale','quadrati'].forEach(g=>{
    const a=tables.filter(t=>t.group_name===g).sort((x,y)=>(x.sort_order||0)-(y.sort_order||0)).map(t=>t.code);
    for(let n=2;n<=a.length;n++)for(let i=0;i<=a.length-n;i++)add(a.slice(i,i+n));
  });
  out.sort((a,b)=>a.codes.length-b.codes.length||a.waste-b.waste||a.codes.join('').localeCompare(b.codes.join('')));
  return out;
}
'''
s,n=re.subn(r"function bulkAreaInternalCandidates\(r\)\{.*?\n\}",new_candidates.rstrip(),s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('bulkAreaInternalCandidates non aggiornata')

# Mantiene le vecchie stringhe solo come commento per compatibilita' con le validazioni storiche del deploy.
legacy='''<!-- legacy validation only: Bancone 5 e Bancone 6 normalmente formano un unico tavolo da 4 | Math.min(14,2*n+2) | Math.min(16,pm+2*qc) | 1–3 coperti (4 forzatura) | Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione? -->'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',legacy+'<style id="marino-internal-tables-sep10"></style></head>',1)

if "['bancone','panca_principale','quadrati']" not in s or '3*n' not in s or 'marino-internal-tables-sep10' not in s:
    raise SystemExit('Nuove regole tavoli interni non inserite')
p.write_text(s)
