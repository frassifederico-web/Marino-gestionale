from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()
old="db.from('reservation_tables').select('reservation_id,restaurant_tables(code,label)')"
new="db.from('reservation_tables').select('reservation_id,table_id')"
if old not in s:
    raise SystemExit('Query tavoli della lista cronologica non trovata')
s=s.replace(old,new)
old_labels="const labelsFor=id=>allLinks.filter(x=>x.reservation_id===id).map(x=>x.restaurant_tables?.label||x.restaurant_tables?.code).filter(Boolean).join(' + ');"
new_labels="const labelsFor=id=>allLinks.filter(x=>String(x.reservation_id)===String(id)).map(x=>{const t=allTables.find(t=>String(t.id)===String(x.table_id));return t?.label||t?.code||''}).filter(Boolean).join(' + ');"
if old_labels not in s:
    raise SystemExit('Funzione labelsFor cronologica non trovata')
s=s.replace(old_labels,new_labels)
p.write_text(s)
print('MARINO: lista cronologica tavoli corretta')
