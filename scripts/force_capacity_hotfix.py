from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# 1) Dehors: 5 coperti devono usare esattamente 2 tavoli.
# Evita che i suggerimenti delle regole interne vengano applicati per errore al dehors.
new_hint=r'''function selectionForceHint(){
  const codes=[...selected],party=Number($('party')?.value||0),room=$('room')?.value||'';
  if(room==='dehors'){
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

# Guardia esplicita sul salvataggio: 5 persone nel dehors = 2 tavoli.
marker='function selectionForceHint()'
pos=s.find(marker)
if pos<0:
    raise SystemExit('marker selectionForceHint non trovato')
end=s.find('\n}',pos)
end=s.find('\n',end+2)
wrap=r'''
const _saveBookingDehorsFiveBase=saveBooking;
saveBooking=async function(force){
  const room=$('room')?.value||'',party=Number($('party')?.value||0);
  if(room==='dehors'&&party===5&&selected.length!==2){
    return alert('Per una prenotazione di 5 persone nel Dehors devi selezionare esattamente 2 tavoli.');
  }
  return _saveBookingDehorsFiveBase(force);
};
window.saveBooking=saveBooking;
'''
if '_saveBookingDehorsFiveBase' not in s:
    s=s[:end]+wrap+s[end:]

# 2) Foglio prenotazioni: blocco tavoli disponibili con 3 caselle per turno.
needle='<div class="footerSpace"></div><div class="foot">'
turns='<div class="availableTurns"><div class="availableTurnRow"><b>Tavoli disponibili primo turno</b><span></span><span></span><span></span></div><div class="availableTurnRow"><b>Tavoli disponibili secondo turno</b><span></span><span></span><span></span></div></div>'
if needle not in s:
    raise SystemExit('Punto inserimento tavoli disponibili non trovato')
s=s.replace(needle,turns+needle,1)

cssneedle='.footerSpace{flex:1;min-height:0}'
cssadd='.availableTurns{flex:0 0 auto;margin-top:1.5mm;border:1.5px solid #063f78;border-radius:2mm;padding:1.2mm 1.5mm}.availableTurnRow{display:grid;grid-template-columns:1fr 18mm 18mm 18mm;gap:2mm;align-items:center;min-height:6.5mm}.availableTurnRow+ .availableTurnRow{border-top:1px solid #9fb2c2}.availableTurnRow b{font-size:10px;color:#063f78}.availableTurnRow span{height:5mm;border:1.4px solid #063f78;border-radius:1mm;background:#fff}.footerSpace{flex:1;min-height:0}'
if cssneedle not in s:
    raise SystemExit('CSS footerSpace non trovato')
s=s.replace(cssneedle,cssadd,1)

s=s.replace('A4 verticale · tavolo da assegnare a mano · 8 righe libere finali','A4 verticale · tavolo da assegnare a mano · spazi tavoli disponibili per i due turni',1)

# Marker/verifiche finali.
if "party===5&&selected.length!==2" not in s:
    raise SystemExit('Regola 5 coperti dehors non inserita')
if 'Tavoli disponibili primo turno' not in s or 'Tavoli disponibili secondo turno' not in s:
    raise SystemExit('Riquadri tavoli disponibili non inseriti')
if 'grid-template-columns:1fr 18mm 18mm 18mm' not in s:
    raise SystemExit('Tre caselle per turno non inserite')

scripts=re.findall(r'<script type="module">(.*?)</script>',s,re.S)
if len(scripts)!=1:
    raise SystemExit(f'Atteso 1 script module, trovati {len(scripts)}')

p.write_text(s)
Path('/tmp/marino-module-hotfix.mjs').write_text(scripts[0])
