# Pibby Glitch Cursor

A fully glitched, animated mouse cursor set for **Windows** and **Linux**, with a one-click installer app.

![Every glitched pointer, all 10 frames](dist/preview-all-pointers.png)

- **The normal arrow** is the original 10-frame glitch animation, frame-for-frame and pixel-for-pixel, at the same 60 fps.
- **16 more pointers** match it: text, link hand, busy, help, resize, move and the rest. They're drawn in the same pixel style and glitch on the same rhythm.
- **Pixel-exact at normal size**, with clean 2×/3×/4× copies for high-DPI screens.

## Download & install

Get the latest version from **[Releases](../../releases)**:

| System | Download | How |
|---|---|---|
| Windows | `PibbyGlitchCursorInstaller.exe` | Double-click it. No admin rights are needed. If Windows warns the app is unrecognized, click *More info → Run anyway* (it isn't code-signed). |
| Linux (app) | `PibbyGlitchCursorInstaller-x86_64.AppImage` | Make it executable (`chmod +x`, or Properties → Allow executing), then run it. |
| Linux (no app) | `PibbyGlitchCursor-linux.zip` | Unzip it, then run `sh install.sh`. |

The installer app:
- **Detects** your current cursors, with a per-pointer **Details** view.
- **Install / Uninstall:** one click each.
- **Backup:** saves your current custom cursors first, including copies of the cursor files.
- **Restore backup:** brings them back.

To install without the app, see [dist/README.md](dist/README.md).

## Build from source

You need Python 3 with tkinter, and `pip install pillow pyinstaller`. Then:

```sh
python build_cursors.py      # cursor files -> dist/windows, dist/linux
python build_installer.py    # installer app -> dist/ (.exe on Windows, .AppImage on Linux)
```

| File | What it is |
|---|---|
| `images/cursor/`, `scripts/cursor.lua` | The original frames and animation script |
| `glitch_pointers.py` | Pixel art and glitch engine for the other 16 pointers |
| `build_cursors.py` | Writes Windows `.ani` files and the Linux Xcursor theme |
| `installer_gui.py` | The installer app (Windows and Linux) |
| `credits.py` | The credits list (also used to write `CREDITS.md`) |

## Privacy

The installer app is fully offline. It has no accounts, no tracking and no phone-home.

**It does not:**
- **Connect to the internet.** The app contains no networking code: no update checks, analytics, telemetry or crash reporting. The only way anything goes online is if *you* click a credits link. That opens the page in your own web browser, and the app itself never makes the request.
- **Collect, send or upload anything.** Nothing leaves your computer.
- **Need admin rights.** It never asks for them, so it can't change system-wide settings.
- **Run in the background, start with your computer, or install services.** It runs only while its window is open. On Windows it unpacks itself to a temporary folder while running and deletes that folder when you close it.
- **Read anything besides cursor settings.** It doesn't look at your files, browsing data, other apps or personal info.

**What it does, and only when you click a button:**

| | Windows | Linux |
|---|---|---|
| **Reads (to detect your current cursors)** | Your cursor settings in `HKEY_CURRENT_USER\Control Panel\Cursors`, plus Windows' built-in list of cursor schemes | Your cursor theme setting from GNOME/Cinnamon/MATE (`gsettings`), Xfce (`xfconf-query`), KDE (`~/.config/kcminputrc`) and `~/.icons/default/index.theme` |
| **Install** | Copies the cursor files to `%LOCALAPPDATA%\Cursors\PibbyGlitchCursor` and points your cursor settings at them | Unpacks the theme to `~/.icons/PibbyGlitchCursor` and selects it in your desktop's settings |
| **Backup** (only if ticked) | Saves your cursor settings and copies the cursor files they use to `%LOCALAPPDATA%\PibbyGlitchCursor\backup` | Saves your theme settings and copies a user-installed theme to `~/.local/share/PibbyGlitchCursor/backup` |
| **Uninstall** | Deletes its cursor folder and switches back to Windows Default | Deletes its theme folder and resets the cursor setting |
| **Restore** | Puts back your backed-up settings and recreates any backed-up cursor files that were deleted | The same, for your theme |

The backup stays on your computer. It holds your old cursor settings and the file paths they used (which include your username, as all Windows/Linux paths do). Delete the backup folder at any time to remove it.

**You don't have to trust me:**
- **The app is open source.** It's all in one readable file, [`installer_gui.py`](installer_gui.py), so you can search it for anything network-related yourself.
- **You can build the app yourself** from this source (see *Build from source*). The Linux AppImage is built by the public GitHub Actions workflow in [`.github/workflows`](.github/workflows), not on anyone's PC.
- **You can check your downloads** against `SHA256SUMS.txt` on each release. On Windows, run `Get-FileHash <file>` in PowerShell. On Linux, run `sha256sum -c SHA256SUMS.txt`.
- **You can install without any app at all.** Use the plain cursor files and the [manual steps](dist/README.md).

## Credits

- Based on the **[Pibby Apocalypse Cursor Recreation Script](https://gamebanana.com/tools/15314)** by **[jarekboho](https://gamebanana.com/members/2145650)**.
- The cursor art comes from **[Pibby: Apocalypse](https://gamebanana.com/wips/73842)** by the Pibby: Apocalypse Team, licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- The full team list is in [CREDITS.md](CREDITS.md).

This is a free, non-commercial fan project.
