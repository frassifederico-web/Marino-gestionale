from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# PWA metadata
if 'rel="manifest"' not in s:
    s=s.replace('</head>','<link rel="manifest" href="./manifest.webmanifest"><link rel="icon" href="./icon.svg" type="image/svg+xml"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="apple-mobile-web-app-title" content="MARINO"></head>',1)

# Area backup dentro Accessi / Amministrazione.
if 'id="backupPanel"' not in s:
    marker='<div id="menuAdminSlot"></div>'
    if marker in s:
        s=s.replace(marker,marker+'<div id="backupPanel" class="card" style="display:none"></div>',1)
    else:
        s=s.replace('<div id="users"></div>','<div id="users"></div><div id="backupPanel" class="card" style="display:none"></div>',1)

new_users=r'''function renderUsers(users){
  $('inviteBox').style.display=profile?.role==='principal'?'block':'none';
  $('users').innerHTML=users.map(u=>{
    let backupCtl='';
    if(profile?.role==='principal'&&u.role!=='principal'){
      backupCtl='<button class="secondary" data-backup-user="'+esc(u.user_id)+'" data-backup-value="'+(!u.can_manage_backups)+'">Backup: '+(u.can_manage_backups?'ABILITATO':'NO')+'</button>';
    }
    return '<div class="row"><div><b>'+esc(u.display_name)+'</b><div class="muted">'+(u.role==='principal'?'Principale':'Collaboratore')+'</div></div><div class="actions"><span class="badge">'+(u.active?'ATTIVO':'DISATTIVO')+'</span>'+backupCtl+'</div></div>'
  }).join('');
  $('users').querySelectorAll('[data-backup-user]').forEach(b=>b.addEventListener('click',()=>updateBackupPermission(b.dataset.backupUser,b.dataset.backupValue==='true')));
  renderBackupPanel();
}
async function updateBackupPermission(userId,value){
  if(profile?.role!=='principal')return;
  let r=await db.from('profiles').update({can_manage_backups:value,updated_at:new Date().toISOString()}).eq('user_id',userId);
  if(r.error)return alert(r.error.message);
  await loadAll();
}
async function renderBackupPanel(){
  const el=$('backupPanel'); if(!el)return;
  const allowed=profile?.role==='principal'||profile?.can_manage_backups;
  if(!allowed){el.style.display='none';return}
  el.style.display='block';
  el.innerHTML='<h3>Backup prenotazioni</h3><div class="muted">Caricamento…</div>';
  let r=await db.from('backup_snapshots').select('id,created_at,reason,created_by').order('created_at',{ascending:false}).limit(30);
  if(r.error){el.innerHTML='<h3>Backup prenotazioni</h3><div class="warn">'+esc(r.error.message)+'</div>';return}
  const a=r.data||[], last=a[0];
  const rows=a.slice(0,10).map(x=>'<div class="row"><div><b>'+new Date(x.created_at).toLocaleString('it-IT')+'</b><div class="muted">'+esc(x.reason||'backup')+' · #'+x.id+'</div></div></div>').join('');
  el.innerHTML='<div class="actions" style="justify-content:space-between;align-items:center"><div><h3 style="margin:0">Backup prenotazioni</h3><div class="muted">'+(last?'Ultimo backup: '+new Date(last.created_at).toLocaleString('it-IT'):'Nessun backup disponibile')+'</div></div><div class="actions"><button class="primary" id="manualBackupBtn">Crea backup ora</button><button class="secondary" id="exportBackupBtn" '+(last?'':'disabled')+'>Esporta ultimo</button></div></div><div class="muted" style="margin:9px 0">Il sistema mantiene snapshot automatici; questa area serve per controllo e copie manuali autorizzate.</div>'+rows;
  $('manualBackupBtn')?.addEventListener('click',createManualBackup);
  $('exportBackupBtn')?.addEventListener('click',()=>last&&exportBackup(last.id));
}
async function createManualBackup(){
  let r=await db.rpc('create_backup_snapshot',{p_reason:'manual'});
  if(r.error)return alert(r.error.message);
  alert('Backup creato correttamente.');
  renderBackupPanel();
}
async function exportBackup(id){
  let r=await db.from('backup_snapshots').select('id,created_at,reason,payload').eq('id',id).single();
  if(r.error)return alert(r.error.message);
  const blob=new Blob([JSON.stringify(r.data,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='marino-backup-'+String(r.data.created_at).slice(0,10)+'-'+r.data.id+'.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function inviteAdmin'''

s,n=re.subn(r"function renderUsers\(users\)\{.*?\}\s*async function inviteAdmin",new_users,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'renderUsers non sostituito: {n}')

# Espone solo le funzioni necessarie agli handler/eventi esterni già usati nell'app.
if 'updateBackupPermission' not in s.split('Object.assign(window',1)[-1]:
    s=s.replace('Object.assign(window,{','Object.assign(window,{updateBackupPermission,renderBackupPanel,createManualBackup,exportBackup,',1)

# Registrazione service worker: la rete resta prioritaria per evitare dati/app obsoleti.
boot="""
if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(e=>console.warn('Service worker:',e)))}
"""
marker='(async()=>{let s=(await db.auth.getSession()).data.session;if(s)afterAuth(s)})();'
if marker in s and 'navigator.serviceWorker.register' not in s:
    s=s.replace(marker,boot+marker,1)

# In produzione il redirect Auth deve essere stabile e non dipendere da querystring/cache-buster.
prod_redirect="https://frassifederico-web.github.io/Marino-gestionale/"
s=s.replace("emailRedirectTo:location.href.split('#')[0]", f"emailRedirectTo:'{prod_redirect}'", 1)
if prod_redirect not in s:
    raise SystemExit('Redirect produzione MARINO non applicato')

css='''<style id="marino-app-ready">\n#backupPanel h3{color:var(--marino-blue,#063f78)}\n#backupPanel .row{align-items:flex-start}\n@media(max-width:720px){#backupPanel .actions{width:100%}#backupPanel button{min-height:44px}}\n</style>'''
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
