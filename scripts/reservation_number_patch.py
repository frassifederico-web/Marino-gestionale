from pathlib import Path

p=Path('_site/index.html')
s=p.read_text()

# Numero prenotazione coerente tra lista e mappa, calcolato nello stesso ordine
# cronologico usato dal riepilogo del servizio.
marker="function renderBookings(){"
helper="""function reservationDisplayNo(r){\n  const ordered=[...reservations].sort((a,b)=>String(a.arrival_time).localeCompare(String(b.arrival_time))||String(a.created_at||'').localeCompare(String(b.created_at||'')));\n  const i=ordered.findIndex(x=>x.id===r.id);\n  return i>=0?i+1:'—';\n}\n"""
if marker not in s:
    raise SystemExit('renderBookings non trovata per numerazione')
s=s.replace(marker,helper+marker,1)

# Disponibilità: mostra il primo orario in cui il tavolo torna prenotabile.
# Non richiede che dopo quell'orario resti un altro intero turno prima della chiusura:
# basta che l'orario sia entro la chiusura e non oltrepassi un turno successivo già inserito.
old="""    let limit=next?mins(next.arrival_time):serviceClose(r);\n    if(freeFrom+STD+TURN>limit)return '';\n"""
new="""    let limit=next?mins(next.arrival_time):serviceClose(r);\n    if(freeFrom>limit)return '';\n"""
if old not in s:
    raise SystemExit('regola disponibilità attesa non trovata')
s=s.replace(old,new,1)

# Lista prenotazioni: numero, orario di arrivo e coperti restano immediatamente visibili.
old="""<span class=\"bookingTime\">'+hhmm(r.arrival_time)+'</span> · '+esc(r.guest_name)+' · '+r.party_size+' coperti"""
new="""<span class=\"reservationNo\">#'+reservationDisplayNo(r)+'</span> · <span class=\"bookingTime\">'+hhmm(r.arrival_time)+'</span> · '+esc(r.guest_name)+' · '+r.party_size+' coperti"""
if old not in s:
    raise SystemExit('intestazione prenotazione non trovata')
s=s.replace(old,new,1)

# Mappa tavoli: ogni turno contiene numero prenotazione, orario e coperti,
# oltre al nome già previsto. Vale anche per le tessere divise in due turni.
old="""+'<div class=\"mapBookingTime\">'+esc(hhmm(r.arrival_time))+'</div><div class=\"mapBookingName\">'+esc(r.guest_name||'—')+'</div><div class=\"mapBookingCovers\">'+Number(r.party_size||0)+' cop.</div>';"""
new="""+'<div class=\"mapBookingNo\">#'+reservationDisplayNo(r)+'</div><div class=\"mapBookingTime\">'+esc(hhmm(r.arrival_time))+'</div><div class=\"mapBookingName\">'+esc(r.guest_name||'—')+'</div><div class=\"mapBookingCovers\">'+Number(r.party_size||0)+' cop.</div>';"""
if old not in s:
    raise SystemExit('contenuto tessera mappa non trovato')
s=s.replace(old,new,1)

css=r'''<style id="marino-reservation-number-ui">
.reservationNo{display:inline-block;background:#d8a52f;color:#17283a;border-radius:8px;padding:3px 7px;font-size:13px;font-weight:950;vertical-align:1px}
.mapBookingNo{font-size:9px;font-weight:950;color:#805d00;letter-spacing:.04em;line-height:1}
@media(max-width:720px){.reservationNo{font-size:12px;padding:3px 6px}.mapBookingNo{font-size:8.5px}}
</style>'''
if '</head>' not in s:
    raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
