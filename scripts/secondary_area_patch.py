from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

old="if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura'))){"
new="if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura')||t.includes('Area secondaria non attiva'))){"
if old not in s:
    raise SystemExit('Condizione forzatura salvataggio non trovata')
s=s.replace(old,new,1)

p.write_text(s)
