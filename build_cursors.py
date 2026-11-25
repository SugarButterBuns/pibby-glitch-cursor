"""
Build an animated cursor set for Windows (.ani) and Linux (Xcursor theme).

The normal arrow is images/cursor/mouse (1..10).png, exactly as in scripts/cursor.lua:
  * 10 frames, played in order 1 -> 10 and looping
  * one frame per game update (Psych Engine default 60 fps) -> ~16.7 ms/frame
  * hotspot at the top-left pixel (0, 0), same as FlxG.mouse.load() defaults
  * pixels are kept 1:1 (larger sizes are exact 2x/3x/4x nearest-neighbour)

Every other pointer (text, hand, busy, resize, ...) comes from glitch_pointers.py:
drawn in the arrow's pixel style and glitched with the same effects and rhythm.

Credits: based on the "Pibby Apocalypse Cursor Recreation Script" by jarekboho
(https://gamebanana.com/tools/15314). Cursor art from Pibby: Apocalypse by the Pibby: Apocalypse
Team (https://gamebanana.com/wips/73842), licensed CC BY-NC 4.0. Full list: CREDITS.md.

Requires: Python 3 + Pillow.   Run:  python build_cursors.py
Output goes to ./dist
"""
import gzip
import io
import struct
import tarfile
import zipfile
from pathlib import Path

from PIL import Image

import glitch_pointers

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "images" / "cursor"
DIST = ROOT / "dist"
THEME = "PibbyGlitchCursor"
FRAMES = 10
FPS = 60

arrow_frames = [Image.open(SRC / f"mouse ({i}).png").convert("RGBA") for i in range(1, FRAMES + 1)]
NOMINAL = arrow_frames[0].width  # 24: the art's 1:1 pixel size on Linux

# Windows role -> (frames, hotspot). Order is the order of a Windows scheme string.
ROLES = {"Arrow": (arrow_frames, (0, 0)), **glitch_pointers.build(arrow_frames)}
ROLE_ORDER = ["Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen", "No",
              "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand", "Pin", "Person"]
assert sorted(ROLES) == sorted(ROLE_ORDER)

# Windows role -> Linux/X11 cursor names (first one is the real file, the rest are symlinks)
LINUX_NAMES = {
    "Arrow": ["default", "left_ptr", "arrow", "top_left_arrow", "left_arrow",
              "x-cursor", "X_cursor", "pointer-default"],
    "Help": ["help", "question_arrow", "whats_this", "left_ptr_help",
             "5c6cd98b3f3ebcb1f9c7f1c204630408", "d9ce0ab605698f320427677b458ad60b"],
    "AppStarting": ["progress", "left_ptr_watch", "half-busy",
                    "00000000000000020006000e7e9ffc3f", "08e8e1c95fe2fc01f976f1e063a24ccd",
                    "3ecb610c1bf2410f44200f48c40d3599"],
    "Wait": ["wait", "watch"],
    "Crosshair": ["crosshair", "cross", "tcross", "cross_reverse", "diamond_cross", "cell", "plus"],
    "IBeam": ["text", "xterm", "ibeam", "vertical-text"],
    "NWPen": ["pencil", "draft"],
    "No": ["not-allowed", "no-drop", "forbidden", "crossed_circle", "circle", "dnd-no-drop",
           "03b6e0fcb3499374a867c041f52298f0"],
    "SizeNS": ["ns-resize", "n-resize", "s-resize", "size_ver", "sb_v_double_arrow",
               "v_double_arrow", "row-resize", "split_v", "top_side", "bottom_side",
               "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
    "SizeWE": ["ew-resize", "e-resize", "w-resize", "size_hor", "sb_h_double_arrow",
               "h_double_arrow", "col-resize", "split_h", "left_side", "right_side",
               "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
    "SizeNWSE": ["nwse-resize", "nw-resize", "se-resize", "size_fdiag", "bd_double_arrow",
                 "top_left_corner", "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "SizeNESW": ["nesw-resize", "ne-resize", "sw-resize", "size_bdiag", "fd_double_arrow",
                 "top_right_corner", "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "SizeAll": ["move", "all-scroll", "fleur", "size_all", "grabbing", "closedhand", "dnd-move",
                "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"],
    "UpArrow": ["up-arrow", "center_ptr", "sb_up_arrow"],
    "Hand": ["pointer", "hand", "hand1", "hand2", "pointing_hand", "grab", "openhand",
             "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822"],
    # Pin and Person are Windows-only pointers; Linux has no equivalent name.
}

ANI_NAME = {r: f"{THEME}.ani" if r == "Arrow" else f"{THEME}-{r}.ani" for r in ROLE_ORDER}


def scaled(img, k):
    return img if k == 1 else img.resize((img.width * k, img.height * k), Image.NEAREST)


# ---------------------------------------------------------------- Windows ---
def padded_square(img, side):
    """Windows stretches cursors to a square; pad (not stretch) to keep pixels exact."""
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, (0, 0))
    return canvas


def png(img):
    """PNG-compressed cursor image (supported by Windows Vista and later).
    Stores exactly the same RGBA values the uncompressed bitmap would."""
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def cur_file(frame, hot):
    # 32 is pixel-exact at 100% scaling; 64/96/128 are exact integer upscales for HiDPI.
    imgs = []
    for k in (1, 2, 3, 4):
        side = 32 * k
        imgs.append((side, (hot[0] * k, hot[1] * k), png(padded_square(scaled(frame, k), side))))
    out = struct.pack("<HHH", 0, 2, len(imgs))
    offset = 6 + 16 * len(imgs)
    for side, (hx, hy), data in imgs:
        out += struct.pack("<BBBBHHII", side % 256, side % 256, 0, 0, hx, hy, len(data), offset)
        offset += len(data)
    for _, _, data in imgs:
        out += data
    return out


def chunk(cid, data):
    pad = b"\0" if len(data) % 2 else b""
    return cid + struct.pack("<I", len(data)) + data + pad


def ani_file(role):
    frames, hot = ROLES[role]
    title = THEME if role == "Arrow" else f"{THEME} {role}"
    jiffies = max(1, round(60 / FPS))  # 1 jiffy = 1/60 s
    anih = struct.pack("<9I", 36, len(frames), len(frames), 0, 0, 0, 0, jiffies, 0x1)  # AF_ICON
    fram = b"fram" + b"".join(chunk(b"icon", cur_file(f, hot)) for f in frames)
    info = b"INFO" + chunk(b"INAM", f"{title}\0".encode())
    body = b"ACON" + chunk(b"LIST", info) + chunk(b"anih", anih) + chunk(b"LIST", fram)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def inf_file():
    reg_vals = "\n".join(
        f'HKCU,"Control Panel\\Cursors",{r},0x00020000,"%10%\\%CUR_DIR%\\{ANI_NAME[r]}"' for r in ROLE_ORDER)
    scheme = ",".join(f"%10%\\%CUR_DIR%\\{ANI_NAME[r]}" for r in ROLE_ORDER)
    files = "\n".join(f'"{ANI_NAME[r]}"' for r in ROLE_ORDER)
    return f"""[Version]
signature="$CHICAGO$"

[DefaultInstall]
CopyFiles = Scheme.Cur
AddReg    = Scheme.Reg

[DestinationDirs]
Scheme.Cur = 10,"%CUR_DIR%"

[Scheme.Reg]
HKCU,"Control Panel\\Cursors\\Schemes","%SCHEME_NAME%",0x00020000,"{scheme}"
HKCU,"Control Panel\\Cursors",,0x00000000,"%SCHEME_NAME%"
{reg_vals}
HKCU,"Control Panel\\Cursors",Scheme Source,0x00010001,1

[Scheme.Cur]
{files}

[Strings]
CUR_DIR     = "Cursors\\{THEME}"
SCHEME_NAME = "{THEME}"
"""


# ------------------------------------------------------------------ Linux ---
def xcursor_file(role):
    frames, hot = ROLES[role]
    delay = round(1000 / FPS)  # 17 ms
    # Xcursor pixels are premultiplied ARGB in little-endian, i.e. B,G,R,A bytes.
    # Premultiply once per frame; nearest-neighbour scaling commutes with it.
    premul = []
    for f in frames:
        px = f.tobytes()
        bgra = bytearray(len(px))
        for i in range(0, len(px), 4):
            r, g, b, a = px[i:i + 4]
            bgra[i:i + 4] = (b * a // 255, g * a // 255, r * a // 255, a)
        premul.append(Image.frombytes("RGBA", f.size, bytes(bgra)))  # channels hold B,G,R,A
    images = []
    for k in (1, 2, 3, 4):  # nominal sizes 24, 48, 72, 96 (24 = Linux default size)
        nominal = NOMINAL * k
        for f in premul:
            s = scaled(f, k)
            hdr = struct.pack("<9I", 36, 0xFFFD0002, nominal, 1, s.width, s.height, hot[0] * k, hot[1] * k, delay)
            images.append((nominal, hdr + s.tobytes()))
    ntoc = len(images)
    out = b"Xcur" + struct.pack("<III", 16, 0x10000, ntoc)
    pos = 16 + 12 * ntoc
    for nominal, data in images:
        out += struct.pack("<III", 0xFFFD0002, nominal, pos)
        pos += len(data)
    return out + b"".join(d for _, d in images)


INDEX_THEME = f"""[Icon Theme]
Name={THEME}
Comment=Animated glitch arrow (10 frames @ {FPS} fps)
Inherits=Adwaita
"""

INSTALL_SH = f"""#!/bin/sh
# Installs the {THEME} cursor theme for the current user and selects it.
set -e
cd "$(dirname "$0")"
mkdir -p "$HOME/.icons"
rm -rf "$HOME/.icons/{THEME}"
tar -xzf {THEME}.tar.gz -C "$HOME/.icons"
mkdir -p "$HOME/.icons/default"
printf '[Icon Theme]\\nInherits={THEME}\\n' > "$HOME/.icons/default/index.theme"
if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.gnome.desktop.interface cursor-theme '{THEME}' 2>/dev/null || true
fi
if command -v plasma-apply-cursortheme >/dev/null 2>&1; then
  plasma-apply-cursortheme {THEME} || true
fi
echo "Installed {THEME}. Log out and back in if some apps still show the old cursor."
"""


def tar_add(tar, name, data=None, mode=0o644, link=None):
    ti = tarfile.TarInfo(name)
    ti.mtime = 0
    if link:
        ti.type, ti.linkname, ti.mode = tarfile.SYMTYPE, link, 0o777
        tar.addfile(ti)
    else:
        ti.size, ti.mode = len(data), mode
        tar.addfile(ti, io.BytesIO(data))


def main():
    win = DIST / "windows"
    lin = DIST / "linux"
    win.mkdir(parents=True, exist_ok=True)
    lin.mkdir(parents=True, exist_ok=True)

    for role in ROLE_ORDER:
        (win / ANI_NAME[role]).write_bytes(ani_file(role))
    (win / "install.inf").write_bytes(inf_file().replace("\n", "\r\n").encode("ascii"))

    tgz = lin / f"{THEME}.tar.gz"
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        tar_add(tar, f"{THEME}/index.theme", INDEX_THEME.encode())
        tar_add(tar, f"{THEME}/cursor.theme", INDEX_THEME.encode())
        for role, (main_name, *aliases) in LINUX_NAMES.items():
            tar_add(tar, f"{THEME}/cursors/{main_name}", xcursor_file(role))
            for alias in aliases:
                tar_add(tar, f"{THEME}/cursors/{alias}", link=main_name)
    tgz_bytes = gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)  # fixed timestamp: reproducible
    tgz.write_bytes(tgz_bytes)
    (lin / "install.sh").write_bytes(INSTALL_SH.encode())

    # A zip with the sh marked executable, convenient to copy to a Linux box.
    with zipfile.ZipFile(DIST / f"{THEME}-linux.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        zi = zipfile.ZipInfo("install.sh")
        zi.external_attr = (0o100755 << 16)
        z.writestr(zi, INSTALL_SH)
        z.writestr(zipfile.ZipInfo(tgz.name), tgz_bytes)

    print("Built:")
    for p in sorted(DIST.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
