# PibbyGlitchCursor

> **Credits**
> - Based on the [Pibby Apocalypse Cursor Recreation Script](https://gamebanana.com/tools/15314) by **[jarekboho](https://gamebanana.com/members/2145650)**. That's where the 10 cursor frames and the frame-by-frame animation logic come from.
> - The cursor art comes from **[Pibby: Apocalypse](https://gamebanana.com/wips/73842)** by the Pibby: Apocalypse Team, led by BAUDASlel (owner and director). It's licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): keep these credits, and don't use it commercially.
> - The full credits list for all 72 people is in `CREDITS.md`. In the installer app, click **Credits…**.

A fully glitched, animated pointer set.

**The normal arrow** uses `images/cursor/mouse (1..10).png` unchanged and behaves the way `scripts/cursor.lua` does:

- 10 frames, played 1 → 10 and then looping
- one frame per game update at 60 fps (about 16.7 ms per frame)
- hotspot on the top-left pixel (0,0), the `FlxG.mouse.load()` default

**Every other pointer** is drawn in the arrow's pixel style and breaks up with the same glitches on the same 10-frame rhythm. That includes text, link hand, busy, working in background, help, crosshair, unavailable, handwriting, all four resize pointers, move, alternate select, location select and person select. The glitches are:

- row bands sliding sideways
- outline slivers and dashes breaking off
- 1 px jitter

Help, working, location and person are your arrow frames with a glitching badge, so they stay in sync with the arrow.

All pointers are 1:1 pixels at normal size, with exact 2×/3×/4× copies for HiDPI screens.

Rebuild with `python build_cursors.py` (needs Pillow). The art and glitch engine for the extra pointers are in `glitch_pointers.py`.

## Easiest: the installer app

**Windows:** double-click `PibbyGlitchCursorInstaller.exe`. It's a single file and needs no admin rights. Windows may show "Windows protected your PC" because the app isn't code-signed. Click **More info → Run anyway**.

**Linux:** run `PibbyGlitchCursorInstaller-x86_64.AppImage`. You can build it with the steps at the bottom of this file. Mark it executable first with `chmod +x` or Properties → Allow executing.

The app shows the animated cursor and has these controls:

- **Back up my current cursors before installing.** This is ticked automatically when you're using a custom cursor set. It saves your current cursor settings and copies of the cursor files they use, so they can come back even if their original folder gets deleted.
- **Install / Reinstall** puts in the full glitch set and switches to it right away.
- **Uninstall** removes it and switches to the standard system cursors. Your backup is kept.
- **Restore backup** is available once a backup exists. It brings back exactly what you had before.

Backups are stored at:
- Windows: `%LOCALAPPDATA%\PibbyGlitchCursor\backup`
- Linux: `~/.local/share/PibbyGlitchCursor/backup`

## Windows (manual)

1. In `windows\`, right-click `install.inf` and choose **Install**. If Windows 11 hides the option, choose **Show more options** first.
2. Open **Settings → Bluetooth & devices → Mouse → Additional mouse settings → Pointers**.
3. Pick **PibbyGlitchCursor** from the Scheme list and click **OK**.

To undo it, pick **Windows Default** in that Pointers tab, or use the installer app's **Uninstall** / **Restore backup**.

> Windows stretches every cursor to a square. That's why each frame sits on a transparent 32×32 canvas: it keeps the pixel art from getting distorted.

## Linux (manual; X11 and Wayland: GNOME, KDE, Xfce, Cinnamon, etc.)

Copy `PibbyGlitchCursor-linux.zip` to the Linux machine, then run:

```sh
unzip PibbyGlitchCursor-linux.zip -d pibby && sh pibby/install.sh
```

This puts the theme in `~/.icons/PibbyGlitchCursor`, makes it the default, and switches GNOME or KDE over to it. Log out and back in if some apps still show the old cursor.

The theme has 15 glitched cursors under all their standard X11/CSS names, including:

- `default`, `text`, `pointer`
- `wait`, `progress`, `help`
- `crosshair`, `not-allowed`, `pencil`
- `move`, `up-arrow`
- all `*-resize`

That's 103 names in total. Location and person select exist only on Windows. Any rarer cursor an app asks for falls back to Adwaita.

To install it by hand, extract `linux/PibbyGlitchCursor.tar.gz` into `~/.icons/` (or `/usr/share/icons/` for every user), then choose it in your desktop's cursor settings.

## Building the installer app

From the project folder, with Python 3, Pillow and PyInstaller installed (`pip install pillow pyinstaller`), run:

```sh
python build_installer.py
```

- **On Windows** this produces `dist/PibbyGlitchCursorInstaller.exe`.
- **On Linux** it produces `dist/PibbyGlitchCursorInstaller-x86_64.AppImage`. This also needs `python3-tk` and `appimagetool`. Put `appimagetool` in your PATH, or place `appimagetool-x86_64.AppImage` from https://github.com/AppImage/appimagetool/releases next to the script.

You can only build an AppImage on Linux.
