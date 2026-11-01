import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.request import Request

from nodelift.model_library import ModelLibrary, HubRedirect, check_gguf

GGUF=struct.pack('<4sIQQ',b'GGUF',3,1,1)+b'unit test data (not an executable model)'

class Response(io.BytesIO):
    status=200

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.library=ModelLibrary(self.root)
    def tearDown(self):self.tmp.cleanup()
    def wait(self):
        deadline=time.monotonic()+3
        while self.library.status()['transfer']['status'] in ('transferring','verifying'):
            if time.monotonic()>deadline:self.fail('transfer worker did not finish')
            time.sleep(.01)
        return self.library.status()['transfer']
    def start(self):return self.library.upload_start({'name':'test.gguf','bytes':len(GGUF)})['id']
    def test_local_import_without_copy_survives_restart(self):
        p=self.root/'test.gguf';p.write_bytes(GGUF)
        self.library.import_path(str(p));self.assertEqual(ModelLibrary(self.root).paths(),[p.resolve()])
        self.assertEqual(list(self.library.folder.glob('*.gguf')),[])
        self.assertEqual(self.library.registry_path.stat().st_mode&0o777,0o600)
    def test_reject_relative_invalid_headers_shards_and_code(self):
        with self.assertRaises(ValueError):self.library.import_path('relative.gguf')
        for name,data in [('x.gguf',b'bad'),('x.bin',GGUF),('x-00001-of-00002.gguf',GGUF),('x.gguf',struct.pack('<4sIQQ',b'GGUF',1,1,1))]:
            p=self.root/name;p.write_bytes(data)
            with self.subTest(name=name),self.assertRaises(ValueError):check_gguf(p)
    def test_upload_checks_offset_overrun_and_never_exposes_partial(self):
        identity=self.start()
        with self.assertRaises(ValueError):self.library.upload_chunk(identity,1,GGUF)
        with self.assertRaises(ValueError):self.library.upload_chunk(identity,0,GGUF+b'x')
        self.library.upload_chunk(identity,0,GGUF[:24]);self.assertEqual(self.library.paths(),[])
        with self.assertRaises(ValueError):self.library.finish(identity)
        self.library.upload_chunk(identity,24,GGUF[24:]);self.library.finish(identity)
        row=self.wait();self.assertEqual(row['status'],'completed');self.assertEqual(row['sha256'],hashlib.sha256(GGUF).hexdigest())
        self.assertEqual(Path(row['path']).read_bytes(),GGUF)
    def test_bad_upload_removed_and_path_traversal_rejected(self):
        with self.assertRaises(ValueError):self.library.upload_start({'name':'../bad.gguf','bytes':24})
        identity=self.start();self.library.upload_chunk(identity,0,b'x'*len(GGUF));self.library.finish(identity)
        self.assertEqual(self.wait()['status'],'failed');self.assertEqual(self.library.paths(),[])
        self.assertEqual(list(self.library.folder.iterdir()),[])
    def test_cancel_and_stale_session_cannot_affect_new_upload(self):
        old=self.start();self.library.cancel(old);new=self.start()
        with self.assertRaises(ValueError):self.library.cancel(old)
        with self.assertRaises(ValueError):self.library.upload_chunk(old,0,GGUF)
        self.library.upload_chunk(new,0,GGUF);self.library.cancel(new)
        self.assertEqual(self.library.status()['transfer']['status'],'cancelled')
    def test_restart_discards_only_owned_partial_files(self):
        self.start();other=self.library.folder/'user.part';other.write_bytes(b'keep')
        partial=self.library._part();ModelLibrary(self.root);self.assertTrue(partial.exists())
        os.utime(partial,(time.time()-90000,time.time()-90000))
        ModelLibrary(self.root);self.assertTrue(other.exists());self.assertFalse(list(self.library.folder.glob('.nodelift-*.part')))
    def test_hf_pins_metadata_filters_splits_and_missing_hash(self):
        payload={'sha':'a'*40,'siblings':[{'rfilename':'x.gguf','size':len(GGUF),'lfs':{'sha256':'b'*64}}, {'rfilename':'x-00001-of-00002.gguf','size':24,'lfs':{'sha256':'c'*64}}, {'rfilename':'unsafe.gguf','size':24}]}
        with patch('nodelift.model_library.hub_json',return_value=payload) as get:
            row=self.library.inspect('owner/repo');self.assertEqual(len(row['files']),1);self.assertEqual(row['revision'],'a'*40)
            self.assertIn('?blobs=true',get.call_args.args[0])
        with self.assertRaises(ValueError):self.library.download({'repo':'owner/repo','revision':'main','file':'x.gguf'})
    def test_download_integrity_and_immutable_url(self):
        info={'repo':'owner/repo','revision':'a'*40,'gated':False,'files':[{'name':'x.gguf','bytes':len(GGUF),'sha256':hashlib.sha256(GGUF).hexdigest()}]}
        with patch.object(self.library,'inspect',return_value=info),patch('nodelift.model_library.hub_open',return_value=Response(GGUF)) as get:
            self.library.download({'repo':'owner/repo','revision':'a'*40,'file':'x.gguf'});self.assertEqual(self.wait()['status'],'completed')
            self.assertIn('/resolve/'+'a'*40+'/',get.call_args.args[0])
        info['files'][0]['sha256']='b'*64
        with patch.object(self.library,'inspect',return_value=info),patch('nodelift.model_library.hub_open',return_value=Response(GGUF)):
            self.library.download({'repo':'owner/repo','revision':'a'*40,'file':'x.gguf'});self.assertEqual(self.wait()['status'],'failed')
        self.assertEqual(len(self.library.paths()),1)
    def test_download_size_mismatch_and_no_gated_auto_acceptance(self):
        info={'repo':'owner/repo','revision':'a'*40,'gated':True,'files':[]}
        with patch.object(self.library,'inspect',return_value=info),self.assertRaises(ValueError):self.library.download({'revision':'a'*40})
        info.update(gated=False,files=[{'name':'x.gguf','bytes':len(GGUF),'sha256':'b'*64}])
        for data in (GGUF[:-1],GGUF+b'x'):
            with patch.object(self.library,'inspect',return_value=info),patch('nodelift.model_library.hub_open',return_value=Response(data)):
                self.library.download({'revision':'a'*40,'file':'x.gguf'});self.assertEqual(self.wait()['status'],'failed')
    def test_redirect_allowlist(self):
        redirect=HubRedirect();req=Request('https://huggingface.co/owner/repo/resolve/revision/x.gguf')
        for url in ('http://huggingface.co/file','https://evil.test/file','https://huggingface.co.evil.test/file','https://127.0.0.1/file'):
            with self.assertRaises(ValueError):redirect.redirect_request(req,None,302,'',{},url)
        out=redirect.redirect_request(req,None,302,'',{},'https://cas-bridge.xethub.hf.co/file')
        self.assertFalse(out.has_header('Authorization'))

    def test_actual_file_size_is_verified_independently_of_progress_counter(self):
        identity=self.start();self.library.upload_chunk(identity,0,GGUF)
        with self.library._part().open('ab') as stream:stream.write(b'unaccounted bytes')
        self.library.finish(identity);self.assertEqual(self.wait()['status'],'failed');self.assertEqual(self.library.paths(),[])
