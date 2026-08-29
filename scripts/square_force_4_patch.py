from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Mostra chiaramente sui singoli tavoli Quadrato la capienza standard e la forzatura a 4.
# Patch volutamente minima: modifica soltanto il testo della capienza nel picker,
# così resta compatibile con gli altri aggiornamenti del layout.
old="<div class=\"coverRange\">'+mn+'–'+mx+' coperti</div>"
new="<div class=\"coverRange\">'+((t.group_name==='quadrati'&&Number(t.single_max_covers||0)===3)?'1–3 coperti (4 forzatura)':(mn+'–'+mx+' coperti'))+'</div>"
if old not in s:
    raise SystemExit('Testo capienza renderPicker non trovato')
s=s.replace(old,new,1)

# Conferma immediata e specifica per 4 coperti su un singolo Quadrato.
if 'Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?' not in s:
    s,n=re.subn(
        r"async\s+function\s+saveBooking\s*\(\s*force\s*\)\s*\{",
        "async function saveBooking(force){if(!force&&selected.length===1&&selected[0].startsWith('PQ')&&Number($('party').value)===4){if(confirm('Sei sicuro? Vuoi mettere 4 coperti su questa prenotazione?'))return saveBooking(true);return;}",
        s,count=1
    )
    if n!=1:
        raise SystemExit('saveBooking non trovato')

# Riepilogo ancora più esplicito quando viene selezionato un Quadrato con 4 coperti.
s=s.replace("⚠ 4 persone su un solo Quadrato richiedono conferma di forzatura.","⚠ 4 coperti su un solo Quadrato: forzatura consentita con conferma.",1)

css='''<style id="marino-square-force-4">\n#picker .coverRange{line-height:1.2}\n@media(max-width:720px){#picker .coverRange{font-size:11px}}\n</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
