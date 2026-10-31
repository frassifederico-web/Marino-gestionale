from pathlib import Path
p=Path('_site/index.html')
s=p.read_text()
if 'marino-ios-pdf-export-v1' in s: raise SystemExit(0)
js=r"""
// marino-ios-pdf-export-v1
async function marinoExportReservationsPdf(){
  try{
    if(!window.jspdf?.jsPDF){
      await new Promise((resolve,reject)=>{
        const script=document.createElement('script');script.src='./jspdf.umd.min.js';
        script.onload=resolve;script.onerror=()=>reject(new Error('Libreria PDF non disponibile. Apri il gestionale in Safari.'));
        document.head.appendChild(script);
      });
    }
    const date=marinoToday();
    const rq=await db.from('reservations').select('*').eq('service_date',date).eq('status','confermata').order('arrival_time');
    if(rq.error)throw rq.error;
    let rows=rq.data||[];
    const dinner=rows.filter(r=>String(r.service_code||'').includes('cena'));
    if(dinner.length)rows=dinner;
    const {jsPDF}=window.jspdf;
    const pdf=new jsPDF({orientation:'portrait',unit:'mm',format:'a4'});
    const clean=v=>String(v??'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^\x20-\x7E]/g,' ');
    const label=new Intl.DateTimeFormat('it-IT',{timeZone:'Europe/Rome',weekday:'long',day:'2-digit',month:'long',year:'numeric'}).format(new Date(date+'T12:00:00'));
    const widths=[30,22,54,18,70],x0=8;
    let y=8;
    function header(){
      pdf.setDrawColor(6,63,120);pdf.setLineWidth(.6);pdf.rect(8,8,194,25);
      pdf.setTextColor(6,63,120);pdf.setFont('helvetica','bold');pdf.setFontSize(21);pdf.text('MARINO',13,18);
      pdf.setFontSize(9);pdf.text('TRATTORIA DI PESCE',13,25);
      pdf.setFontSize(12);pdf.text(clean(label).slice(0,35),196,18,{align:'right'});
      pdf.setFontSize(9);pdf.text(rows.length+' prenotazioni  |  '+rows.reduce((a,r)=>a+Number(r.party_size||0),0)+' coperti',196,25,{align:'right'});
      y=37;pdf.setFillColor(6,63,120);pdf.rect(x0,y,194,9,'F');
      pdf.setTextColor(255,255,255);pdf.setFontSize(10);
      let x=x0;['TAVOLO','ORA','NOME','COP.','NOTE'].forEach((t,i)=>{pdf.text(t,x+2,y+6);x+=widths[i]});
      y+=9;pdf.setTextColor(16,44,69);
    }
    function row(values,blank=false){
      const h=9;
      if(y+h>280){pdf.addPage();header()}
      let x=x0;
      pdf.setDrawColor(165,181,193);pdf.setLineWidth(.2);
      if(blank){pdf.setFillColor(255,253,246);pdf.rect(x0,y,194,h,'F')}
      pdf.setFont('helvetica','normal');pdf.setFontSize(9);
      values.forEach((v,i)=>{
        pdf.rect(x,y,widths[i],h);
        const parts=pdf.splitTextToSize(clean(v),widths[i]-4);
        pdf.text((parts[0]||'').slice(0,85),x+2,y+5.8);
        x+=widths[i];
      });
      y+=h;
    }
    header();
    rows.forEach(r=>row(['',hhmm(r.arrival_time),r.guest_name||'',r.party_size||'',r.notes||'']));
    for(let i=0;i<8;i++)row(['','','','',''],true);
    const name='MARINO-prenotazioni-'+date+'.pdf';
    const blob=pdf.output('blob');
    const file=new File([blob],name,{type:'application/pdf'});
    if(navigator.share && (!navigator.canShare || navigator.canShare({files:[file]}))){
      try{await navigator.share({files:[file],title:'Lista prenotazioni MARINO'});return}
      catch(e){if(e.name==='AbortError')return}
    }
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),60000);
  }catch(e){console.error('MARINO PDF:',e);alert('Impossibile creare il PDF: '+(e.message||e))}
}
document.addEventListener('click',function(e){
  const btn=e.target.closest?.('button');
  if(!btn)return;
  const t=(btn.textContent||'').toLowerCase();
  if((t.includes('scarica lista prenotazioni')||t.includes('stampa lista')) && (document.getElementById('bookingList')||btn.id==='downloadReservationsPdfBtn')){
    e.preventDefault();e.stopImmediatePropagation();marinoExportReservationsPdf();
  }
},true);
"""
marker='function _renderMapBase'
if marker not in s: raise SystemExit('Marker modulo non trovato')
s=s.replace(marker,js+'\n'+marker,1)
p.write_text(s)
