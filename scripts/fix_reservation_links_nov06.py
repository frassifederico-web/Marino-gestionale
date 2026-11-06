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
      .select('reservation_id,restaurant_tables(code,label)')
      .in('reservation_id',bookingIds.slice(i,i+100));
    if(result.error){
      console.error('MARINO table assignment loading failed',result.error);
      alert('Errore caricamento tavoli: assegnazioni non verificabili. Ricarica la pagina.');
      throw result.error;
    }
    links.push(...(result.data||[]));
  }
  if(links.some(x=>!x.restaurant_tables)){
    console.error('MARINO invalid table links',links.filter(x=>!x.restaurant_tables));
    alert('Alcuni collegamenti ai tavoli non sono leggibili.');
  }"""
s=s.replace(old2,new2,1)
p.write_text(s)
print('MARINO reservation links now loaded by reservation IDs for the selected service')
