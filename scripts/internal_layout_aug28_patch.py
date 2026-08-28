from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Range frontend coerenti con la nuova sala interna.
new_range=r'''function selectionRange(){
  let ts=allTables.filter(t=>selected.includes(t.code));
  if(!ts.length)return null;
  let n=ts.length,groups=ts.map(t=>t.group_name||'');
  if(ts[0]?.area==='dehors'){
    if(n===1)return {mn:1,mx:4};
    if(n===2)return {mn:4,mx:6};
    return {mn:2*n+1,mx:2*n+2};
  }
  if(n===1)return {mn:Number(ts[0].single_min_covers||1),mx:Number(ts[0].single_max_covers||1)};
  let all=g=>groups.every(x=>x===g);
  if(all('bancone_sinistra'))return {mn:1,mx:n===2?4:7};
  if(all('bancone_56')&&n===2)return {mn:1,mx:4};
  if(all('quadrati')){
    let ranges={2:[4,6],3:[7,8],4:[9,10],5:[11,12]},r=ranges[n]||[1,12];
    return {mn:r[0],mx:r[1]};
  }
  if(all('panca_principale'))return n===1?{mn:1,mx:3}:{mn:2*n,mx:Math.min(14,2*n+2)};
  let pc=groups.filter(x=>x==='panca_principale').length,qc=groups.filter(x=>x==='quadrati').length;
  if(pc>0&&qc>0&&pc+qc===n){
    let pm=pc===1?3:Math.min(14,2*pc+2);
    return {mn:1,mx:Math.min(16,pm+2*qc)};
  }
  return {mn:Math.max(1,ts.reduce((a,t)=>a+Number(t.single_min_covers||1),0)),mx:ts.reduce((a,t)=>a+Number(t.single_max_covers||1),0)};
}
function selectionForceHint(){
  let party=Number($('party').value||0),codes=[...selected];
  if(codes.length===1&&(codes[0]==='B5'||codes[0]==='B6'))return '⚠ Bancone 5 e 6 sono normalmente uniti da 4: usare un solo tavolo richiede conferma di forzatura.';
  if(codes.length===1&&codes[0].startsWith('PQ')&&party===4)return '⚠ 4 persone su un solo Quadrato richiedono conferma di forzatura.';
  return '';
}
function renderSelectionSummary'''
s,n=re.subn(r"function selectionRange\(\)\{.*?\}\s*function renderSelectionSummary",new_range,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'selectionRange non sostituito: {n}')

# Messaggio di forzatura nel riepilogo selezione.
old="let ok=party>=r.mn&&party<=r.mx;el.innerHTML='<div class=\"selectionLine\"><b>'+selected.map(c=>{let t=allTables.find(x=>x.code===c);return esc(t?.label||c)}).join(' + ')+'</b><span class=\"badge\">'+r.mn+'–'+r.mx+' coperti</span></div><div class=\"'+(ok?'ok':'warn')+'\">'+(ok?'La selezione copre i '+party+' coperti richiesti.':'Controlla la selezione: '+party+' coperti richiesti, capacità indicativa '+r.mn+'–'+r.mx+'. Le regole definitive vengono sempre verificate al salvataggio.')+'</div>'"
new="let ok=party>=r.mn&&party<=r.mx,hint=selectionForceHint();el.innerHTML='<div class=\"selectionLine\"><b>'+selected.map(c=>{let t=allTables.find(x=>x.code===c);return esc(t?.label||c)}).join(' + ')+'</b><span class=\"badge\">'+r.mn+'–'+r.mx+' coperti</span></div><div class=\"'+(ok?'ok':'warn')+'\">'+(ok?'La selezione copre i '+party+' coperti richiesti.':'Controlla la selezione: '+party+' coperti richiesti, capacità indicativa '+r.mn+'–'+r.mx+'. Le regole definitive vengono sempre verificate al salvataggio.')+'</div>'+(hint?'<div class=\"warn layoutForceHint\">'+hint+'</div>':'')"
if old not in s: raise SystemExit('renderSelectionSummary atteso non trovato')
s=s.replace(old,new,1)

# Conferma dedicata quando si separa B5/B6.
old_q="let q=(t.toLowerCase().includes('non sono consecutivi')||t.toLowerCase().includes('associarli comunque'))?'I tavoli selezionati non sono consecutivi. Vuoi associarli comunque?':t+'\\n\\nVuoi comunque forzare questa prenotazione?';"
new_q="let q=t.toLowerCase().includes('bancone 5 e bancone 6')?'Bancone 5 e Bancone 6 normalmente formano un unico tavolo da 4. Vuoi separarli e usare il tavolo selezionato da massimo 2 persone?':(t.toLowerCase().includes('non sono consecutivi')||t.toLowerCase().includes('associarli comunque'))?'I tavoli selezionati non sono consecutivi. Vuoi associarli comunque?':t+'\\n\\nVuoi comunque forzare questa prenotazione?';"
if old_q not in s: raise SystemExit('Conferma forzatura non trovata')
s=s.replace(old_q,new_q,1)

css='''<style id="marino-layout-aug28">\n.layoutForceHint{margin-top:8px;font-weight:700}\n@media(max-width:720px){.layoutForceHint{font-size:13px}.table{min-height:84px;touch-action:manipulation}}\n</style>'''
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
