"""
Pibby Glitch Cursor installer: a small GUI to install, uninstall, back up and restore
mouse cursors on Windows and Linux.

Windows: installs the 17 .ani pointers per user (no admin), sets them in
         HKCU\\Control Panel\\Cursors and applies them immediately.
Linux:   installs the Xcursor theme to ~/.icons and selects it for GNOME, Cinnamon,
         MATE, KDE Plasma, Xfce and plain X11 (~/.icons/default).

Backups store the current cursor settings *and copies of the cursor files they use*,
so they can be restored even if the original cursor files were deleted later.

Credits: based on the "Pibby Apocalypse Cursor Recreation Script" by jarekboho
(https://gamebanana.com/tools/15314). Cursor art from Pibby: Apocalypse by the Pibby: Apocalypse
Team (https://gamebanana.com/wips/73842), licensed CC BY-NC 4.0. Full list: CREDITS.md.

Testing hooks (never needed by users):
  PIBBY_TEST_ROOT   - use this folder instead of %LOCALAPPDATA% / $HOME
  PIBBY_TEST_REGKEY - use this HKCU key instead of Control Panel\\Cursors
  PIBBY_NO_APPLY    - don't broadcast cursor changes / run desktop commands
"""
import json
import os
import shutil
import subprocess
import sys
import tarfile
import threading
import time
from pathlib import Path

APP_NAME = "Pibby Glitch Cursor"
VERSION = "1.1.1"  # the one place to change it: the builds and release check read it from here
import credits  # who made what: shown in the footer and the Credits window
THEME = "PibbyGlitchCursor"
IS_WINDOWS = sys.platform == "win32"


def resource(*parts):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def payload(*parts):
    """Cursor files bundled into the app (or ./dist when run from source)."""
    p = resource("payload", *parts)
    return p if p.exists() else resource("dist", *parts)


# =============================================================== Windows ===
class WindowsCursors:
    ROLES = ["Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen", "No",
             "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand", "Pin", "Person"]
    DEFAULTS = {  # the "Windows Default" scheme
        "Arrow": "aero_arrow.cur", "Help": "aero_helpsel.cur", "AppStarting": "aero_working.ani",
        "Wait": "aero_busy.ani", "Crosshair": "", "IBeam": "", "NWPen": "aero_pen.cur",
        "No": "aero_unavail.cur", "SizeNS": "aero_ns.cur", "SizeWE": "aero_ew.cur",
        "SizeNWSE": "aero_nwse.cur", "SizeNESW": "aero_nesw.cur", "SizeAll": "aero_move.cur",
        "UpArrow": "aero_up.cur", "Hand": "aero_link.cur", "Pin": "aero_pin.cur", "Person": "aero_person.cur",
    }

    def __init__(self):
        import winreg
        self.reg = winreg
        root = Path(os.environ.get("PIBBY_TEST_ROOT") or os.environ["LOCALAPPDATA"])
        self.install_dir = root / "Cursors" / THEME
        self.backup_dir = root / THEME / "backup"
        self.key = os.environ.get("PIBBY_TEST_REGKEY", r"Control Panel\Cursors")
        self.sysdir = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Cursors"

    # ---- registry helpers
    def _open(self, sub="", write=False):
        path = self.key + ("\\" + sub if sub else "")
        if write:
            return self.reg.CreateKeyEx(self.reg.HKEY_CURRENT_USER, path, 0, self.reg.KEY_ALL_ACCESS)
        return self.reg.OpenKey(self.reg.HKEY_CURRENT_USER, path, 0, self.reg.KEY_READ)

    def _values(self, sub=""):
        out = {}
        try:
            with self._open(sub) as k:
                i = 0
                while True:
                    try:
                        name, data, typ = self.reg.EnumValue(k, i)
                    except OSError:
                        break
                    out[name] = (data, typ)
                    i += 1
        except FileNotFoundError:
            pass
        return out

    def _set(self, name, value, typ=None, sub=""):
        with self._open(sub, write=True) as k:
            self.reg.SetValueEx(k, name, 0, typ if typ is not None else self.reg.REG_EXPAND_SZ, value)

    def _delete(self, name, sub=""):
        try:
            with self._open(sub, write=True) as k:
                self.reg.DeleteValue(k, name)
        except FileNotFoundError:
            pass

    def _apply(self):
        if os.environ.get("PIBBY_NO_APPLY") or os.environ.get("PIBBY_TEST_REGKEY"):
            return
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(0x57, 0, None, 0x2)  # SPI_SETCURSORS, SPIF_SENDCHANGE

    def _file(self, role):
        return self.install_dir / (f"{THEME}.ani" if role == "Arrow" else f"{THEME}-{role}.ani")

    # ---- state
    LABELS = {"Arrow": "Normal select", "Help": "Help select", "AppStarting": "Working in background",
              "Wait": "Busy", "Crosshair": "Precision select", "IBeam": "Text select",
              "NWPen": "Handwriting", "No": "Unavailable", "SizeNS": "Vertical resize",
              "SizeWE": "Horizontal resize", "SizeNWSE": "Diagonal resize 1",
              "SizeNESW": "Diagonal resize 2", "SizeAll": "Move", "UpArrow": "Alternate select",
              "Hand": "Link select", "Pin": "Location select", "Person": "Person select"}

    def _norm(self, role, value):
        """Comparable form of a pointer path; empty means the built-in default pointer."""
        v = os.path.expandvars(value or "").strip()
        if not v:
            v = str(self.sysdir / self.DEFAULTS[role]) if self.DEFAULTS[role] else ""
        return os.path.normcase(os.path.normpath(v)) if v else ""

    def _system_schemes(self):
        out = {}
        try:
            k = self.reg.OpenKey(self.reg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Control Panel\Cursors\Schemes")
        except OSError:
            return out
        with k:
            i = 0
            while True:
                try:
                    name, data, _ = self.reg.EnumValue(k, i)
                except OSError:
                    break
                # "Windows Aero" is what the Pointers dialog shows as "Windows Default"
                out["Windows Default" if name == "Windows Aero" else name] = data
                i += 1
        return out

    def detect(self):
        """Work out which cursor set is in use: where each pointer comes from, which
        known scheme it matches, which folder/pack custom pointers live in, missing files."""
        vals = self._values()
        scheme_name = str(vals.get("", ("",))[0])
        ours = os.path.normcase(str(self.install_dir))
        sysdir = os.path.normcase(str(self.sysdir))
        access = os.path.normcase(str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Cursors"))
        roles, current = [], {}
        for r in self.ROLES:
            raw = str(vals.get(r, ("",))[0])
            n = self._norm(r, raw)
            current[r] = n
            if not raw.strip():
                origin = "Windows (built-in default)"
            elif n.startswith(ours):
                origin = "Pibby Glitch Cursor"
            elif n.startswith(sysdir):
                origin = "Windows"
            elif access and n.startswith(access):
                origin = "Windows pointer style"
            else:
                origin = "Custom"
            exists = not n or Path(n).is_file()
            roles.append({"role": r, "label": self.LABELS[r], "file": raw or "(default)",
                          "origin": origin, "exists": exists})
        counts = {}
        for x in roles:
            counts[x["origin"]] = counts.get(x["origin"], 0) + 1
        missing = [x["label"] for x in roles if not x["exists"]]

        # which known scheme matches best (user schemes + Windows' built-in ones)
        best, best_score = None, 0
        schemes = {**self._system_schemes(), **{k: v[0] for k, v in self._values("Schemes").items()}}
        for name, data in schemes.items():
            if not isinstance(data, str):
                continue
            parts = data.split(",")
            score = sum(1 for i, r in enumerate(self.ROLES)
                        if self._norm(r, parts[i] if i < len(parts) else "") == current[r])
            if score > best_score:
                best, best_score = name, score

        # original spelling (not the lower-cased comparison form) so pack names keep their case
        custom_files = [Path(os.path.normpath(os.path.expandvars(x["file"])))
                        for x in roles if x["origin"] == "Custom"]
        source, pack = "", ""
        if custom_files:
            try:
                source = os.path.commonpath([str(p.parent) for p in custom_files])
            except ValueError:
                source = str(custom_files[0].parent)
            folder = Path(source)
            pack = folder.parent.name if folder.name.lower() in ("cursors", "cursor") else folder.name

        n_ours, n_custom = counts.get("Pibby Glitch Cursor", 0), counts.get("Custom", 0)
        total = len(self.ROLES)
        if n_ours == total:
            kind, name = "pibby", "Pibby Glitch Cursor"
        elif n_ours:
            kind, name = "mixed", "Pibby Glitch Cursor (partly)"
        elif n_custom:
            kind = "custom"
            name = (scheme_name if scheme_name and scheme_name == best and best_score == total
                    else best if best_score == total else scheme_name or pack or "Custom cursors")
        elif counts.get("Windows pointer style"):
            kind, name = "accessibility", "Windows pointer style (Accessibility)"
        else:
            kind = "windows"
            name = best if best and best_score == total else scheme_name or "Windows Default"
        modified = bool(best) and best_score < total and kind in ("custom", "windows") and \
            scheme_name and scheme_name == best
        size = vals.get("CursorBaseSize", (32,))[0]
        parts = []
        if kind == "custom":
            parts.append(f"Custom set, {n_custom}/{total} pointers"
                         + (f" from \"{pack}\"" if pack else ""))
        elif kind == "mixed":
            parts.append(f"{n_ours}/{total} pointers are Pibby, the rest are "
                         + ("custom" if n_custom else "Windows"))
        elif kind == "windows":
            parts.append("Built-in Windows cursors")
        elif kind == "accessibility":
            parts.append("Recoloured or resized by Windows accessibility settings")
        else:
            parts.append(f"All {total} pointers installed")
        if modified:
            parts.append(f"edited from \"{best}\"")
        if isinstance(size, int) and size != 32:
            parts.append(f"size {size}px")
        if missing:
            parts.append(f"{len(missing)} file(s) missing")
        return {"name": name, "kind": kind, "summary": ", ".join(parts), "source": source,
                "roles": roles, "missing": missing}

    def is_installed(self):
        arrow = str(self._values().get("Arrow", ("",))[0])
        return str(self.install_dir).lower() in os.path.expandvars(arrow).lower()

    def current_name(self):
        return self.detect()["name"]

    def has_custom(self):
        """True if the current cursors are anything other than stock Windows or ours."""
        return self.detect()["kind"] in ("custom", "mixed", "accessibility")

    def backup_info(self):
        f = self.backup_dir / "backup.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    # ---- actions
    def backup(self):
        values = self._values()
        scheme_name = str(values.get("", ("",))[0])
        scheme = self._values("Schemes").get(scheme_name) if scheme_name else None
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        (self.backup_dir / "files").mkdir(parents=True)
        files = {}
        for name, (data, typ) in values.items():
            if not isinstance(data, str) or not data:
                continue
            src = Path(os.path.expandvars(data))
            key = str(src).lower()
            if key in files or not src.is_file() or str(self.install_dir).lower() in key:
                continue
            dest = f"{len(files):02d}_{src.name}"
            shutil.copy2(src, self.backup_dir / "files" / dest)
            files[key] = {"original": str(src), "copy": dest}
        info = {
            "platform": "windows",
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "name": scheme_name or "Windows Default",
            "values": {n: [d, t] for n, (d, t) in values.items()},
            "scheme": [scheme_name, scheme[0], scheme[1]] if scheme else None,
            "files": list(files.values()),
        }
        (self.backup_dir / "backup.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
        return info

    def install(self):
        self.install_dir.mkdir(parents=True, exist_ok=True)
        for role in self.ROLES:
            shutil.copyfile(payload("windows", self._file(role).name), self._file(role))
        for role in self.ROLES:
            self._set(role, str(self._file(role)))
        self._set(THEME, ",".join(str(self._file(r)) for r in self.ROLES), sub="Schemes")
        self._set("", THEME, self.reg.REG_SZ)
        self._set("Scheme Source", 1, self.reg.REG_DWORD)
        self._apply()

    def _remove_ours(self):
        self._delete(THEME, sub="Schemes")
        shutil.rmtree(self.install_dir, ignore_errors=True)

    def uninstall(self):
        for role in self.ROLES:
            f = self.DEFAULTS[role]
            self._set(role, f"%SystemRoot%\\cursors\\{f}" if f and (self.sysdir / f).exists() else "")
        self._set("", "Windows Default", self.reg.REG_SZ)
        self._set("Scheme Source", 2, self.reg.REG_DWORD)
        self._apply()
        self._remove_ours()

    def restore(self):
        info = self.backup_info()
        if not info:
            raise RuntimeError("No backup found.")
        redirect = {}
        for f in info["files"]:
            orig, copy = Path(f["original"]), self.backup_dir / "files" / f["copy"]
            if not orig.exists():
                try:
                    orig.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(copy, orig)
                except OSError:
                    redirect[str(orig).lower()] = str(copy)  # can't write there: use the backup copy
        for name, (data, typ) in info["values"].items():
            if isinstance(data, str) and data:
                data = redirect.get(os.path.expandvars(data).lower(), data)
            self._set(name, data, typ)
        if info["scheme"]:
            name, data, typ = info["scheme"]
            if isinstance(data, str):
                data = ",".join(redirect.get(os.path.expandvars(p).lower(), p) for p in data.split(","))
            self._set(name, data, typ, sub="Schemes")
        self._apply()
        if info["name"] != THEME:
            self._remove_ours()


# ================================================================= Linux ===
class LinuxCursors:
    GSETTINGS = [("org.gnome.desktop.interface", "cursor-theme"),
                 ("org.cinnamon.desktop.interface", "cursor-theme"),
                 ("org.mate.peripherals-mouse", "cursor-theme")]
    STOCK = {"", "default", "Adwaita", "breeze_cursors", "Breeze", "Breeze_Snow", "DMZ-White",
             "DMZ-Black", "Yaru", "Bibata-Modern-Classic", "Pop", "elementary", "whiteglass", "redglass"}

    def __init__(self):
        self.home = Path(os.environ.get("PIBBY_TEST_ROOT") or Path.home())
        self.icons = self.home / ".icons"
        self.install_dir = self.icons / THEME
        self.default_index = self.icons / "default" / "index.theme"
        data = Path(os.environ.get("XDG_DATA_HOME") or self.home / ".local" / "share")
        if os.environ.get("PIBBY_TEST_ROOT"):
            data = self.home / ".local" / "share"
        self.user_icon_dirs = [self.icons, data / "icons"]
        self.backup_dir = data / THEME / "backup"
        self.kde_rc = self.home / ".config" / "kcminputrc"

    def _run(self, *cmd):
        if os.environ.get("PIBBY_NO_APPLY") or not shutil.which(cmd[0]):
            return None
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return r.stdout.strip() if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    # ---- read current settings from every desktop we know
    def _settings(self):
        s = {"gsettings": {}, "xfce": None, "kde": None,
             "default_index": self.default_index.read_text() if self.default_index.is_file() else None}
        for schema, key in self.GSETTINGS:
            v = self._run("gsettings", "get", schema, key)
            if v is not None:
                s["gsettings"][schema] = v.strip("'\"")
        s["xfce"] = self._run("xfconf-query", "-c", "xsettings", "-p", "/Gtk/CursorThemeName")
        if self.kde_rc.is_file():
            for line in self.kde_rc.read_text(errors="ignore").splitlines():
                if line.strip().lower().startswith("cursortheme="):
                    s["kde"] = line.split("=", 1)[1].strip()
        return s

    def _theme_from(self, s):
        for v in list(s["gsettings"].values()) + [s["kde"], s["xfce"]]:
            if v:
                return v
        for line in (s["default_index"] or "").splitlines():
            if line.strip().startswith("Inherits="):
                return line.split("=", 1)[1].strip().split(",")[0]
        return ""

    SYSTEM_ICON_DIRS = [Path("/usr/local/share/icons"), Path("/usr/share/icons"), Path("/usr/share/pixmaps")]
    KEY_CURSORS = [("default", "Normal select"), ("text", "Text select"), ("pointer", "Link select"),
                   ("wait", "Busy"), ("progress", "Working in background"), ("help", "Help select"),
                   ("crosshair", "Precision select"), ("not-allowed", "Unavailable"), ("move", "Move"),
                   ("ns-resize", "Vertical resize"), ("ew-resize", "Horizontal resize"),
                   ("nwse-resize", "Diagonal resize 1"), ("nesw-resize", "Diagonal resize 2"),
                   ("pencil", "Handwriting"), ("up-arrow", "Alternate select")]
    LEGACY = {"default": "left_ptr", "text": "xterm", "pointer": "hand2", "wait": "watch",
              "progress": "left_ptr_watch", "help": "question_arrow", "crosshair": "crosshair",
              "not-allowed": "crossed_circle", "move": "fleur", "ns-resize": "sb_v_double_arrow",
              "ew-resize": "sb_h_double_arrow", "nwse-resize": "bd_double_arrow",
              "nesw-resize": "fd_double_arrow", "pencil": "pencil", "up-arrow": "sb_up_arrow"}

    def _find_theme(self, name, depth=0):
        """Folder holding `name`'s cursors, following Inherits= (e.g. the 'default' theme)."""
        if not name or depth > 5:
            return None, None
        for d in self.user_icon_dirs + self.SYSTEM_ICON_DIRS:
            t = d / name
            if (t / "cursors").is_dir():
                return t, name
        for d in self.user_icon_dirs + self.SYSTEM_ICON_DIRS:
            idx = d / name / "index.theme"
            if idx.is_file():
                for line in idx.read_text(errors="ignore").splitlines():
                    if line.strip().startswith("Inherits="):
                        for parent in line.split("=", 1)[1].split(","):
                            found = self._find_theme(parent.strip(), depth + 1)
                            if found[0]:
                                return found
        return None, None

    def detect(self):
        s = self._settings()
        name = self._theme_from(s)
        reported = {f"{schema.split('.')[1].title()} settings": v for schema, v in s["gsettings"].items() if v}
        if s["kde"]:
            reported["KDE Plasma"] = s["kde"]
        if s["xfce"]:
            reported["Xfce"] = s["xfce"]
        folder, real = self._find_theme(name or "default")
        display = real or name or "system default"
        if folder and (folder / "index.theme").is_file():
            for line in (folder / "index.theme").read_text(errors="ignore").splitlines():
                if line.strip().startswith("Name="):
                    display = line.split("=", 1)[1].strip() or display
                    break
        user = folder is not None and any(str(folder).startswith(str(d)) for d in self.user_icon_dirs)
        roles = []
        for cur, label in self.KEY_CURSORS:
            f = None
            if folder:
                for n in (cur, self.LEGACY.get(cur, cur)):
                    if (folder / "cursors" / n).exists():
                        f = folder / "cursors" / n
                        break
            roles.append({"role": cur, "label": label, "file": str(f) if f else "(falls back to another theme)",
                          "origin": display if f else "Fallback", "exists": True})
        covered = sum(1 for x in roles if x["origin"] != "Fallback")
        if name == THEME or real == THEME:
            kind = "pibby"
        elif folder is None:
            kind = "missing"
        elif user:
            kind = "custom"
        else:
            kind = "system"
        summary = {"pibby": f"{covered}/{len(roles)} main pointers installed",
                   "custom": f"Custom theme installed for your user, {covered}/{len(roles)} main pointers",
                   "system": f"System theme, {covered}/{len(roles)} main pointers",
                   "missing": "Selected theme isn't installed, so the desktop falls back to a default"}[kind]
        if len(set(reported.values())) > 1:
            summary += "; desktops disagree: " + ", ".join(f"{k}={v}" for k, v in reported.items())
        return {"name": display, "kind": kind, "summary": summary,
                "source": str(folder) if folder else "", "roles": roles, "missing": []}

    def current_name(self):
        return self.detect()["name"]

    def is_installed(self):
        return self.install_dir.is_dir() and self._theme_from(self._settings()) == THEME

    def has_custom(self):
        d = self.detect()
        return d["kind"] == "custom" or (d["kind"] == "system" and self._theme_from(self._settings()) not in self.STOCK)

    def backup_info(self):
        f = self.backup_dir / "backup.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def _apply_theme(self, name):
        for schema, key in self.GSETTINGS:
            self._run("gsettings", "set", schema, key, name)
        self._run("xfconf-query", "-c", "xsettings", "-p", "/Gtk/CursorThemeName", "-s", name)
        self._run("plasma-apply-cursortheme", name)

    # ---- actions
    def backup(self):
        s = self._settings()
        name = self._theme_from(s)
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        (self.backup_dir / "themes").mkdir(parents=True)
        copied = []
        for d in self.user_icon_dirs:  # user-installed themes could get deleted: keep a copy
            src = d / name
            if name and name != THEME and (src / "cursors").is_dir():
                shutil.copytree(src, self.backup_dir / "themes" / name, symlinks=True)
                copied.append({"original": str(src), "copy": name})
                break
        info = {"platform": "linux", "created": time.strftime("%Y-%m-%d %H:%M"),
                "name": name or "system default", "settings": s, "themes": copied}
        (self.backup_dir / "backup.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
        return info

    def install(self):
        shutil.rmtree(self.install_dir, ignore_errors=True)
        self.icons.mkdir(parents=True, exist_ok=True)
        with tarfile.open(payload("linux", f"{THEME}.tar.gz")) as t:
            if hasattr(tarfile, "data_filter"):
                t.extractall(self.icons, filter="data")
            else:
                t.extractall(self.icons)
        self.default_index.parent.mkdir(parents=True, exist_ok=True)
        self.default_index.write_text(f"[Icon Theme]\nInherits={THEME}\n")
        self._apply_theme(THEME)

    def uninstall(self):
        if self.default_index.is_file() and f"Inherits={THEME}" in self.default_index.read_text():
            self.default_index.unlink()
        for schema, key in self.GSETTINGS:
            self._run("gsettings", "reset", schema, key)
        self._run("xfconf-query", "-c", "xsettings", "-p", "/Gtk/CursorThemeName", "-s", "Adwaita")
        self._run("plasma-apply-cursortheme", "breeze_cursors")
        shutil.rmtree(self.install_dir, ignore_errors=True)

    def restore(self):
        info = self.backup_info()
        if not info:
            raise RuntimeError("No backup found.")
        for t in info["themes"]:
            dest = Path(t["original"])
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(self.backup_dir / "themes" / t["copy"], dest, symlinks=True)
        s = info["settings"]
        if s["default_index"] is None:
            if self.default_index.is_file():
                self.default_index.unlink()
        else:
            self.default_index.parent.mkdir(parents=True, exist_ok=True)
            self.default_index.write_text(s["default_index"])
        for schema, key in self.GSETTINGS:
            if schema in s["gsettings"]:
                self._run("gsettings", "set", schema, key, s["gsettings"][schema])
        if s["xfce"]:
            self._run("xfconf-query", "-c", "xsettings", "-p", "/Gtk/CursorThemeName", "-s", s["xfce"])
        if s["kde"]:
            self._run("plasma-apply-cursortheme", s["kde"])
        if info["name"] != THEME:
            shutil.rmtree(self.install_dir, ignore_errors=True)


def backend():
    return WindowsCursors() if IS_WINDOWS else LinuxCursors()


# =================================================================== GUI ===
def run_gui():
    import tkinter as tk
    from tkinter import messagebox, ttk

    sysc = backend()
    root = tk.Tk()
    root.title(f"{APP_NAME} Installer v{VERSION}")
    root.resizable(False, False)
    BG, FG, DIM, ACCENT = "#14191b", "#e8ecef", "#8b979e", "#b4bfcb"
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TButton", padding=(14, 7), background="#2a3236", foreground=FG,
                    bordercolor="#3a4549", focuscolor="#2a3236")
    style.map("TButton", background=[("disabled", "#1c2224"), ("active", "#38434a")],
              foreground=[("disabled", "#55626a")])
    style.configure("Accent.TButton", background=ACCENT, foreground="#101416")
    style.map("Accent.TButton", background=[("active", "#ffffff"), ("disabled", "#1c2224")])
    style.configure("Treeview", background="#1c2224", fieldbackground="#1c2224", foreground=FG,
                    bordercolor="#3a4549", rowheight=22)
    style.configure("Treeview.Heading", background="#2a3236", foreground=FG, bordercolor="#3a4549")
    style.map("Treeview.Heading", background=[("active", "#38434a")])
    style.configure("TCheckbutton", background=BG, foreground=FG)
    style.map("TCheckbutton", background=[("active", BG)])

    # ---- optional glitch effect on every app window (off by default; the choice is saved)
    import random
    GLITCH_BARS = ("#c878c8", "#ff00ff", "#00ffff", "#2020ff", "#000000", "#ffffff", "#0f1314")
    GLITCH_TEXT = ("#ff00ff", "#00ffff", "#4040ff")
    GLITCH_CHARS = "▓▒░█▚▞#@%&$?!_"
    settings_file = sysc.backup_dir.parent / "settings.json"

    def load_settings():
        try:
            return json.loads(settings_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_settings(**changes):
        s = {**load_settings(), **changes}
        try:
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings_file.write_text(json.dumps(s, indent=1), encoding="utf-8")
        except OSError:
            pass  # can't save: the box still works for this session

    glitch_on = tk.BooleanVar(value=bool(load_settings().get("glitch_windows")))
    gstate = {}  # window -> {"bars", "job", "title", "fg", "text"}

    def glitch_widgets(w):
        """Text widgets in this window (not in its child windows, which glitch on their own)."""
        for c in w.winfo_children():
            if isinstance(c, tk.Toplevel):
                continue
            if isinstance(c, (tk.Label, ttk.Button, ttk.Checkbutton)):
                yield c
            yield from glitch_widgets(c)

    def scramble(text):
        t = list(text)
        spots = [i for i, ch in enumerate(t) if not ch.isspace()]
        for i in random.sample(spots, min(len(spots), random.randint(1, 3))):
            t[i] = random.choice(GLITCH_CHARS)
        return "".join(t)

    def glitch_undo_text(st):
        """Put back the colours and text the last step changed. Text the app updated in the
        meantime (e.g. a new detection result) is left as the app set it."""
        for w, fg in st["fg"].items():
            if w.winfo_exists():
                w.configure(fg=fg)
        for w, (orig, scrambled) in st["text"].items():
            if w.winfo_exists() and str(w.cget("text")) == scrambled:
                w.configure(text=orig)
        st["fg"], st["text"] = {}, {}

    def glitch_clear(win):
        st = gstate.get(win)
        if not st:
            return
        try:
            for bar in st["bars"]:
                bar.place_forget()
            glitch_undo_text(st)
            if st["title"] is not None:
                win.title(st["title"])
                win.pack_propagate(True)
        except tk.TclError:
            pass
        st["title"] = None

    def glitch_schedule(win, delay=None):
        st = gstate.get(win)
        if st and not st["job"] and glitch_on.get():
            st["job"] = root.after(delay if delay is not None else random.randint(350, 2200),
                                   lambda: glitch_burst(win, random.randint(2, 6)))

    def glitch_burst(win, steps):
        """One short burst: a few 30-70 ms steps of corrupted bars, text and title."""
        st = gstate.get(win)
        if not st:
            return
        st["job"] = None
        if not glitch_on.get() or steps <= 0:
            glitch_clear(win)
            glitch_schedule(win)
            return
        try:
            if st["title"] is None:
                st["title"] = win.title()
                win.pack_propagate(False)  # scrambled text mustn't make the window jump in size
            glitch_undo_text(st)
            w, h = max(win.winfo_width(), 2), max(win.winfo_height(), 2)
            for bar in st["bars"]:
                if random.random() < 0.4:
                    bar.place_forget()
                    continue
                if random.random() < 0.5:  # thin tear across the whole window
                    bw, bh, x = w, random.randint(1, 4), 0
                else:  # chunky displaced block
                    bw, bh = random.randint(w // 10 + 1, w // 2 + 1), random.randint(4, h // 6 + 4)
                    x = random.randint(-bw // 2, w - bw // 2)
                bar.configure(bg=random.choice(GLITCH_BARS))
                bar.place(x=x, y=random.randint(0, max(0, h - bh)), width=bw, height=bh)
                bar.lift()
            for wid in glitch_widgets(win):
                if isinstance(wid, tk.Label) and random.random() < 0.25:
                    st["fg"][wid] = wid.cget("fg")
                    wid.configure(fg=random.choice(GLITCH_TEXT))
                text = str(wid.cget("text"))
                if text.strip() and random.random() < 0.3:
                    scrambled = scramble(text)
                    st["text"][wid] = (text, scrambled)
                    wid.configure(text=scrambled)
            win.title(scramble(st["title"]) if st["title"].strip() else st["title"])
        except tk.TclError:  # window is closing
            return
        st["job"] = root.after(random.randint(30, 70), lambda: glitch_burst(win, steps - 1))

    def glitchable(win):
        """Register a window so the glitch effect (when switched on) runs on it too."""
        gstate[win] = {"bars": [tk.Frame(win, bd=0, highlightthickness=0) for _ in range(7)],
                       "job": None, "title": None, "fg": {}, "text": {}}

        def forget(e):
            if e.widget is win and win in gstate:
                st = gstate.pop(win)
                if st["job"]:
                    root.after_cancel(st["job"])
        win.bind("<Destroy>", forget, add="+")
        glitch_schedule(win, 250)
        return win

    def glitch_toggle():
        save_settings(glitch_windows=glitch_on.get())
        for win, st in list(gstate.items()):
            if st["job"]:
                root.after_cancel(st["job"])
                st["job"] = None
            glitch_clear(win)
            glitch_schedule(win, 150)

    glitchable(root)

    # animated preview of the actual cursor frames
    frames = []
    frame_dir = resource("payload", "preview")
    if not frame_dir.exists():
        frame_dir = resource("images", "cursor")
    for i in range(1, 11):
        f = frame_dir / f"mouse ({i}).png"
        if f.exists():
            frames.append(tk.PhotoImage(file=str(f)).zoom(4, 4))
    top = tk.Frame(root, bg=BG)
    top.pack(padx=22, pady=(20, 8), fill="x")
    canvas = tk.Label(top, bg="#c878c8", width=24 * 4 + 16, height=32 * 4 + 16, bd=0)
    canvas.pack(side="left")
    if frames:
        root.iconphoto(True, frames[6])
        state = {"i": 0}

        def tick():
            canvas.configure(image=frames[state["i"]])
            state["i"] = (state["i"] + 1) % len(frames)
            root.after(16, tick)  # one frame per game update at 60 fps, like cursor.lua
        tick()
    info = tk.Frame(top, bg=BG)
    info.pack(side="left", padx=(18, 0), fill="both")
    name_row = tk.Frame(info, bg=BG)
    name_row.pack(anchor="w")
    tk.Label(name_row, text=APP_NAME, bg=BG, fg=FG, font=("Segoe UI" if IS_WINDOWS else "Sans", 16, "bold")
             ).pack(side="left")
    tk.Label(name_row, text=f"v{VERSION}", bg=BG, fg=DIM, font=("Segoe UI" if IS_WINDOWS else "Sans", 9)
             ).pack(side="left", anchor="s", padx=(6, 0), pady=(0, 4))
    tk.Label(info, text="Fully glitched animated pointer set", bg=BG, fg=DIM).pack(anchor="w")
    tk.Label(info, text="DETECTED", bg=BG, fg=DIM, font=("Segoe UI" if IS_WINDOWS else "Sans", 8, "bold")
             ).pack(anchor="w", pady=(12, 0))
    status = tk.Label(info, bg=BG, fg=FG, justify="left", wraplength=290,
                      font=("Segoe UI" if IS_WINDOWS else "Sans", 11, "bold"))
    status.pack(anchor="w")
    summary = tk.Label(info, bg=BG, fg=DIM, justify="left", wraplength=290)
    summary.pack(anchor="w")
    details_btn = tk.Label(info, text="Details…", bg=BG, fg=ACCENT, cursor="hand2",
                           font=("Segoe UI" if IS_WINDOWS else "Sans", 9, "underline"))
    details_btn.pack(anchor="w", pady=(2, 0))
    backup_lbl = tk.Label(info, bg=BG, fg=DIM, justify="left", wraplength=290)
    backup_lbl.pack(anchor="w", pady=(8, 0))
    detected = {"d": None, "sig": None, "gen": 0}

    def show_details(_event=None):
        d = detected["d"] or sysc.detect()
        win = tk.Toplevel(root)
        win.title(f"Detected cursors: {d['name']}")
        win.configure(bg=BG)
        glitchable(win)
        tk.Label(win, text=d["name"], bg=BG, fg=FG, font=("Segoe UI" if IS_WINDOWS else "Sans", 12, "bold")
                 ).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Label(win, text=d["summary"] + (f"\nFolder: {d['source']}" if d["source"] else ""),
                 bg=BG, fg=DIM, justify="left", wraplength=640).pack(anchor="w", padx=14)
        tree = ttk.Treeview(win, columns=("pointer", "from", "file"), show="headings", height=len(d["roles"]))
        for col, text, w in (("pointer", "Pointer", 150), ("from", "Comes from", 170), ("file", "File", 420)):
            tree.heading(col, text=text)
            tree.column(col, width=w, anchor="w")
        src = os.path.normcase(d["source"]) if d["source"] else ""
        for x in d["roles"]:
            f = x["file"]
            full = os.path.normpath(os.path.expandvars(f)) if f and not f.startswith("(") else f
            if src and os.path.normcase(full).startswith(src + os.sep):
                f = full[len(src) + 1:]  # folder is shown above; keep rows short
            tree.insert("", "end", values=(x["label"], x["origin"] + ("" if x["exists"] else "  (FILE MISSING)"), f))
        tree.pack(padx=14, pady=12, fill="both", expand=True)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 12))
    details_btn.bind("<Button-1>", show_details)

    do_backup = tk.BooleanVar(value=sysc.has_custom())
    chk = ttk.Checkbutton(root, text="Back up my current cursors before installing", variable=do_backup)
    chk.pack(anchor="w", padx=22, pady=(6, 0))
    ttk.Checkbutton(root, text="Glitch effect on every window", variable=glitch_on,
                    command=glitch_toggle).pack(anchor="w", padx=22, pady=(4, 0))
    btns = tk.Frame(root, bg=BG)
    btns.pack(padx=22, pady=(12, 10), fill="x")

    # credits footer
    import webbrowser
    small = ("Segoe UI" if IS_WINDOWS else "Sans", 8)
    FOOT = "#0f1314"
    footer = tk.Frame(root, bg=FOOT)
    footer.pack(side="bottom", fill="x")

    def credit_line(parts, pady):
        """parts: (text, url or None, bold) pieces laid out on one line."""
        row = tk.Frame(footer, bg=FOOT)
        row.pack(anchor="w", padx=22, pady=pady)
        for text, target, bold in parts:
            style_ = small + (("bold",) if bold else ()) + (("underline",) if target else ())
            lbl = tk.Label(row, text=text, bg=FOOT, fg=ACCENT if target else DIM, font=style_,
                           cursor="hand2" if target else "", padx=1)
            lbl.pack(side="left")
            if callable(target):
                lbl.bind("<Button-1>", lambda e, t=target: t())
            elif target:
                lbl.bind("<Button-1>", lambda e, u=target: webbrowser.open(u))

    def show_credits():
        win = tk.Toplevel(root)
        win.title("Credits")
        win.configure(bg=BG)
        glitchable(win)
        s, m = credits.SCRIPT, credits.MOD
        tk.Label(win, text="Credits", bg=BG, fg=FG, font=("Segoe UI" if IS_WINDOWS else "Sans", 13, "bold")
                 ).pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(win, text=f"Based on the {s['title']} by {s['author']} ({s['role']}).\n"
                           f"Cursor art from {m['title']}, licensed {m['license']}.\n"
                           "Double-click a name to open their page.",
                 bg=BG, fg=DIM, justify="left").pack(anchor="w", padx=14)
        tree = ttk.Treeview(win, columns=("role",), height=18)
        tree.heading("#0", text="Name")
        tree.heading("role", text="Role")
        tree.column("#0", width=240)
        tree.column("role", width=440)
        urls = {}
        top = tree.insert("", "end", text=s["title"], open=True)
        urls[tree.insert(top, "end", text=s["author"], values=(s["role"],))] = s["author_url"]
        mod = tree.insert("", "end", text=f"{m['title']} Team", open=True)
        for group, people in credits.MOD_CREDITS:
            g = tree.insert(mod, "end", text=group, open=True)
            for name, role, url in people:
                urls[tree.insert(g, "end", text=name, values=(role,))] = url
        tree.bind("<Double-1>", lambda e: urls.get(tree.focus()) and webbrowser.open(urls[tree.focus()]))
        tree.pack(padx=14, pady=10, fill="both", expand=True)
        links = tk.Frame(win, bg=BG)
        links.pack(pady=(0, 12))
        ttk.Button(links, text="Script page", command=lambda: webbrowser.open(s["url"])).pack(side="left")
        ttk.Button(links, text=f"{m['title']} page", command=lambda: webbrowser.open(m["url"])
                   ).pack(side="left", padx=8)
        ttk.Button(links, text="Close", command=win.destroy).pack(side="left")

    s, m = credits.SCRIPT, credits.MOD
    credit_line([("Based on the", None, False), (s["title"], s["url"], False),
                 ("by", None, False), (s["author"], s["author_url"], True)], (8, 0))
    credit_line([("Cursor art from", None, False), (m["title"], m["url"], True),
                 ("by the Pibby: Apocalypse Team · CC BY-NC 4.0 ·", None, False),
                 ("Credits…", show_credits, True)], (0, 8))

    def snapshot():
        """What the window shows about the system. Slow-ish on Linux (runs gsettings)."""
        return sysc.is_installed(), sysc.backup_info(), sysc.detect()

    def refresh(snap=None):
        installed, b, d = snap or snapshot()
        detected["gen"] += 1  # results of checks started before this are now out of date
        detected["d"] = d
        detected["sig"] = (d["name"], d["summary"], installed, b["created"] if b else None)
        status.configure(text=d["name"])
        summary.configure(text=d["summary"])
        backup_lbl.configure(text=f"Backup: \"{b['name']}\" from {b['created']}" if b else "No backup yet.")
        install_btn.configure(text="Reinstall" if installed else "Install")
        uninstall_btn.state(["!disabled"] if installed else ["disabled"])
        restore_btn.state(["!disabled"] if b else ["disabled"])
        if installed:
            chk.state(["disabled"]); do_backup.set(False)
        else:
            chk.state(["!disabled"])

    def watch():
        """Re-detect every 2 s so changes made in system settings show up live. The check runs
        on a background thread so the animations never pause for it; only the result is
        applied here, on the window's own thread (tkinter isn't thread-safe)."""
        gen, box = detected["gen"], {}

        def work():
            try:
                snap = snapshot()
                box["result"] = (snap, sysc.has_custom())
            except Exception:
                box["result"] = None

        def collect():
            if "result" not in box:
                root.after(50, collect)
                return
            # skip results that a button action (which refreshes itself) has overtaken
            if box["result"] and gen == detected["gen"]:
                snap, custom = box["result"]
                installed, b, d = snap
                if (d["name"], d["summary"], installed, b["created"] if b else None) != detected["sig"]:
                    refresh(snap)
                    do_backup.set(custom and not installed)
            root.after(2000, watch)

        threading.Thread(target=work, daemon=True).start()
        root.after(50, collect)

    def guarded(fn):
        def wrapper():
            root.configure(cursor="watch"); root.update()
            try:
                fn()
            except Exception as e:  # show any failure instead of crashing silently
                messagebox.showerror(APP_NAME, f"Something went wrong:\n\n{e}")
            finally:
                root.configure(cursor=""); refresh()
        return wrapper

    @guarded
    def on_install():
        if do_backup.get() and not sysc.is_installed():
            old = sysc.backup_info()
            if old and not messagebox.askyesno(
                    APP_NAME, f"Replace your existing backup (\"{old['name']}\", {old['created']}) "
                              f"with your current cursors?"):
                return
            sysc.backup()
        sysc.install()
        messagebox.showinfo(APP_NAME, "Installed Successfully!"
                            + ("" if IS_WINDOWS else "\n\nLog out and back in if some apps still "
                                                     "show the old cursor."))

    @guarded
    def on_uninstall():
        if messagebox.askyesno(APP_NAME, "Remove the Pibby Glitch Cursor and switch to the "
                                         "standard system cursors?"
                               + ("\n\nYour backup is kept: use Restore to get your old "
                                  "cursors back." if sysc.backup_info() else "")):
            sysc.uninstall()

    @guarded
    def on_restore():
        b = sysc.backup_info()
        if messagebox.askyesno(APP_NAME, f"Restore \"{b['name']}\" from {b['created']}?"):
            sysc.restore()
            messagebox.showinfo(APP_NAME, "Your previous cursors are back.")

    install_btn = ttk.Button(btns, text="Install", style="Accent.TButton", command=on_install)
    install_btn.pack(side="left")
    uninstall_btn = ttk.Button(btns, text="Uninstall", command=on_uninstall)
    uninstall_btn.pack(side="left", padx=8)
    restore_btn = ttk.Button(btns, text="Restore backup", command=on_restore)
    restore_btn.pack(side="left")
    refresh()
    root.after(2000, watch)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
