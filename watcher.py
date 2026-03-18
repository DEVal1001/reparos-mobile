import os, time, pathlib

GRADLE = pathlib.Path.home() / ".pub-cache/hosted/pub.dev/wakelock_plus-1.4.0/android/build.gradle"

FIXADO = """group 'dev.fluttercommunity.plus.wakelock'
version '1.0-SNAPSHOT'

buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.1.0' }
}

apply plugin: 'com.android.library'

android {
    namespace 'dev.fluttercommunity.plus.wakelock'
    compileSdkVersion 35
    defaultConfig { minSdkVersion 21; targetSdkVersion 35 }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
}
"""

print("[watcher] iniciado, aguardando wakelock_plus...")
while True:
    try:
        if GRADLE.exists():
            txt = GRADLE.read_text()
            if "flutter." in txt or "namespace" not in txt:
                GRADLE.write_text(FIXADO)
                print("[watcher] patch aplicado com namespace + compileSdk 35!")
    except Exception as e:
        print(f"[watcher] erro: {e}")
    time.sleep(1)
