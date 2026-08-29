from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Evita bootstrap concorrenti e logout globali dovuti a errori transitori di rete/token.
marker="async function afterAuth(s){if(!s||passwordRecoveryMode)return;"
if marker not in s:
    raise SystemExit('afterAuth compatibile con recovery non trovata')

start=s.find('async function afterAuth(s){')
end=s.find('\nfunction serviceOptions()',start)
if start<0 or end<0:
    raise SystemExit('Confini afterAuth non trovati')

new_fn=r'''let authBootPromise=null;
const authSleep=ms=>new Promise(r=>setTimeout(r,ms));
async function loadAuthorizedProfile(userId){
  let lastError=null;
  for(let attempt=0;attempt<3;attempt++){
    let r=await db.from('profiles').select('*').eq('user_id',userId).maybeSingle();
    if(!r.error)return r;
    lastError=r.error;
    await authSleep(250*(attempt+1));
  }
  return {data:null,error:lastError||new Error('Profilo non disponibile')};
}
async function afterAuth(s){
  if(!s||passwordRecoveryMode)return;
  if(authBootPromise)return authBootPromise;
  authBootPromise=(async()=>{
    let r=await loadAuthorizedProfile(s.user.id);
    if(r.error){
      console.warn('Profilo temporaneamente non disponibile:',r.error);
      msg('Connessione temporaneamente non disponibile. La sessione resta attiva: riprova tra qualche secondo.');
      return;
    }
    if(!r.data||!r.data.active){
      await db.auth.signOut();
      profile=null;
      $('auth').style.display='flex';
      msg('Account non autorizzato o disattivato.');
      return;
    }
    profile=r.data;
    msg('');
    $('auth').style.display='none';
    $('dot').classList.add('on');
    $('online').textContent='online';
    $('who').textContent=' · '+profile.display_name+' · '+(profile.role==='principal'?'principale':'admin');
    await boot();
    subscribe();
  })();
  try{return await authBootPromise}finally{authBootPromise=null}
}'''

s=s[:start]+new_fn+s[end:]

old="db.auth.onAuthStateChange((e,s)=>{if(e==='PASSWORD_RECOVERY'&&s){showPasswordRecovery();return}if(e==='SIGNED_IN'&&s&&!profile&&!passwordRecoveryMode)setTimeout(()=>afterAuth(s),0)})"
new="db.auth.onAuthStateChange((e,s)=>{if(e==='PASSWORD_RECOVERY'&&s){showPasswordRecovery();return}if(e==='SIGNED_OUT'){profile=null;$('dot')?.classList.remove('on');if($('online'))$('online').textContent='non connesso';if($('auth')&&!passwordRecoveryMode)$('auth').style.display='flex';return}if((e==='SIGNED_IN'||e==='TOKEN_REFRESHED')&&s&&!profile&&!passwordRecoveryMode)setTimeout(()=>afterAuth(s),0)})"
if old not in s:
    raise SystemExit('Listener auth recovery non trovato')
s=s.replace(old,new,1)

# Mantiene le opzioni Supabase necessarie alla persistenza mobile.
for token in ['persistSession:true','autoRefreshToken:true','detectSessionInUrl:true']:
    if token not in s:
        raise SystemExit('Configurazione sessione mancante: '+token)

css='''<style id="marino-auth-stability">\n.authSessionNotice{font-size:12px}\n</style>'''
if '</head>' not in s: raise SystemExit('head non trovato')
s=s.replace('</head>',css+'</head>',1)
p.write_text(s)
