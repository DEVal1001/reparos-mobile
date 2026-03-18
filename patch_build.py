"""
Script que:
1. Faz flutter pub get num projeto temporário para popular o cache
2. Corrige o build.gradle do wakelock_plus
3. Roda flet build apk
"""
import os, subprocess, sys, shutil, pathlib

HOME = pathlib.Path.home()
PUB_CACHE = HOME / ".pub-cache"
WAKELOCK_GRADLE = PUB_CACHE / "hosted/pub.dev/wakelock_plus-1.4.0/android/build.gradle"

GRADLE_FIXADO = """\
group 'dev.fluttercommunity.plus.wakelock'
version '1.0-SNAPSHOT'

buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.3.0'
    }
}

apply plugin: 'com.android.library'

android {
    compileSdkVersion 34

    defaultConfig {
        minSdkVersion 21
        targetSdkVersion 34
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
}
"""

def run(cmd, **kw):
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd, shell=True, **kw)
    return r.returncode

def popular_pub_cache():
    """Cria projeto temp e faz flutter pub get para popular o cache."""
    tmp = pathlib.Path("/tmp/fix_wakelock")
    if tmp.exists():
        shutil.rmtree(tmp)
    
    run(f"flutter create --platforms android --project-name fixwakelock {tmp} -q")
    
    pubspec = tmp / "pubspec.yaml"
    content = pubspec.read_text()
    # Adiciona wakelock_plus nas dependências
    content = content.replace(
        "dependencies:\n  flutter:\n    sdk: flutter",
        "dependencies:\n  flutter:\n    sdk: flutter\n  wakelock_plus: 1.4.0"
    )
    pubspec.write_text(content)
    
    os.chdir(tmp)
    run("flutter pub get || true")
    os.chdir("/")

def corrigir_wakelock():
    """Substitui o build.gradle problemático pelo corrigido."""
    if WAKELOCK_GRADLE.exists():
        print(f"\n✅ Encontrado: {WAKELOCK_GRADLE}")
        print("Conteúdo ANTES:")
        print(WAKELOCK_GRADLE.read_text())
        WAKELOCK_GRADLE.write_text(GRADLE_FIXADO)
        print("\nConteúdo DEPOIS:")
        print(WAKELOCK_GRADLE.read_text())
        print("✅ wakelock_plus corrigido!")
        return True
    else:
        print(f"❌ Arquivo não encontrado: {WAKELOCK_GRADLE}")
        # Busca alternativa
        results = list(PUB_CACHE.rglob("wakelock_plus*/android/build.gradle"))
        print(f"Encontrados: {results}")
        for f in results:
            print(f"Corrigindo: {f}")
            f.write_text(GRADLE_FIXADO)
        return bool(results)

if __name__ == "__main__":
    print("=== PASSO 1: Popular pub cache ===")
    popular_pub_cache()
    
    print("\n=== PASSO 2: Corrigir wakelock_plus ===")
    ok = corrigir_wakelock()
    if not ok:
        print("AVISO: wakelock não encontrado, continuando mesmo assim...")
    
    print("\n=== PASSO 3: Build APK ===")
    src_dir = pathlib.Path(__file__).parent
    os.chdir(src_dir)
    code = run("flet build apk --verbose")
    sys.exit(code)
