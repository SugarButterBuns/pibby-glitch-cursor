"""
Builds the installer app for the system you run it on.

  Windows:  python build_installer.py   ->  dist/PibbyGlitchCursorInstaller.exe  (single file)
  Linux:    python3 build_installer.py  ->  dist/PibbyGlitchCursorInstaller-x86_64.AppImage

Credits: based on the "Pibby Apocalypse Cursor Recreation Script" by jarekboho
(https://gamebanana.com/tools/15314). Cursor art from Pibby: Apocalypse by the Pibby: Apocalypse
Team (https://gamebanana.com/wips/73842), licensed CC BY-NC 4.0. Full list: CREDITS.md.

Needs: Python 3 with tkinter, Pillow, PyInstaller  (pip install pillow pyinstaller)
Linux also needs: python3-tk, and appimagetool (in PATH, or appimagetool-x86_64.AppImage
next to this script) from https://github.com/AppImage/appimagetool/releases
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "installer"
NAME = "PibbyGlitchCursorInstaller"
SEP = ";" if os.name == "nt" else ":"


def run(*cmd, **kw):
    print(">", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def main():
    run(sys.executable, ROOT / "build_cursors.py")  # make sure dist/ is current
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)

    # app icon from the cleanest arrow frame, padded square, pixel-exact upscales
    frame = Image.open(ROOT / "images/cursor/mouse (7).png").convert("RGBA")
    icon = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    icon.paste(frame, (4, 0))
    icon_png = BUILD / "icon.png"
    icon.resize((256, 256), Image.NEAREST).save(icon_png)
    icon_ico = BUILD / "icon.ico"
    icon.resize((256, 256), Image.NEAREST).save(icon_ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    data = [(ROOT / "images/cursor", "payload/preview")]
    if os.name == "nt":
        data += [(p, "payload/windows") for p in sorted((ROOT / "dist/windows").glob("*.ani"))]
    else:
        data += [(ROOT / "dist/linux/PibbyGlitchCursor.tar.gz", "payload/linux")]
    args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
            "--name", NAME, "--distpath", BUILD / "out", "--workpath", BUILD / "work",
            "--specpath", BUILD, "--icon", icon_ico if os.name == "nt" else icon_png]
    for src, dest in data:
        args += ["--add-data", f"{src}{SEP}{dest}"]
    if os.name == "nt":
        # Standard-library parts the app never uses but PyInstaller pulls in through other
        # modules' optional imports (pathlib -> urllib.request -> ssl, ...). Leaving them out
        # saves ~3 MB and means the app ships with no networking or SSL code at all.
        # (hashlib still works without _hashlib, using Python's built-in hashes.)
        for mod in ("ssl", "_ssl", "_hashlib", "socket", "_socket", "select", "http", "urllib.request",
                    "ftplib", "email", "decimal", "_decimal", "lzma", "_lzma", "bz2", "_bz2",
                    "compression.zstd", "_zstd"):
            args += ["--exclude-module", mod]
    run(*args, ROOT / "installer_gui.py")

    if os.name == "nt":
        out = ROOT / "dist" / f"{NAME}.exe"
        shutil.copyfile(BUILD / "out" / f"{NAME}.exe", out)
        print(f"\nBuilt {out}")
        return

    # ---- Linux: wrap the single binary in an AppImage
    appdir = BUILD / "AppDir"
    (appdir / "usr/bin").mkdir(parents=True)
    shutil.copy2(BUILD / "out" / NAME, appdir / "usr/bin" / NAME)
    shutil.copyfile(icon_png, appdir / f"{NAME}.png")
    (appdir / f"{NAME}.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Pibby Glitch Cursor Installer\n"
        f"Exec={NAME}\nIcon={NAME}\nCategories=Settings;DesktopSettings;\nTerminal=false\n")
    apprun = appdir / "AppRun"
    apprun.write_text(f'#!/bin/sh\nHERE="$(dirname "$(readlink -f "$0")")"\nexec "$HERE/usr/bin/{NAME}" "$@"\n')
    apprun.chmod(apprun.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    tool = shutil.which("appimagetool") or next(
        (str(p) for p in ROOT.glob("appimagetool*.AppImage")), None)
    if not tool:
        sys.exit("appimagetool not found. Download appimagetool-x86_64.AppImage from\n"
                 "https://github.com/AppImage/appimagetool/releases, chmod +x it, put it next\n"
                 "to this script and run again.")
    out = ROOT / "dist" / f"{NAME}-x86_64.AppImage"
    run(tool, appdir, out, env={**os.environ, "ARCH": "x86_64"})
    print(f"\nBuilt {out}")


if __name__ == "__main__":
    main()
