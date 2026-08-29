from pathlib import Path
import re

p=Path('_site/index.html')
s=p.read_text()

# Pulsante recupero password nella schermata di accesso.
old='<button class="primary" onclick="login()">Accedi</button><button class="secondary" onclick="signup()">Primo accesso</button>'
new='<button class="primary" onclick="login()">Accedi</button><button class="secondary" onclick="signup()">Primo accesso</button><button class="secondary" id="forgotPasswordBtn" onclick="requestPasswordReset()">Password dimenticata?</button>'
if old not in s:
    raise SystemExit('Pulsanti accesso non trovati')
s=s.replace(old,new,1)

# Area per impostare la nuova password quando si rientra dal link email di recupero.
marker='<div class="muted" style="margin-top:10px">Il primo accesso è consentito solo alle email autorizzate.</div>'
recovery='''<div id="passwordRecoveryBox" class="card" style="display:none;margin-top:12px"><b>Imposta nuova password</b><div class="muted" style="margin:6px 0">Inserisci una nuova password di almeno 8 caratteri.</div><label>Nuova password<input id="newPassword" type="password" autocomplete="new-password" minlength="8"></label><label>Ripeti password<input id="newPassword2" type="password" autocomplete="new-password" minlength="8"></label><button class="primary" style="margin-top:10px;width:100%" onclick="completePasswordRecovery()">Salva nuova password</button></div>'''
if marker not in s:
    raise SystemExit('Testo primo accesso non trovato')
s=s.replace(marker,marker+recovery,1)

# Variabile di stato prima delle funzioni di autenticazione.
needle="function msg(t){$('authmsg').style.display=t?'block':'none';$('authmsg').textContent=t||''}"
insert="""let passwordRecoveryMode=location.hash.includes('type=recovery')||location.search.includes('type=recovery');\nconst MARINO_PROD_URL='https://frassifederico-web.github.io/Marino-gestionale/';\n"""+needle
if needle not in s:
    raise SystemExit('Funzione msg non trovata')
s=s.replace(needle,insert,1)

# Funzioni reset via email e completamento cambio password.
login_marker='async function login(){'
funcs=r'''async function requestPasswordReset(){
  let e=$('email').value.trim().toLowerCase();
  if(!e||!e.includes('@'))return msg('Inserisci prima la tua email.');
  let r=await db.auth.resetPasswordForEmail(e,{redirectTo:MARINO_PROD_URL});
  if(r.error)return msg(r.error.message);
  msg('Email di recupero inviata. Apri il link ricevuto e scegli la nuova password.');
}
function showPasswordRecovery(){
  passwordRecoveryMode=true;
  $('auth').style.display='flex';
  $('passwordRecoveryBox').style.display='block';
  $('password')?.closest('label')?.setAttribute('style','display:none');
  $('displayName')?.closest('label')?.setAttribute('style','display:none');
  $('forgotPasswordBtn')?.setAttribute('style','display:none');
  msg('Scegli ora la nuova password.');
  setTimeout(()=>$('newPassword')?.focus(),50);
}
async function completePasswordRecovery(){
  let p1=$('newPassword').value,p2=$('newPassword2').value;
  if(p1.length<8)return msg('La nuova password deve avere almeno 8 caratteri.');
  if(p1!==p2)return msg('Le due password non coincidono.');
  let r=await db.auth.updateUser({password:p1});
  if(r.error)return msg(r.error.message);
  msg('Password aggiornata correttamente. Ora puoi accedere con la nuova password.');
  passwordRecoveryMode=false;
  await db.auth.signOut();
  setTimeout(()=>{location.href=MARINO_PROD_URL+'?password=updated'},700);
}
'''
if login_marker not in s:
    raise SystemExit('Funzione login non trovata')
s=s.replace(login_marker,funcs+login_marker,1)

# Durante il recupero non deve partire il normale bootstrap dell'app.
s=s.replace('async function afterAuth(s){if(!s)return;', 'async function afterAuth(s){if(!s||passwordRecoveryMode)return;',1)

# Espone le funzioni agli onclick del modulo ES.
if 'Object.assign(window,{' not in s:
    raise SystemExit('Object.assign window non trovato')
s=s.replace('Object.assign(window,{','Object.assign(window,{requestPasswordReset,showPasswordRecovery,completePasswordRecovery,',1)

# Gestisce esplicitamente l'evento Supabase PASSWORD_RECOVERY.
old_auth="db.auth.onAuthStateChange((e,s)=>{if(e==='SIGNED_IN'&&s&&!profile)setTimeout(()=>afterAuth(s),0)})"
new_auth="db.auth.onAuthStateChange((e,s)=>{if(e==='PASSWORD_RECOVERY'&&s){showPasswordRecovery();return}if(e==='SIGNED_IN'&&s&&!profile&&!passwordRecoveryMode)setTimeout(()=>afterAuth(s),0)})"
if old_auth not in s:
    raise SystemExit('Listener Auth non trovato')
s=s.replace(old_auth,new_auth,1)

# Se il link recovery contiene già type=recovery, mostra subito il form e lascia Supabase completare la sessione.
bootstrap="(async()=>{let s=(await db.auth.getSession()).data.session;if(s)afterAuth(s)})();"
new_boot="(async()=>{let s=(await db.auth.getSession()).data.session;if(passwordRecoveryMode){showPasswordRecovery();return}if(s)afterAuth(s)})();"
if bootstrap not in s:
    raise SystemExit('Bootstrap Auth non trovato')
s=s.replace(bootstrap,new_boot,1)

css='''<style id="marino-password-recovery">\n#forgotPasswordBtn{min-height:44px}\n#passwordRecoveryBox input{font-size:16px}\n@media(max-width:720px){#forgotPasswordBtn{width:100%}#passwordRecoveryBox{margin-top:10px}}\n</style>'''
s=s.replace('</head>',css+'</head>',1)

p.write_text(s)
