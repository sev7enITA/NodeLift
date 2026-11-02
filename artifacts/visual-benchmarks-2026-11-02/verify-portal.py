from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, urllib.request
out=Path(__file__).resolve().parent
manifest=json.loads((out/'deployment-manifest.json').read_text())
paths=json.loads((out/'portal-ftps-readback.json').read_text())['published']
def verify(name):
 request=urllib.request.Request('https://www.fabriziodegni.com/NodeLift/'+name,headers={'Cache-Control':'no-cache'})
 with urllib.request.urlopen(request,timeout=40) as response:
  data=response.read(); status=response.status
 digest=hashlib.sha256(data).hexdigest()
 assert status==200 and digest==manifest['files'][name]['sha256'],name
 return {'path':name,'status':status,'sha256':digest,'bytes':len(data)}
with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(verify,paths))
(out/'portal-http-readback.json').write_text(json.dumps({'verified':results},indent=2)+'\n')
print(json.dumps({'https_verified_files':len(results),'all_hashes_match':True}))
