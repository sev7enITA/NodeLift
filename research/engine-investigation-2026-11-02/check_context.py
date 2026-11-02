import sys,json,hashlib,os
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/host')
from nodelift.native import Native
with Native() as e:
 e.call('load',path=sys.argv[2],n_ctx=256,threads=8,gpu_layers=0)
 pattern=e.call('tokenize',text='count the words',chat=False)['tokens'];prefix=(pattern*((255+len(pattern)-1)//len(pattern)))[:255]
 proposal=e.call('draft',prefix=prefix,count=1)['tokens'];r=e.call('verify',prefix=prefix,proposal=proposal,remaining=9)
 print('RESULT '+json.dumps({'native_sha256':hashlib.sha256(Path(os.environ['NODELIFT_LIBRARY']).read_bytes()).hexdigest(),'prefix_length':len(prefix),'context_size':256,'proposal_length':len(proposal),'accepted':r['accepted'],'returned_tokens':len(r['tokens'])}))
