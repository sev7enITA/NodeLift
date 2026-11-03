#include <jni.h>
#include "core.h"
#include <memory>
#include <string>

// JNI's GetStringUTFChars uses Modified UTF-8, not the standard UTF-8 JSON
// accepted by nl_call. Preserve scalar values and reject malformed UTF-16.
static bool json_utf8(JNIEnv * env, jstring input, std::string & out) {
    const jsize size=env->GetStringLength(input);
    const jchar * chars=env->GetStringChars(input,nullptr);
    if(!chars)return false;
    auto release=[&](const jchar * p){env->ReleaseStringChars(input,p);};
    std::unique_ptr<const jchar,decltype(release)> guard(chars,release);
    out.reserve(size_t(size)*3);
    for(jsize i=0;i<size;++i) {
        unsigned int cp=chars[i];
        if(cp==0)return false; // Raw NUL is not JSON and would truncate the C ABI.
        if(cp>=0xd800 && cp<=0xdbff) {
            if(i+1>=size || chars[i+1]<0xdc00 || chars[i+1]>0xdfff)return false;
            cp=0x10000+((cp-0xd800)<<10)+(chars[++i]-0xdc00);
        } else if(cp>=0xdc00 && cp<=0xdfff)return false;
        if(cp<0x80)out.push_back(char(cp));
        else if(cp<0x800){out.push_back(char(0xc0|(cp>>6)));out.push_back(char(0x80|(cp&0x3f)));}
        else if(cp<0x10000){out.push_back(char(0xe0|(cp>>12)));out.push_back(char(0x80|((cp>>6)&0x3f)));out.push_back(char(0x80|(cp&0x3f)));}
        else {out.push_back(char(0xf0|(cp>>18)));out.push_back(char(0x80|((cp>>12)&0x3f)));out.push_back(char(0x80|((cp>>6)&0x3f)));out.push_back(char(0x80|(cp&0x3f)));}
    }
    return true;
}
extern "C" JNIEXPORT jlong JNICALL Java_dev_nodelift_companion_NativeEngine_create(JNIEnv *,jobject) {return reinterpret_cast<jlong>(nl_create());}
extern "C" JNIEXPORT jstring JNICALL Java_dev_nodelift_companion_NativeEngine_request(JNIEnv * env,jobject,jlong handle,jstring input) {
    try {
        std::string text;
        if(!input || !json_utf8(env,input,text)) {
            if(env->ExceptionCheck())return nullptr;
            return env->NewStringUTF("{\"error\":\"invalid Unicode or NUL in JSON request\"}");
        }
        std::unique_ptr<char,decltype(&nl_free_string)> result(nl_call(reinterpret_cast<void *>(handle),text.c_str()),nl_free_string);
        if(!result)return env->NewStringUTF("{\"error\":\"native allocation failed\"}");
        // nl_call serializes with ensure_ascii=true, so Modified UTF-8 output
        // is safe here: supplementary characters are JSON ASCII escapes.
        return env->NewStringUTF(result.get());
    } catch(...) {
        if(env->ExceptionCheck())return nullptr;
        return env->NewStringUTF("{\"error\":\"native request conversion failed\"}");
    }
}
extern "C" JNIEXPORT void JNICALL Java_dev_nodelift_companion_NativeEngine_interrupt(JNIEnv *,jobject,jlong handle) {nl_cancel(reinterpret_cast<void *>(handle));}
extern "C" JNIEXPORT void JNICALL Java_dev_nodelift_companion_NativeEngine_dispose(JNIEnv *,jobject,jlong handle) {nl_destroy(reinterpret_cast<void *>(handle));}
