from pathlib import Path
import sys, hashlib, io, json, secrets, ftplib
sys.path.insert(0, str(Path('artifacts/credits').resolve()))
from ftps_connection import connect, enter_site
out=Path('artifacts/iphone-tradeoffs-2026-11-02'); site=Path('site/NodeLift')
previous=json.loads(Path('artifacts/ios-draft-2026-11-02/deployment-manifest.json').read_text())
paths=['data/changelog.md','data/changelog.json','index.html']
manifest=json.loads(json.dumps(previous)); sha=lambda b:hashlib.sha256(b).hexdigest()
new={name:(site/name).read_bytes() for name in paths}
for name,b in new.items(): manifest['files'][name]={'bytes':len(b),'sha256':sha(b)}
ftp=connect(); enter_site(ftp)
def read(name):
 value=io.BytesIO(); ftp.retrbinary('RETR '+name,value.write); return value.getvalue()
old={}; staged={}; published=[]
try:
 for name in paths:
  if name in previous['files']:
   old[name]=read(name)
   assert sha(old[name])==previous['files'][name]['sha256'],'Concurrent remote change: '+name
   backup=out/'portal-backup'/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(old[name])
  else:
   existing={Path(item).name for item in ftp.nlst(str(Path(name).parent))}
   assert Path(name).name not in existing,'Untracked existing remote file: '+name
   old[name]=None
 for name in paths:
  p=Path(name);temp=str(p.parent/('.'+p.name+'.release-'+secrets.token_hex(5)+'.tmp'));staged[name]=temp
  ftp.storbinary('STOR '+temp,io.BytesIO(new[name]));assert sha(read(temp))==sha(new[name])
 for name in paths:
  if old[name] is not None: assert sha(read(name))==sha(old[name]),'Concurrent remote change: '+name
  else: assert Path(name).name not in {Path(item).name for item in ftp.nlst(str(Path(name).parent))}
  ftp.rename(staged[name],name);del staged[name];published.append(name);assert sha(read(name))==sha(new[name])
 (out/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 report={'secure_ftps':True,'published':published,'remote_readback_verified':True,'mobile_packages_changed':False}
 (out/'portal-ftps-readback.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
except Exception:
 for name in reversed(published):
  if sha(read(name))==sha(new[name]):
   if old[name] is None:ftp.delete(name)
   else:ftp.storbinary('STOR '+name,io.BytesIO(old[name]))
 raise
finally:
 for name in staged.values():
  try:ftp.delete(name)
  except ftplib.Error:pass
 ftp.quit()
