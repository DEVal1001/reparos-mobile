import time, pathlib, re, glob

print("[watcher] iniciado...")

WAKELOCK = pathlib.Path.home() / ".pub-cache/hosted/pub.dev/wakelock_plus-1.4.0/android/build.gradle"

while True:
    try:
        # 1. Patcha wakelock_plus build.gradle
        if WAKELOCK.exists():
            txt = WAKELOCK.read_text()
            if "flutter." in txt or "namespace" not in txt:
                txt = txt.replace("flutter.compileSdkVersion", "35")
                txt = txt.replace("flutter.minSdkVersion", "21")
                txt = txt.replace("flutter.targetSdkVersion", "35")
                if "namespace" not in txt:
                    txt = re.sub(r"(android\s*\{)",
                        "android {\n    namespace 'dev.fluttercommunity.plus.wakelock'",
                        txt, count=1)
                WAKELOCK.write_text(txt)
                print("[watcher] wakelock patchado!")

        # 2. Patcha app/build.gradle — compileSdk 35 + DESABILITA R8
        for f in glob.glob("/tmp/flet_flutter_build_*/android/app/build.gradle"):
            txt = pathlib.Path(f).read_text()
            changed = False

            # compileSdk 35
            if "compileSdk = 35" not in txt and "compileSdkVersion 35" not in txt:
                txt = re.sub(r"(android\s*\{)",
                    "android {\n    compileSdk = 35", txt, count=1)
                changed = True

            # Desabilita R8/minify — evita erro kotlinx-metadata-jvm 2.2.0
            if "minifyEnabled false" not in txt:
                txt = txt.replace("minifyEnabled true", "minifyEnabled false")
                txt = txt.replace("shrinkResources true", "shrinkResources false")
                # Garante que buildTypes release tenha minifyEnabled false
                if "buildTypes" in txt and "release" in txt:
                    txt = re.sub(
                        r"(buildTypes\s*\{[^}]*release\s*\{[^}]*)(proguardFiles[^\n]+\n)",
                        r"\1minifyEnabled false\n            shrinkResources false\n            \2",
                        txt
                    )
                changed = True

            if changed:
                pathlib.Path(f).write_text(txt)
                print(f"[watcher] app/build.gradle patchado: {f}")

        # 3. Atualiza Kotlin no settings.gradle
        for f in glob.glob("/tmp/flet_flutter_build_*/android/settings.gradle"):
            txt = pathlib.Path(f).read_text()
            if "kotlin" in txt and "2.2.0" not in txt:
                novo = re.sub(
                    r'(id\s+"org\.jetbrains\.kotlin\.android"\s+version\s+")[^"]+(")',
                    r'\g<1>2.2.0\g<2>', txt)
                if novo != txt:
                    pathlib.Path(f).write_text(novo)
                    print(f"[watcher] kotlin 2.2.0 em settings.gradle: {f}")

        # 4. Atualiza AGP no bootstrap build.gradle para suportar Kotlin 2.2.0
        for f in glob.glob("/tmp/flet_flutter_build_*/android/build.gradle"):
            txt = pathlib.Path(f).read_text()
            if "com.android.tools.build:gradle" in txt and "8." not in txt:
                novo = re.sub(
                    r"com\.android\.tools\.build:gradle:[^'\"]+",
                    "com.android.tools.build:gradle:8.3.2", txt)
                if novo != txt:
                    pathlib.Path(f).write_text(novo)
                    print(f"[watcher] AGP 8.3.2 em build.gradle: {f}")

    except Exception as e:
        print(f"[watcher] erro: {e}")
    time.sleep(1)
