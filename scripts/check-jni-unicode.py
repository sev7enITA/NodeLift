#!/usr/bin/env python3
"""Exercise the real JNI request bridge on macOS/JDK without loading weights.

This validates JNI string conversion, not Android-device behavior. An optional
Android compiler checks the same source against the NDK ABI without installing
an APK. No host service, model selection or phone state is changed.
"""
import argparse,hashlib,json,platform,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=r'''package dev.nodelift.companion;
public class NativeEngine {
  private native long create();
  private native String request(long handle, String value);
  private native void dispose(long handle);
  private static String json(String value) { return "{\"op\":\"reset\",\"note\":\""+value+"\"}"; }
  public static void main(String[] args) {
    System.load(args[0]); NativeEngine e=new NativeEngine(); long h=e.create();
    String[] names={"ascii","accent","chinese","combining","emoji","supplementary_cjk","maximum_scalar","escaped_emoji","escaped_nul","raw_nul","high_surrogate","low_surrogate","reversed_pair","high_then_ascii","null_input"};
    String[] values={"hello","caff\u00e8","\u4e2d\u6587","e\u0301",new String(Character.toChars(0x1f600)),new String(Character.toChars(0x20000)),new String(Character.toChars(0x10ffff)),"\\ud83d\\ude00","\\u0000",String.valueOf((char)0),String.valueOf((char)0xd800),String.valueOf((char)0xdc00),new String(new char[]{0xdc00,0xd800}),new String(new char[]{0xd800,'A'}),null};
    for(int i=0;i<names.length;i++)System.out.println(names[i]+"\t"+e.request(h,values[i]==null?null:json(values[i])));
    e.dispose(h);
  }
}'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--jni-source',type=Path,default=ROOT/'native/jni.cpp');ap.add_argument('--library-dir',type=Path,default=ROOT/'native/build/host/lib');ap.add_argument('--android-compiler',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 if platform.system()!='Darwin':raise SystemExit('This qualification harness currently requires macOS and a JDK; it is not an Android device test.')
 j=Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())
 with tempfile.TemporaryDirectory(prefix='nodelift-jni-') as tmp:
  out=Path(tmp);source=out/'NativeEngine.java';source.write_text(JAVA)
  native=out/'libjni-check.dylib'
  subprocess.run(['clang++','-std=c++17','-dynamiclib',str(args.jni_source.resolve()),'-I'+str(ROOT/'native'),'-I'+str(j/'include'),'-I'+str(j/'include/darwin'),'-L'+str(args.library_dir.resolve()),'-lnodelift','-Xlinker','-rpath','-Xlinker',str(args.library_dir.resolve()),'-o',str(native)],check=True,capture_output=True,text=True)
  subprocess.run([str(j/'bin/javac'),'-d',str(out),str(source)],check=True,capture_output=True,text=True)
  run=subprocess.run([str(j/'bin/java'),'-cp',str(out),'dev.nodelift.companion.NativeEngine',str(native)],check=True,capture_output=True,text=True)
  rows=[]
  for line in run.stdout.splitlines():
   name,payload=line.split('\t',1);result=json.loads(payload)
   expected='invalid Unicode or NUL in JSON request' if name in ('raw_nul','high_surrogate','low_surrogate','reversed_pair','high_then_ascii','null_input') else 'no model loaded'
   rows.append({'case':name,'result':result,'passed':result=={'error':expected}})
  android=False
  if args.android_compiler:
   subprocess.run([str(args.android_compiler.resolve()),'-std=c++17','-O3','-fPIC','-c',str(args.jni_source.resolve()),'-I'+str(ROOT/'native'),'-o',str(out/'jni-android.o')],check=True,capture_output=True,text=True);android=True
  report={'scope':'Real JVM/JNI bridge on macOS, no model loaded; optional Android object compilation is not a device test','jni_source_sha256':sha(args.jni_source),'native_library_sha256':sha(args.library_dir/'libnodelift.dylib'),'jni_harness_binary_sha256':sha(native),'android_object_compiled':android,'cases':rows,'passed':len(rows)==15 and all(r['passed'] for r in rows)}
  args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps({'cases':len(rows),'passed':report['passed'],'android_object_compiled':android}))
  if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
