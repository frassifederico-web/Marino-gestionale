from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()
old="db.from('reservation_tables').select('reservation_id,restaurant_tables(code,label)')"
if s.count(old)<1: raise SystemExit('Global links query not found')
s=s.replace(old,"Promise.resolve({data:[],error:null})",1)
old2="links=(l.data||[]).filter(x=>reservations.some(y=>y.id===x.reservation_id));"
if s.count(old2)!=1: raise SystemExit(f'Expected one link assignment, found {s.count(old2)}')
new2="""links=[];
  const bookingIds=reservations.map(x=>x.id);
  for(let i=0;i<bookingIds.length;i+=100){
    const result=await db.from('reservation_tables')
      .select('reservation_id,table_id')
      .in('reservation_id',bookingIds.slice(i,i+100));
    if(result.error){
      console.error('MARINO table assignment loading failed',result.error);
      alert('Errore caricamento tavoli: assegnazioni non verificabili. Ricarica la pagina.');
      throw result.error;
    }
    links.push(...(result.data||[]).map(x=>({reservation_id:x.reservation_id,restaurant_tables:allTables.find(t=>t.id===x.table_id)||null})));
  }
  if(links.some(x=>!x.restaurant_tables)){
    console.error('MARINO invalid table links',links.filter(x=>!x.restaurant_tables));
    alert('Alcuni collegamenti ai tavoli non sono leggibili.');
  }"""
s=s.replace(old2,new2,1)
# Sincronizza le etichette della lista con i collegamenti usati dalla piantina.
# Non modifica prenotazioni, tavoli o associazioni nel database.
import re
js=r'''
// MARINO booking-list table label sync, presentation only.
const marinoRenderBookingsOriginal = renderBookings;
renderBookings = function(...args) {
  const result = marinoRenderBookingsOriginal.apply(this,args);
  const applyLabels = () => {
    const root = document.getElementById('bookingList');
    if (!root) return;
    const rows = root.querySelectorAll('[data-edit-booking]');
    rows.forEach(button => {
      const id = button.getAttribute('data-edit-booking');
      const booking = reservations.find(r => String(r.id) === String(id));
      if (!booking) return;
      const tableNames = links.filter(link => String(link.reservation_id) === String(id))
        .map(link => link.restaurant_tables?.label || allTables.find(t => t.id === link.table_id)?.label)
        .filter(Boolean);
      if (!tableNames.length) return;
      const row = button.closest('.bookingRow, .row');
      if (!row) return;
      const details = row.querySelector('.muted');
      if (!details) return;
      const label = tableNames.join(' + ');
      const placeholder = /Tavol[oi] da assegnare/i;
      if (placeholder.test(details.textContent)) {
        const walker = document.createTreeWalker(details, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {
          if (placeholder.test(node.nodeValue)) {
            node.nodeValue = node.nodeValue.replace(placeholder, label);
            break;
          }
        }
      } else if (!details.textContent.includes(label)) {
        let badge = details.querySelector('.marino-assigned-table');
        if (!badge) {
          badge = document.createElement('span');
          badge.className = 'marino-assigned-table';
          details.append(' · ',badge);
        }
        badge.textContent = 'Tavolo ' + label;
      }
    });
  };
  if (result && typeof result.then === 'function') return result.then(value => {applyLabels();return value;});
  applyLabels();
  return result;
};
'''
module_close=re.search(r'(<script\\s+type="module"[^>]*>)(.*?)(</script>)',s,re.S|re.I)
if not module_close:
    raise SystemExit('MARINO: modulo JS non trovato per etichette prenotazioni')
s=s[:module_close.end(2)]+ '\n'+js+'\n'+s[module_close.end(2):]
if s.count('MARINO booking-list table label sync')!=1:
    raise SystemExit('MARINO: etichette tavoli non inserite una sola volta')
print('MARINO: lista prenotazioni sincronizzata con tavoli piantina')
p.write_text(s)
print('MARINO reservation links now loaded by reservation IDs for the selected service')
