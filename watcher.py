import time, pathlib, re, glob, shutil

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

        # 2. Patcha settings.gradle — atualiza Kotlin para 2.2.0
        for f in glob.glob("/tmp/flet_flutter_build_*/android/settings.gradle"):
            p = pathlib.Path(f)
            txt = p.read_text()
            if "kotlin" in txt and "2.2.0" not in txt:
                novo = re.sub(
                    r'(id\s+"org\.jetbrains\.kotlin\.android"\s+version\s+")[^"]+(")',
                    r'\g<1>2.2.0\g<2>', txt)
                if novo != txt:
                    p.write_text(novo)
                    print(f"[watcher] kotlin 2.2.0 em settings.gradle")
                    # Limpa cache de transforms para forçar re-download com versão correta
                    cache = pathlib.Path.home() / ".gradle/caches/transforms-4"
                    if cache.exists():
                        shutil.rmtree(str(cache), ignore_errors=True)
                        print("[watcher] cache transforms-4 limpo!")

        # 3. Patcha app/build.gradle — compileSdk 35
        for f in glob.glob("/tmp/flet_flutter_build_*/android/app/build.gradle"):
            p = pathlib.Path(f)
            txt = p.read_text()
            if "compileSdk = 35" not in txt and "compileSdkVersion 35" not in txt:
                txt = re.sub(r"(android\s*\{)",
                    "android {\n    compileSdk = 35", txt, count=1)
                p.write_text(txt)
                print(f"[watcher] compileSdk 35 em app/build.gradle")

    except Exception as e:
        print(f"[watcher] erro: {e}")
    time.sleep(1)
