import time, pathlib, re, glob

print("[watcher] iniciado...")

WAKELOCK = pathlib.Path.home() / ".pub-cache/hosted/pub.dev/wakelock_plus-1.4.0/android/build.gradle"

GRADLE_FIXADO = """\
group 'dev.fluttercommunity.plus.wakelock'
version '1.0-SNAPSHOT'

buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:7.3.0' }
}

apply plugin: 'com.android.library'
apply plugin: 'kotlin-android'

android {
    namespace 'dev.fluttercommunity.plus.wakelock'
    compileSdkVersion 35
    defaultConfig { minSdkVersion 21; targetSdkVersion 35 }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = '1.8'
        freeCompilerArgs += ['-Xskip-metadata-version-check']
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation "org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.24"
}
"""

patched_wakelock = False

while True:
    try:
        # Patcha wakelock build.gradle com -Xskip-metadata-version-check
        if WAKELOCK.exists() and not patched_wakelock:
            WAKELOCK.write_text(GRADLE_FIXADO)
            print("[watcher] wakelock patchado com Xskip-metadata!")
            patched_wakelock = True

        # Patcha app/build.gradle — compileSdk 35
        for f in glob.glob("/tmp/flet_flutter_build_*/android/app/build.gradle"):
            p = pathlib.Path(f)
            txt = p.read_text()
            if "compileSdk = 35" not in txt:
                txt = re.sub(r"(android\s*\{)",
                    "android {\n    compileSdk = 35", txt, count=1)
                p.write_text(txt)
                print(f"[watcher] compileSdk 35 em app/build.gradle")

    except Exception as e:
        print(f"[watcher] erro: {e}")
    time.sleep(1)
