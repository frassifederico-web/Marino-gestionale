from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Dehors: regole operative specifiche.
# - 1/2/3/4 coperti: un solo tavolo di default.
# - 4 coperti su due tavoli: ammessi solo dopo conferma esplicita dell'operatore.
# - 5 coperti: esattamente due tavoli.
new_hint=r'''function selectionForceHint(){
  const codes=[...selected],party=Number($('party')?.value||0),room=$('room')?.value||'';
  if(room==='dehors'){
    if(party>=1&&party<=3&&codes.length!==1)return '⚠ Nel Dehors '+party+' coperti richiedono 1 tavolo.';
    if(party===4&&codes.length===2)return '⚠ 4 coperti su 2 tavoli: richiede conferma esplicita.';
    if(party===4&&codes.length!==1)return '⚠ Nel Dehors 4 coperti vanno normalmente su 1 tavolo.';
    if(party===5&&codes.length!==2)return '⚠ Nel Dehors 5 coperti richiedono esattamente 2 tavoli.';
    return '';
  }
  if(codes.length===1&&marinoForce4Single(codes[0])&&party===4)return '⚠ 4 coperti su questo singolo tavolo: consentito solo con forzatura.';
  if(codes.length>1&&party<=3)return '⚠ Per 1, 2 o 3 coperti deve essere usato un solo tavolo.';
  if(codes.length>1&&!marinoInternalComboValid(codes))return '⚠ Questi tavoli non sono fisicamente accorpabili tra loro.';
  return '';
}'''
s,n=re.subn(r"function selectionForceHint\(\)\{.*?\n\}",new_hint,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('selectionForceHint non trovata')

# Guardia al salvataggio. Per 4 coperti su due tavoli nel dehors non usa la
# forzatura di capienza DB: chiede solo una conferma operativa esplicita.
marker='function selectionForceHint()'
pos=s.find(marker)
if pos<0:
    raise SystemExit('marker selectionForceHint non trovato')
end=s.find('\n}',pos)
end=s.find('\n',end+2)
wrap=r'''
const _saveBookingDehorsRulesBase=saveBooking;
saveBooking=async function(force){
  const room=$('room')?.value||'',party=Number($('party')?.value||0),n=selected.length;
  if(room==='dehors'){
    if(party>=1&&party<=3&&n!==1){
      return alert('Nel Dehors una prenotazione da '+party+' coperti deve essere inserita su 1 tavolo.');
    }
    if(party===4){
      if(n===1)return _saveBookingDehorsRulesBase(force);
      if(n===2){
        if(!confirm('Vuoi inserire quattro coperti su due tavoli?'))return;
        return _saveBookingDehorsRulesBase(force);
      }
      return alert('Nel Dehors 4 coperti vanno normalmente su 1 tavolo. Se necessario puoi selezionare esattamente 2 tavoli e confermare la richiesta.');
    }
    if(party===5&&n!==2){
      return alert('Per una prenotazione di 5 persone nel Dehors devi selezionare esattamente 2 tavoli.');
    }
  }
  return _saveBookingDehorsRulesBase(force);
};
window.saveBooking=saveBooking;
'''
# Sostituisce il vecchio wrapper, se presente; altrimenti lo inserisce.
oldwrap=re.compile(r"\nconst _saveBookingDehorsFiveBase=saveBooking;.*?window\.saveBooking=saveBooking;\n",re.S)
if oldwrap.search(s):
    s=oldwrap.sub('\n'+wrap,s,count=1)
elif '_saveBookingDehorsRulesBase' not in s:
    s=s[:end]+wrap+s[end:]

# Foglio prenotazioni: blocco tavoli disponibili con 3 caselle per turno.
needle='<div class="footerSpace"></div><div class="foot">'
turns='<div class="availableTurns"><div class="availableTurnRow"><b>Tavoli disponibili primo turno</b><span></span><span></span><span></span></div><div class="availableTurnRow"><b>Tavoli disponibili secondo turno</b><span></span><span></span><span></span></div></div>'
if 'Tavoli disponibili primo turno' not in s:
    if needle not in s:
        raise SystemExit('Punto inserimento tavoli disponibili non trovato')
    s=s.replace(needle,turns+needle,1)

cssneedle='.footerSpace{flex:1;min-height:0}'
cssadd='.availableTurns{flex:0 0 auto;margin-top:1.5mm;border:1.5px solid #063f78;border-radius:2mm;padding:1.2mm 1.5mm}.availableTurnRow{display:grid;grid-template-columns:1fr 18mm 18mm 18mm;gap:2mm;align-items:center;min-height:6.5mm}.availableTurnRow+ .availableTurnRow{border-top:1px solid #9fb2c2}.availableTurnRow b{font-size:10px;color:#063f78}.availableTurnRow span{height:5mm;border:1.4px solid #063f78;border-radius:1mm;background:#fff}.footerSpace{flex:1;min-height:0}'
if 'grid-template-columns:1fr 18mm 18mm 18mm' not in s:
    if cssneedle not in s:
        raise SystemExit('CSS footerSpace non trovato')
    s=s.replace(cssneedle,cssadd,1)

s=s.replace('A4 verticale · tavolo da assegnare a mano · 8 righe libere finali','A4 verticale · tavolo da assegnare a mano · spazi tavoli disponibili per i due turni',1)

# Verifiche finali.
checks=[
    "party===4&&codes.length===2",
    "Vuoi inserire quattro coperti su due tavoli?",
    "party===5&&n!==2",
    'Tavoli disponibili primo turno',
    'Tavoli disponibili secondo turno',
    'grid-template-columns:1fr 18mm 18mm 18mm'
]
for x in checks:
    if x not in s: raise SystemExit('Verifica mancante: '+x)

scripts=re.findall(r'<script type="module">(.*?)</script>',s,re.S)
if len(scripts)!=1:
    raise SystemExit(f'Atteso 1 script module, trovati {len(scripts)}')

p.write_text(s)
Path('/tmp/marino-module-hotfix.mjs').write_text(scripts[0])
