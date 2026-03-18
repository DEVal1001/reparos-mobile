import os, time, pathlib, re, glob

print("[watcher] iniciado...")

WAKELOCK = pathlib.Path.home() / ".pub-cache/hosted/pub.dev/wakelock_plus-1.4.0/android/build.gradle"

while True:
    try:
        # 1. Patcha wakelock_plus/android/build.gradle
        if WAKELOCK.exists():
            txt = WAKELOCK.read_text()
            if "flutter." in txt or "namespace" not in txt:
                txt = txt.replace("flutter.compileSdkVersion", "35")
                txt = txt.replace("flutter.minSdkVersion", "21")
                txt = txt.replace("flutter.targetSdkVersion", "35")
                if "namespace" not in txt:
                    txt = re.sub(
                        r"(android\s*\{)",
                        "android {\n    namespace 'dev.fluttercommunity.plus.wakelock'",
                        txt, count=1
                    )
                WAKELOCK.write_text(txt)
                print("[watcher] wakelock build.gradle patchado!")

        # 2. Patcha Kotlin version no projeto bootstrap do flet
        for settings in glob.glob("/tmp/flet_flutter_build_*/android/settings.gradle"):
            txt = pathlib.Path(settings).read_text()
            if "kotlin" in txt and "2.2.0" not in txt:
                # Atualiza versão do plugin Kotlin para 2.2.0
                novo = re.sub(
                    r'(id\s+"org\.jetbrains\.kotlin\.android"\s+version\s+")[^"]+(")',
                    r'\g<1>2.2.0\g<2>',
                    txt
                )
                if novo != txt:
                    pathlib.Path(settings).write_text(novo)
                    print(f"[watcher] kotlin version atualizado em {settings}")

        # 3. Patcha ext.kotlin_version no build.gradle do bootstrap
        for build in glob.glob("/tmp/flet_flutter_build_*/android/build.gradle"):
            txt = pathlib.Path(build).read_text()
            if "kotlin_version" in txt and "2.2.0" not in txt:
                novo = re.sub(
                    r"(ext\.kotlin_version\s*=\s*')[^']+(')",
                    r"\g<1>2.2.0\g<2>",
                    txt
                )
                novo = re.sub(
                    r'(ext\.kotlin_version\s*=\s*")[^"]+(")',
                    r'\g<1>2.2.0\g<2>',
                    novo
                )
                if novo != txt:
                    pathlib.Path(build).write_text(novo)
                    print(f"[watcher] kotlin_version atualizado em {build}")

    except Exception as e:
        print(f"[watcher] erro: {e}")
    time.sleep(1)
