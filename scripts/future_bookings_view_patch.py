from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()

# Keep the original chronological booking renderer. It already uses the exact
# reservation number, notes, arrival/edit/cancel controls and compact styling.
# Do not append a second set of cards or replace its event handlers.
if 'id="marinoAllBookings"' in s:
    raise SystemExit('MARINO: unexpected duplicate list in built page')

# Extend the existing original renderer's window from 31 to 366 days.
# Empty days are omitted, so scrolling remains compact.
changed=False
for before,after in [
    ('d1.setDate(d1.getDate()+30)', 'd1.setDate(d1.getDate()+365)'),
    ('for(let i=0;i<=30;i++)', 'for(let i=0;i<=365;i++)'),
    ('host.innerHTML=days.map(iso=>{', 'host.innerHTML=days.filter(iso=>all.some(r=>r.service_date===iso)).map(iso=>{')
]:
    if before in s:
        s=s.replace(before,after,1)
        changed=True

if changed:
    p.write_text(s)
    print('MARINO: original compact chronological view kept, 366-day span, empty days hidden')
else:
    print('MARINO: original chronological view retained unchanged (no legacy date-window anchors)')
