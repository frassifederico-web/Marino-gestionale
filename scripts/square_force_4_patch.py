from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Mostra chiaramente sui singoli tavoli Quadrato la capienza standard e la forzatura a 4.
old="let state=busy?'Occupato':forceOnly?'Forzabile 1h30':used?'Rimpiazzabile 1h45':'Libero';let advice=fit?'IDEALE':oversize?'Tavolo grande':'Disponibile';return '<button type=\"button\" class=\"table '+cl+'\" '+(busy?'disabled aria-disabled=\"true\"':'data-table-code=\"'+esc(t.code)+'\"')+'><b>'+esc(t.label)+'</b><div class=\"coverRange\">'+mn+'–'+mx+' coperti</div><div class=\"tableAdvice\">'+advice+'</div><div class=\"muted\">'+state+'</div></button>'"
new="let state=busy?'Occupato':forceOnly?'Forzabile 1h30':used?'Rimpiazzabile 1h45':'Libero';let advice=fit?'IDEALE':oversize?'Tavolo grande':'Disponibile';let coverText=(t.group_name==='quadrati'&&Number(t.single_max_covers||0)===3)?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti');return '<button type=\"button\" class=\"table '+cl+'\" '+(busy?'disabled aria-disabled=\"true\"':'data-table-code=\"'+esc(t.code)+'\"')+'><b>'+esc(t.label)+'</b><div class=\"coverRange\">'+coverText+'</div><div class=\"tableAdvice\">'+advice+'</div><div class=\"muted\">'+state+'</div></button>'"
if old not in s:
    raise SystemExit('Blocco renderPicker per capienza tavoli non trovato')
s=s.replace(old,new,1)

# Conferma immediata e specifica per 4 coperti su un singolo Quadrato.
needle="async function saveBooking(force){$('saveMsg').style.display='none';"
repl="async function saveBooking(force){$('saveMsg').style.display='none';if(!force&&selected.length===1&&selected[0].startsWith('PQ')&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?'))return saveBooking(true);return;}"
if needle not in s:
    raise SystemExit('saveBooking non trovato')
s=s.replace(needle,repl,1)

# Riepilogo ancora più esplicito quando viene selezionato un Quadrato con 4 coperti.
s=s.replace("⚠ 4 persone su un solo Quadrato richiedono conferma di forzatura.","⚠ 4 coperti su un solo Quadrato: forzatura consentita con conferma.",1)

css='''<style id="marino-square-force-4">\n#picker .coverRange{line-height:1.2}\n@media(max-width:720px){#picker .coverRange{font-size:11px}}\n</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
