const CACHE='marino-shell-v2-20261010';
const SHELL=['./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));self.skipWaiting()});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(event.request.mode==='navigate'||event.request.destination==='document'){
    event.respondWith(fetch(new Request(event.request,{cache:'no-store'})).catch(()=>caches.match(event.request)));
    return;
  }
  if(url.origin!==self.location.origin)return;
  event.respondWith(fetch(event.request).then(response=>{
    if(response.ok&&SHELL.some(p=>url.pathname.endsWith(p.slice(1)))){const copy=response.clone();event.waitUntil(caches.open(CACHE).then(c=>c.put(event.request,copy)));}
    return response;
  }).catch(()=>caches.match(event.request)));
});
