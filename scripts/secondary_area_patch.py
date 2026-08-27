from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

# Il backend restituisce gia un messaggio contenente "forzatura" quando
# l'area secondaria non e attiva, quindi il controllo generale del frontend
# lo intercetta senza dover modificare qui la condizione di saveBooking.
needle="if(!force&&(t.includes('massima')||t.includes('Capienza servizio superata')||t.toLowerCase().includes('forzatura'))){"
if needle not in s:
    raise SystemExit('Condizione forzatura salvataggio non trovata')

p.write_text(s)
