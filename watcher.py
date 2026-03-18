import os, time, pathlib, re

GRADLE = pathlib.Path.home() / ".pub-cache/hosted/pub.dev/wakelock_plus-1.4.0/android/build.gradle"

print("[watcher] iniciado, aguardando wakelock_plus...")
patched = False

while True:
    try:
        if GRADLE.exists():
            txt = GRADLE.read_text()
            needs_patch = (
                "flutter.compileSdkVersion" in txt or
                "flutter.minSdkVersion" in txt or
                "flutter.targetSdkVersion" in txt or
                "namespace" not in txt
            )
            if needs_patch:
                # Substitui apenas as linhas problemáticas, mantém o resto
                txt = txt.replace("flutter.compileSdkVersion", "35")
                txt = txt.replace("flutter.minSdkVersion",     "21")
                txt = txt.replace("flutter.targetSdkVersion",  "35")

                # Adiciona namespace logo após "apply plugin: 'com.android.library'"
                if "namespace" not in txt:
                    txt = txt.replace(
                        "apply plugin: 'com.android.library'",
                        "apply plugin: 'com.android.library'\n"
                    )
                    txt = re.sub(
                        r"(android\s*\{)",
                        "android {\n    namespace 'dev.fluttercommunity.plus.wakelock'",
                        txt,
                        count=1
                    )

                GRADLE.write_text(txt)
                print("[watcher] patch aplicado!")
                print("[watcher] conteudo:")
                print(GRADLE.read_text())
                patched = True
    except Exception as e:
        print(f"[watcher] erro: {e}")
    time.sleep(1)
