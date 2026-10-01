from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Corregge la riallocazione massiva: nel Dehors esterno ogni tavolo vale 1-3 coperti,
# e le prenotazioni su più tavoli usano solo tavoli contigui lungo la stessa fila.
old="""    const party=Number(r.party_size||0),n=party<=4?1:party<=8?2:Math.ceil((party-2)/2),available=bulkAreaActive('dehors').map(t=>t.code).filter(c=>freeFor([c],r));
    if(available.length<n)return [];
    if(n===1)return available.slice(0,22).map(c=>[c]);
    let opts=[];for(let i=0;i<=available.length-n&&opts.length<40;i++)opts.push(available.slice(i,i+n));
    if(opts.length<40)opts.push(...bulkAreaComb(available,n,40-opts.length));
    return opts;"""
new="""    const party=Number(r.party_size||0),n=Math.max(1,Math.ceil(party/3));
    const outdoor=new Set(['D7','D8','D9','D10','D11','D12','D13','D14','D15','D16','D17','D18']);
    const rows=[['D7','D8','D9','D10','D11','D12'],['D13','D14','D15','D16','D17','D18']];
    const active=new Set(bulkAreaActive('dehors').map(t=>t.code).filter(c=>outdoor.has(c)));
    if(n===1)return [...active].filter(c=>freeFor([c],r)).map(c=>[c]);
    const opts=[];
    for(const row of rows){
      for(let i=0;i<=row.length-n;i++){
        const codes=row.slice(i,i+n);
        if(codes.every(c=>active.has(c))&&freeFor(codes,r))opts.push(codes);
      }
    }
    return opts;"""
if old not in s:
    raise SystemExit('Algoritmo riallocazione dehors precedente non trovato')
s=s.replace(old,new,1)

# Anche la stima di capienza deve rispettare 3 coperti per tavolo.
s=s.replace("if(area==='dehors')return n===1?[1,4,4]:n===2?[4,8,8]:[2*n+1,2*n+2,2*n+2];",
            "if(area==='dehors')return [n===1?1:3*(n-1)+1,3*n,3*n];",1)

for required in ["Math.ceil(party/3)","['D7','D8','D9','D10','D11','D12']","['D13','D14','D15','D16','D17','D18']","3*n,3*n"]:
    if required not in s: raise SystemExit('Verifica riallocazione dehors mancante: '+required)

p.write_text(s)
