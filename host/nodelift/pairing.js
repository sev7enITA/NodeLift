'use strict';
// Compact, offline transport of the existing pinned TLS invitation. No network lookup.
const NodeLiftPairing = (() => {
  function encode(ticket) {
    const url = new URL(ticket.url);
    if(![1,2].includes(ticket.protocol) || url.protocol!=='https:' || url.username || url.password || url.search || url.hash || !['','/'].includes(url.pathname))throw Error('Invalid invitation');
    const certificate=ticket.certificate.replace(/-----BEGIN CERTIFICATE-----|-----END CERTIFICATE-----|\s/g,'');
    if(!/^[A-Za-z0-9+/]+={0,2}$/.test(certificate) || !/^[A-Za-z0-9_-]{32}$/.test(ticket.invite) || !Number.isFinite(ticket.expires_at))throw Error('Invalid invitation');
    if(ticket.protocol===2){
      if(!/^nodelift-[0-9a-f]{32}\.local$/.test(ticket.tls_name))throw Error('Invalid invitation');
      return 'nodelift://pair/v2/'+url.hostname+':'+(url.port||443)+'/'+Math.floor(ticket.expires_at)+'/'+ticket.invite+'/'+ticket.tls_name+'/'+certificate.replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
    }
    return 'nodelift://pair/v1/'+url.hostname+':'+(url.port||443)+'/'+Math.floor(ticket.expires_at)+'/'+ticket.invite+'/'+certificate.replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function draw(canvas, value) {
    const qr=qrcodegen.QrCode.encodeText(value,qrcodegen.QrCode.Ecc.MEDIUM);
    const scale=4, border=4, size=(qr.size+border*2)*scale;
    canvas.width=size;canvas.height=size;
    const context=canvas.getContext('2d');
    context.fillStyle='#ffffff';context.fillRect(0,0,size,size);context.fillStyle='#000000';
    for(let y=0;y<qr.size;y++)for(let x=0;x<qr.size;x++)if(qr.getModule(x,y))context.fillRect((x+border)*scale,(y+border)*scale,scale,scale);
    canvas.hidden=false;
  }
  function mount({api,t,authenticated,error}) {
    const $=id=>document.getElementById(id);
    let ticket=null, epoch=0, timer=null, busy=false, polling=false, message='';
    function identity(value){const el=$('pairing-identity'),host=new URL(value.url).host;el.textContent=t('Computer: {0} · Identity: {1}',host,value.sha256.match(/.{1,4}/g).join(' '));el.setAttribute('aria-label',t('Computer: {0} · Identity: {1}',host,Array.from(value.sha256).join(' ')));}
    function erase(){ticket=null;clearInterval(timer);timer=null;$('ticket').value='';$('copy').disabled=true;$('pairing-qr').getContext('2d').clearRect(0,0,$('pairing-qr').width,$('pairing-qr').height);$('pairing-qr').hidden=true;$('pairing-identity').textContent='';$('pairing-identity').removeAttribute('aria-label');$('pairing-manual').open=false;}
    function clear(){epoch++;erase();$('pairing').hidden=true;}
    function say(key,...args){message=key;$('expiry').textContent=t(key,...args);}
    async function close(){const previous=ticket;clear();$('invite').focus();if(previous)try{await api('invite/revoke',{invite:previous.invite});}catch(_){error(Error('QR hidden. Revocation could not be confirmed; the invitation expires after 5 minutes.'));}}
    async function tick(){
      if(!ticket)return;
      const current=ticket, stamp=epoch, left=Math.ceil(current.expires_at-Date.now()/1000);
      if(left<=0){erase();say('Invitation expired. Choose New QR code.');return;}
      say('Expires in {0}:{1}',Math.floor(left/60),String(left%60).padStart(2,'0'));
      if(polling)return;polling=true;
      try{const state=await api('invite/status',{invite:current.invite});if(stamp===epoch && ticket===current && !state.pending){erase();say(state.network_changed?'The computer changed networks. Choose New QR code and scan again.':'Invitation used or closed. Check connected devices.');}}
      catch(_){/* Keep the bounded invitation usable during a transient status failure. */}
      finally{polling=false;}
    }
    async function open(){
      if(busy || !authenticated())return;busy=true;
      const previous=ticket;clear();const stamp=epoch;
      $('invite').disabled=true;$('renew-invite').disabled=true;
      try{
        if(previous)await api('invite/revoke',{invite:previous.invite});
        const next=await api('invite',{});
        if(stamp!==epoch || !authenticated()){try{await api('invite/revoke',{invite:next.invite});}catch(_){}return;}
        ticket=next;draw($('pairing-qr'),encode(next));$('ticket').value=JSON.stringify(next);$('copy').disabled=false;
        identity(next);
        $('pairing').hidden=false;await tick();if(ticket===next)timer=setInterval(tick,2000);
        $('pairing').scrollIntoView({behavior:'smooth',block:'center'});$('hide').focus({preventScroll:true});
      }catch(e){const failed=ticket;clear();if(failed)try{await api('invite/revoke',{invite:failed.invite});}catch(_){}error(e);}
      finally{busy=false;$('invite').disabled=!authenticated();$('renew-invite').disabled=false;}
    }
    async function copy(){if(!ticket || ticket.expires_at<=Date.now()/1000)return;try{await navigator.clipboard.writeText($('ticket').value);say('Copied');}catch(_){$('pairing-manual').open=true;$('ticket').select();error(Error('Select and copy the invitation manually.'));}}
    document.addEventListener('nodelift-languagechange',()=>{if(ticket){identity(ticket);tick();}else if(message)say(message);});
    window.addEventListener('pagehide',()=>{const previous=ticket;clear();if(previous)api('invite/revoke',{invite:previous.invite}).catch(()=>{});});
    return {open,close,clear,copy};
  }
  return {encode,draw,mount};
})();
