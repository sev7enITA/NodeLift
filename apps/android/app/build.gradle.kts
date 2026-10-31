plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "dev.nodelift.companion"
    compileSdk = 36
    ndkVersion = "27.1.12297006"
    defaultConfig {
        applicationId = "dev.nodelift.companion"
        minSdk = 26
        targetSdk = 36
        versionCode = 3
        versionName = "0.2.1"
        ndk { abiFilters += "arm64-v8a" }
        externalNativeBuild { cmake { arguments += listOf("-DGGML_METAL=OFF","-DGGML_VULKAN=OFF","-DGGML_CPU_ARM_ARCH=armv8-a","-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON") } }
        testInstrumentationRunner = "dev.nodelift.companion.ProtocolCheck"
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    externalNativeBuild { cmake { path = file("../../../native/CMakeLists.txt"); version = "3.22.1" } }
}
