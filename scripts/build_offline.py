"""Generate a versioned offline cache from the exact static assets."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent/'ai-exam'/'dist'
files=sorted(p for p in root.rglob('*') if p.is_file() and p.name!='sw.js')
version=hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()[:14]
assets=['./']+['./'+p.relative_to(root).as_posix() for p in files]
worker='''const CACHE='aicc-__VERSION__';
const ASSETS=__ASSETS__;
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('aicc-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=='GET'||url.origin!==self.location.origin)return;
 event.respondWith(fetch(event.request).then(response=>{
  if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}
  return response;
 }).catch(()=>caches.match(event.request).then(cached=>cached||(event.request.mode==='navigate'?caches.match('./index.html'):Response.error()))));
});
'''.replace('__VERSION__',version).replace('__ASSETS__',json.dumps(assets,separators=(',',':')))
(root/'sw.js').write_text(worker,encoding='utf-8')
print(f'Static site ready: {len(files)} assets, {sum(p.stat().st_size for p in files):,} bytes, offline cache {version}')
