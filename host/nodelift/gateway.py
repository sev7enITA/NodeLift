"""Restricted OpenAI-compatible local text gateway; unsupported features fail explicitly."""
import json
import time


def chat(handler, engine, body):
    allowed={'model','messages','temperature','n','top_p','max_tokens','max_completion_tokens',
             'stream','nodelift_mode','nodelift_node_id','nodelift_draft_k','nodelift_remote_timeout_ms',
             'presence_penalty','frequency_penalty'}
    unknown=set(body)-allowed
    if unknown:raise ValueError('parameters not qualified: '+', '.join(sorted(unknown)))
    body={key:value for key,value in body.items() if value is not None}
    for key,default in (('temperature',0),('n',1),('top_p',1),('presence_penalty',0),('frequency_penalty',0)):
        value=body.get(key,default)
        if type(value) not in (int,float) or value!=default:
            raise ValueError('greedy only: temperature=0, n=1, top_p=1, penalties=0')
    streaming=body.get('stream',False)
    if type(streaming) is not bool:raise ValueError('stream must be boolean')
    if 'max_tokens' in body and 'max_completion_tokens' in body:
        raise ValueError('use one output token limit')
    if body.get('model','nodelift')!='nodelift':raise ValueError('model must be nodelift (select target in dashboard)')
    messages=body.get('messages')
    if not isinstance(messages,list):raise ValueError('messages required')
    run_id=engine.start({'messages':messages,'mode':body.get('nodelift_mode','host'),
                         'node_id':body.get('nodelift_node_id'),'draft_k':body.get('nodelift_draft_k',4),
                         'remote_timeout_ms':body.get('nodelift_remote_timeout_ms',30000),
                         'max_tokens':body.get('max_completion_tokens',body.get('max_tokens',128))})['run_id']
    created=int(time.time());sent='';deadline=time.monotonic()+300;last_event=time.monotonic()
    def event(value):
        handler.wfile.write(('data: '+json.dumps(value,ensure_ascii=True)+'\n\n').encode());handler.wfile.flush()
    def chunk(delta,reason=None):
        return {'id':'chatcmpl-'+run_id,'object':'chat.completion.chunk','created':created,'model':'nodelift',
                'choices':[{'index':0,'delta':delta,'finish_reason':reason}]}
    try:
        if streaming:
            handler.send_response(200);handler.send_header('Content-Type','text/event-stream')
            handler.send_header('Cache-Control','no-store');handler.send_header('Connection','close')
            handler.end_headers();handler.close_connection=True;event(chunk({'role':'assistant','content':''}))
        while True:
            with engine.lock:
                run=next((r for r in engine.runs if r['id']==run_id),None)
                if run is None:raise RuntimeError('run state no longer available')
                status,text=run['status'],run['text']
            if streaming and text!=sent:
                if not text.startswith(sent):raise RuntimeError('non-monotonic output; refusing corrupted stream')
                event(chunk({'content':text[len(sent):]}));sent=text;last_event=time.monotonic()
            if status in ('completed','failed','cancelled'):break
            if time.monotonic()>deadline:engine.stop(run_id);raise RuntimeError('gateway deadline exceeded')
            if streaming and time.monotonic()-last_event>5:
                handler.wfile.write(b': working\n\n');handler.wfile.flush();last_event=time.monotonic()
            time.sleep(.02)
        if status!='completed':raise RuntimeError(run.get('error','inference cancelled'))
        if streaming:
            event(chunk({},run['finish_reason']));handler.wfile.write(b'data: [DONE]\n\n');handler.wfile.flush()
        else:
            return handler.send(200,{'id':'chatcmpl-'+run_id,'object':'chat.completion','created':created,'model':'nodelift',
                                    'choices':[{'index':0,'message':{'role':'assistant','content':text},'finish_reason':run['finish_reason']}],
                                    'usage':{'prompt_tokens':run['prompt_tokens'],'completion_tokens':len(run['tokens']),
                                             'total_tokens':run['prompt_tokens']+len(run['tokens'])}})
    except (BrokenPipeError,ConnectionResetError):
        engine.stop(run_id);handler.close_connection=True
    except Exception as error:
        engine.stop(run_id)
        if streaming:
            try:event({'error':{'message':str(error),'type':'nodelift_error'}});handler.wfile.write(b'data: [DONE]\n\n')
            except OSError:pass
        else:raise
