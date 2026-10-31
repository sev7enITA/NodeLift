"""Bounded real-weight gateway smoke test against an already configured local host."""
import http.client
import json
import re
import time
import urllib.request
from pathlib import Path

state=Path.home()/'.local/share/nodelift'
admin=re.findall(r'9868/#([^\s]+)',(state/'host-session.log').read_text())[-1]
key=(state/'client-api-key').read_text().strip()
base='http://127.0.0.1:9868'
def status():
    request=urllib.request.Request(base+'/admin/engine/status',headers={'Authorization':'Bearer '+admin})
    with urllib.request.urlopen(request,timeout=15) as response:return json.load(response)
assert not status()['busy'],'do not interrupt an existing run'
messages=[{'role':'system','content':'Rispondi in italiano, brevemente.'},
          {'role':'user','content':'Parla di città, energia e caffè. Aggiungi un simbolo 🌍.'}]
body={'model':'nodelift','messages':messages,'temperature':0,'max_tokens':64}
def request(value):
    data=json.dumps(value).encode()
    req=urllib.request.Request(base+'/v1/chat/completions',data=data,
                              headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    return urllib.request.urlopen(req,timeout=120)
with request(body) as response:normal=json.load(response)
with request({**body,'stream':True}) as response:
    text='';chunks=0;done=False
    for line in response:
        if not line.startswith(b'data: '):continue
        if line.strip()==b'data: [DONE]':done=True;break
        event=json.loads(line[6:]);assert 'error' not in event,event
        text+=event['choices'][0]['delta'].get('content','');chunks+=1
assert done and text==normal['choices'][0]['message']['content']
assert '\ufffd' not in text, 'unexpected UTF-8 replacement character'
connection=http.client.HTTPConnection('127.0.0.1',9868,timeout=120)
connection.request('POST','/v1/chat/completions',json.dumps({**body,'messages':[{'role':'user','content':'Write the full Python implementation of a balanced binary search tree with insertion, deletion, search and tests. Include all code, without abbreviations.'}],'max_tokens':512,'stream':True}),
                   {'Authorization':'Bearer '+key,'Content-Type':'application/json'})
response=connection.getresponse();assert response.status==200
# Close after the first committed content, while the remaining generation is active.
while True:
    line=response.readline()
    if line.startswith(b'data: '):
        chunk=json.loads(line[6:])
        if chunk['choices'][0]['delta'].get('content'):break
response.close();connection.close()
deadline=time.monotonic()+15
while status()['busy'] and time.monotonic()<deadline:time.sleep(.1)
last=status()['runs'][0]
assert last['status']=='cancelled',last['status']
report={'real_weights':True,'nonstream_and_stream_equal':True,'utf8_valid':True,
        'stream_chunks':chunks,'usage':normal['usage'],'disconnect_status':last['status'],
        'timestamp':time.time(),'scope':'configured small target; single-user greedy gateway'}
out=Path(__file__).resolve().parents[1]/'artifacts/gateway-live.json'
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
