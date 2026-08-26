from pathlib import Path
import re

p = Path('_site/index.html')
s = p.read_text()

old = "if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura'))){"
new = "if(!force&&selected.length>0&&(t.toLowerCase().includes('massim')||t.toLowerCase().includes('capienza')||t.toLowerCase().includes('forzatura')||t.toLowerCase().includes('coperti consentit'))){"

if old not in s:
    raise SystemExit('Condizione di forzatura capienza non trovata')
s = s.replace(old, new, 1)

# Mantiene il controllo sintattico allineato con il modulo effettivamente pubblicato.
scripts = re.findall(r'<script type="module">(.*?)</script>', s, re.S)
if len(scripts) != 1:
    raise SystemExit(f'Atteso 1 script module, trovati {len(scripts)}')

p.write_text(s)
Path('/tmp/marino-module.mjs').write_text(scripts[0])
