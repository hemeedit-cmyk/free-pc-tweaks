"""
HEPESmenu.free - purple snow PC optimizer (Windows)

Run requirements.bat to install/check Python and launch the app.
Game logos: put PNG files in the "logos" folder next to this script
(fortnite.png, valorant.png, cs2.png, apex.png, lol.png, overwatch.png, gta5.png,
 cod.png, rocketleague.png, roblox.png, r6.png, minecraft.png).
"""
import base64
import ctypes
import math
import os
import queue
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import glob
import hashlib
import json
import secrets
from datetime import datetime, timedelta
import platform
import io
import tkinter as tk
import webbrowser
from collections import deque
from tkinter import messagebox

IS_WIN = sys.platform.startswith("win")
if IS_WIN:
    import winreg

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ------------------------------------------------------------------ theme
W, H = 1240, 760
BG_TOP = (25, 5, 55)
BG_BOT = (5, 10, 38)
CARD = "#1b1940"
BORDER = "#4a4590"
PURPLE = "#8f7bff"
PURPLE2 = "#cfc4ff"
DEEP = "#5846d8"
INPUT = "#14122e"
TEXT = "#f3f1ff"
MUTED = "#a29fcf"
GOOD = "#7cf0b6"
WARN = "#ffd98a"
NOWIN = 0x08000000  # CREATE_NO_WINDOW

APP_NAME = "HEPESmenu.free"
LICENSE_KEY = "982H-TUI2-GHFD-821W"
SUB_DAYS = 9999
LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")
LIC_FILE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "HEPESmenu", "license.dat")
ADMIN_LICENSE_FILE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "HEPESmenu", "generated_licenses.json")
ADMIN_PASSWORD = "Derpikuski14!!"

# License durations the generator can hand out (unit -> seconds).
DURATION_UNITS = {
    "Minutes": 60,
    "Hours": 3600,
    "Days": 86400,
    "Weeks": 7 * 86400,
    "Months (30 days)": 30 * 86400,
    "Years (365 days)": 365 * 86400,
}
LIFETIME = "Lifetime"
MAX_LICENSE_SECONDS = 36500 * 86400  # 100 years


def format_remaining(expires):
    """Human-readable time left until `expires` (None = never expires)."""
    if expires is None:
        return "Lifetime"
    secs = math.ceil((expires - datetime.now()).total_seconds())
    if secs <= 0:
        return "expired"
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d >= 1:
        return f"{d} day{'s' if d != 1 else ''} {h}h left"
    if h >= 1:
        return f"{h}h {m}min left"
    return f"{m}min {s}s left"
_UNIT_SECS = {"min": 60, "minute": 60, "hr": 3600, "hour": 3600, "day": 86400,
              "week": 7 * 86400, "month": 30 * 86400, "year": 365 * 86400}


def parse_duration(text):
    """'7 days', '12 hours', '2 weeks' -> seconds (None if it can't be understood)."""
    m = re.fullmatch(r"\s*(\d+)\s*([a-zA-Z]+?)s?\s*", text or "")
    if not m or m.group(2).lower() not in _UNIT_SECS:
        return None
    secs = int(m.group(1)) * _UNIT_SECS[m.group(2).lower()]
    return secs if 1 <= secs <= MAX_LICENSE_SECONDS else None


def fmt_seconds(secs):
    for name, size in (("year", 365 * 86400), ("month", 30 * 86400), ("week", 7 * 86400),
                       ("day", 86400), ("hour", 3600), ("minute", 60)):
        if secs % size == 0:
            n = secs // size
            return f"{n} {name}{'s' if n != 1 else ''}"
    return f"{secs} seconds"


def license_status(info, now=None):
    """-> (kind, text). kind: revoked / unused / active / lifetime / expired."""
    now = now or datetime.now()
    if info.get("revoked"):
        return "revoked", "Revoked"
    exp = info.get("expires")
    if exp is None:
        return ("unused", "Not used yet") if info.get("duration_seconds") else ("lifetime", "Lifetime")
    try:
        if now < datetime.fromisoformat(exp):
            return "active", "Active"
    except (TypeError, ValueError):
        pass
    return "expired", "Expired"


TALK = [
    "Hi! Welcome to HEPESmenu.free ✦",
    "Tip: restart your PC after Boost Everything!",
    "Pick your game and I'll give it top priority.",
    "Lower ping = happier games ✦",
    "Turn off V-Sync in-game for less input lag.",
    "Psst... try the Ultimate power plan.",
    "Cap your FPS just under your refresh rate.",
    "Clean temp files once in a while ✧",
    "Open the Apps tab to close what you don't need.",
    "Fewer background apps = more FPS ✦",
]

HIGH_PLAN = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
BALANCED_PLAN = "381b4222-f694-41f0-9685-ff5bb260df2e"
ULTIMATE_SRC = "e9a42b02-d5df-448d-aa00-03f14749eb61"
GUID_RE = r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"

GAMES = [
    dict(name="Fortnite", genre="Battle Royale", exes=["FortniteClient-Win64-Shipping.exe"],
         tip="In-game: try Performance mode, turn off V-Sync, cap FPS 2-3 under your monitor's refresh rate."),
    dict(name="Valorant", genre="Tactical FPS", exes=["VALORANT-Win64-Shipping.exe"],
         tip="In-game: turn on Multithreaded Rendering, enable NVIDIA Reflex if you have it, and turn V-Sync off."),
    dict(name="CS2", genre="Tactical FPS", exes=["cs2.exe"],
         tip="In-game: use exclusive fullscreen, V-Sync off, and enable NVIDIA Reflex Low Latency if available."),
    dict(name="Apex Legends", genre="Battle Royale", exes=["r5apex.exe", "r5apex_dx12.exe"],
         tip="In-game: set a frame cap just under your refresh rate and lower Texture Streaming Budget on low VRAM."),
    dict(name="League of Legends", genre="MOBA", exes=["League of Legends.exe"],
         tip="In-game: fullscreen, lower Character Quality + Shadows, and keep the FPS cap at your refresh rate."),
    dict(name="Overwatch 2", genre="Hero Shooter", exes=["Overwatch.exe"],
         tip="In-game: enable Reduce Buffering, turn off V-Sync, and drop Shadow + Local Reflections detail."),
    dict(name="GTA V", genre="Open World", exes=["GTA5.exe", "GTA5_Enhanced.exe"],
         tip="In-game: lower Grass Quality, Shadows and MSAA first - they cost the most FPS for the least visual gain."),
    dict(name="Call of Duty", genre="FPS", exes=["cod.exe"],
         tip="In-game: turn on Nvidia Reflex if available, disable V-Sync, and lower Shadow + Particle quality."),
    dict(name="Rocket League", genre="Sports", exes=["RocketLeague.exe"],
         tip="In-game: cap FPS at your refresh rate, turn on High Quality Shaders only if you have spare GPU."),
    dict(name="Roblox", genre="Sandbox", exes=["RobloxPlayerBeta.exe"],
         tip="In-game: set Graphics Quality to manual and lower it - Roblox is very CPU/GPU quality sensitive."),
    dict(name="Rainbow Six Siege", genre="Tactical FPS", exes=["RainbowSix.exe", "RainbowSix_Vulkan.exe"],
         tip="In-game: try the Vulkan renderer, turn V-Sync off, and use a stable frame cap."),
    dict(name="Minecraft (Java)", genre="Sandbox", exes=["javaw.exe"],
         tip="Note: this boosts javaw.exe, so any Java app gets the boost. Lower render distance for big FPS gains."),
]

META = {
    "Fortnite": ("fortnite", "FN"), "Valorant": ("valorant", "VAL"), "CS2": ("cs2", "CS2"),
    "Apex Legends": ("apex", "APEX"), "League of Legends": ("lol", "LoL"),
    "Overwatch 2": ("overwatch", "OW2"), "GTA V": ("gta5", "GTA V"), "Call of Duty": ("cod", "COD"),
    "Rocket League": ("rocketleague", "RL"), "Roblox": ("roblox", "RBLX"),
    "Rainbow Six Siege": ("r6", "R6"), "Minecraft (Java)": ("minecraft", "MC"),
}
for _g in GAMES:
    _g["slug"], _g["mono"] = META[_g["name"]]

DNS_SETS = {
    "auto": None,
    "cloudflare": ("1.1.1.1", "1.0.0.1"),
    "google": ("8.8.8.8", "8.8.4.4"),
    "quad9": ("9.9.9.9", "149.112.112.112"),
}


# ------------------------------------------------------------------ helpers
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run(cmd):
    """Run a command silently, return its text output."""
    try:
        r = subprocess.run(
            cmd, shell=isinstance(cmd, str), capture_output=True, text=True, errors="replace",
            creationflags=NOWIN if IS_WIN else 0, timeout=90,
        )
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"error: {e}"


def ps(script):
    return run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script])


def get_hw_info():
    """Read CPU / GPU / RAM / board / OS / disks. One PowerShell call, no extra installs."""
    keys = ("cpu", "cores", "gpu", "ram", "board", "os", "disk")
    info = {k: "unknown" for k in keys}
    if not IS_WIN:
        info["cpu"] = platform.processor() or platform.machine()
        info["os"] = platform.platform()
        return info
    script = "; ".join([
        "$ErrorActionPreference='SilentlyContinue'",
        "$c=Get-CimInstance Win32_Processor|Select-Object -First 1",
        "$g=@(Get-CimInstance Win32_VideoController)",
        "$b=Get-CimInstance Win32_BaseBoard",
        "$o=Get-CimInstance Win32_OperatingSystem",
        "$d=@(Get-CimInstance Win32_DiskDrive)",
        "$m=@(Get-CimInstance Win32_PhysicalMemory)",
        "'CPU|'+$c.Name.Trim()",
        "'CORES|'+$c.NumberOfCores+' cores / '+$c.NumberOfLogicalProcessors+' threads @ '+[math]::Round($c.MaxClockSpeed/1000,2)+' GHz'",
        "'GPU|'+(($g|ForEach-Object{$_.Name+'  (driver '+$_.DriverVersion+')'}) -join ' ;; ')",
        "'RAM|'+[math]::Round(($m|Measure-Object Capacity -Sum).Sum/1GB)+' GB  -  '+$m[0].Speed+' MHz  -  '+$m.Count+' stick(s)'",
        "'BOARD|'+$b.Manufacturer+' '+$b.Product",
        "'OS|'+$o.Caption+' (build '+$o.BuildNumber+')'",
        "'DISK|'+(($d|ForEach-Object{$_.Model+'  -  '+[math]::Round($_.Size/1GB)+' GB'}) -join ' ;; ')",
    ])
    out = ps(script)
    for line in out.splitlines():
        if "|" in line:
            k, v = line.split("|", 1)
            k = k.strip().lower()
            if k in info and v.strip():
                info[k] = v.strip().replace(" ;; ", "\n")
    return info


def reg_set(hive, path, name, value, kind=None):
    kind = winreg.REG_DWORD if kind is None else kind
    with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, name, 0, kind, value)


def reg_del(hive, path, name):
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
    except OSError:
        pass


def reg_get(hive, path, name, default=None):
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return default


def spi(action, ui=0, param=None, flags=3):
    try:
        p = ctypes.c_void_p(param) if isinstance(param, int) or param is None else param
        return ctypes.windll.user32.SystemParametersInfoW(action, ui, p, flags)
    except Exception:
        return 0


def key_hash():
    return hashlib.sha256(("HEPES|" + LICENSE_KEY).encode()).hexdigest()


def clear_license():
    try:
        os.remove(LIC_FILE)
    except OSError:
        pass


def ensure_pil():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "pillow"],
                       creationflags=NOWIN if IS_WIN else 0, timeout=180)
        import importlib
        importlib.invalidate_caches()
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def find_logo_file(slug):
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        p = os.path.join(LOGO_DIR, slug + ext)
        if os.path.isfile(p):
            return p
    return None


def load_logo(slug, box=38):
    """Returns a tk.PhotoImage: a clean WHITE silhouette with no background (needs Pillow),
    or None when the game has no logo file (a monogram is drawn instead)."""
    p = find_logo_file(slug)
    if not p:
        return None
    try:
        from PIL import Image, ImageChops
        im = Image.open(p).convert("RGBA")
        alpha = im.getchannel("A")
        if alpha.getextrema()[0] >= 250:  # flat background -> remove it
            bg = Image.new("RGB", im.size, im.getpixel((0, 0))[:3])
            diff = ImageChops.difference(im.convert("RGB"), bg).convert("L")
            alpha = diff.point(lambda v: min(255, v * 4))
        bb = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
        if bb:
            alpha = alpha.crop(bb)
        alpha.thumbnail((box, box), Image.LANCZOS)
        out = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
        out.putalpha(alpha)
        buf = io.BytesIO()
        out.save(buf, "PNG")
        return tk.PhotoImage(data=base64.b64encode(buf.getvalue()).decode())
    except ImportError:
        try:
            img = tk.PhotoImage(file=p)
            f = max(1, -(-max(img.width(), img.height()) // box))
            return img.subsample(f, f)
        except Exception:
            return None
    except Exception:
        return None


def star_pts(x, y, s):
    k = s * 0.3
    return [x, y - s, x + k, y - k, x + s, y, x + k, y + k, x, y + s, x - k, y + k, x - s, y, x - k, y - k]


def need_admin(log, what):
    if is_admin():
        return True
    log(f"! {what} needs Administrator - skipped.")
    return False


def set_live_priority(exe):
    name = exe[:-4] if exe.lower().endswith(".exe") else exe
    ps(f"Get-Process -Name '{name}' -ErrorAction SilentlyContinue | "
       f"ForEach-Object {{ $_.PriorityClass = 'High' }}")


class ANIMINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("iMinAnimate", ctypes.c_int)]


class MEMSTAT(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


# ------------------------------------------------------------------ tweaks
def tweak_network(log):
    log("Flushing DNS cache...")
    run("ipconfig /flushdns")
    if not need_admin(log, "Nagle / throttle tweaks"):
        return
    log("Disabling Nagle's algorithm on all adapters (lower ping)...")
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    count = 0
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                except OSError:
                    break
                i += 1
                try:
                    reg_set(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, "TcpAckFrequency", 1)
                    reg_set(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, "TCPNoDelay", 1)
                    reg_set(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, "TcpDelAckTicks", 0)
                    count += 1
                except OSError:
                    pass
    except OSError as e:
        log(f"! Could not open interfaces: {e}")
    log(f"  Applied to {count} adapter(s).")
    log("Removing network throttling, prioritizing games...")
    prof = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    try:
        hk = winreg.HKEY_LOCAL_MACHINE
        reg_set(hk, prof, "NetworkThrottlingIndex", 0xFFFFFFFF)
        reg_set(hk, prof, "SystemResponsiveness", 0)
        g = prof + r"\Tasks\Games"
        reg_set(hk, g, "GPU Priority", 8)
        reg_set(hk, g, "Priority", 6)
        reg_set(hk, g, "Scheduling Category", "High", winreg.REG_SZ)
        reg_set(hk, g, "SFIO Priority", "High", winreg.REG_SZ)
    except OSError as e:
        log(f"! Registry write failed: {e}")
    run("netsh int tcp set global autotuninglevel=normal")
    run("netsh int tcp set global rss=enabled")
    run("netsh int tcp set global initialRto=2000")   # retry lost connection attempts sooner
    run("netsh int tcp set heuristics disabled")      # stop Windows second-guessing TCP window scaling
    log("Ping tweaks done (restart makes them fully active).")


def ping_test(log):
    for name, host in (("Cloudflare", "1.1.1.1"), ("Google", "8.8.8.8"), ("Quad9", "9.9.9.9")):
        log(f"Pinging {name} ({host})...")
        out = run(f"ping -n 6 {host}")
        nums = re.findall(r"(\d+)\s*ms", out)
        log(f"  Average: {nums[-1]} ms" if nums else "  No reply (check your connection).")


def reset_network(log):
    log("Resetting Winsock + IP stack...")
    run("netsh winsock reset")
    run("netsh int ip reset")
    run("ipconfig /flushdns")
    log("Done. Restart your PC to finish the reset.")


def set_dns(log, key):
    servers = DNS_SETS[key]
    if not need_admin(log, "Changing DNS"):
        return
    if servers is None:
        log("Setting DNS back to automatic...")
        ps("Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object "
           "{ Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ResetServerAddresses }")
    else:
        log(f"Setting DNS to {key.title()} ({servers[0]})...")
        addr = ",".join(f"'{s}'" for s in servers)
        ps("Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object "
           f"{{ Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses ({addr}) }}")
    run("ipconfig /flushdns")
    log("DNS updated.")


def set_power(log, kind):
    if kind == "balanced":
        guid, label = BALANCED_PLAN, "Balanced"
    elif kind == "high":
        guid, label = HIGH_PLAN, "High Performance"
    else:
        label = "Ultimate Performance"
        m = re.search(r"(" + GUID_RE + r")\s+\(Ultimate", run("powercfg /list"), re.I)
        if m:
            guid = m.group(1)
        else:
            m = re.search(GUID_RE, run(f"powercfg -duplicatescheme {ULTIMATE_SRC}"))
            if m:
                guid = m.group(0)
            else:
                guid, label = HIGH_PLAN, "High Performance"
                log("Ultimate plan not available on this PC - using High Performance.")
    log(f"Activating {label} power plan...")
    run(f"powercfg /setactive {guid}")
    log("Power plan active.")


def tweak_gamemode(log, on=True):
    v = 1 if on else 0
    log("Turning Game Mode ON, background recording OFF..." if on
        else "Restoring Game Bar / recording defaults...")
    try:
        u = winreg.HKEY_CURRENT_USER
        reg_set(u, r"Software\Microsoft\GameBar", "AutoGameModeEnabled", 1)
        reg_set(u, r"Software\Microsoft\GameBar", "AllowAutoGameMode", 1)
        reg_set(u, r"System\GameConfigStore", "GameDVR_Enabled", v ^ 1 if on else 1)
        reg_set(u, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", v ^ 1 if on else 1)
    except OSError as e:
        log(f"! Registry write failed: {e}")
    log("Done.")


def visuals(log, perf=True):
    log("Switching Windows visuals to PERFORMANCE..." if perf else "Restoring Windows visuals...")
    try:
        u = winreg.HKEY_CURRENT_USER
        reg_set(u, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "EnableTransparency", 0 if perf else 1)
        reg_set(u, r"Control Panel\Desktop", "MenuShowDelay", "0" if perf else "400", winreg.REG_SZ)
        spi(0x1043, 0, 0 if perf else 1)   # client-area animations
        info = ANIMINFO(ctypes.sizeof(ANIMINFO), 0 if perf else 1)
        spi(0x0049, ctypes.sizeof(ANIMINFO), ctypes.byref(info))  # min/max animation
    except Exception as e:
        log(f"! Visual tweak failed: {e}")
    log("Done.")


def gpu_sched(log):
    if not need_admin(log, "GPU scheduling"):
        return
    try:
        reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 2)
        log("Hardware-accelerated GPU scheduling enabled (restart needed, needs a recent GPU).")
    except OSError as e:
        log(f"! Failed: {e}")


def mouse_accel(log, on):
    log("Restoring Windows mouse acceleration..." if on else "Turning OFF mouse acceleration...")
    vals = ("1", "6", "10") if on else ("0", "0", "0")
    try:
        m = r"Control Panel\Mouse"
        u = winreg.HKEY_CURRENT_USER
        reg_set(u, m, "MouseSpeed", vals[0], winreg.REG_SZ)
        reg_set(u, m, "MouseThreshold1", vals[1], winreg.REG_SZ)
        reg_set(u, m, "MouseThreshold2", vals[2], winreg.REG_SZ)
        arr = (ctypes.c_int * 3)(*[int(v) for v in vals])
        spi(0x0004, 0, arr)
    except Exception as e:
        log(f"! Mouse tweak failed: {e}")
    log("Done - 1:1 pointer movement." if not on else "Done.")


def mouse_drag(log, snappy):
    px = 2 if snappy else 4
    log(f"Drag now starts after {px}px" + (" (snappy)." if snappy else " (Windows default)."))
    try:
        u = winreg.HKEY_CURRENT_USER
        reg_set(u, r"Control Panel\Desktop", "DragWidth", str(px), winreg.REG_SZ)
        reg_set(u, r"Control Panel\Desktop", "DragHeight", str(px), winreg.REG_SZ)
        spi(76, px, None)
        spi(77, px, None)
    except Exception as e:
        log(f"! Failed: {e}")


def pointer_speed(v):
    try:
        reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSensitivity", str(v), winreg.REG_SZ)
        spi(0x0071, 0, int(v))
    except Exception:
        pass


def _delete_contents(folder):
    freed = 0
    if not folder or not os.path.isdir(folder):
        return 0
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        try:
            if os.path.isfile(p) or os.path.islink(p):
                freed += os.path.getsize(p)
                os.remove(p)
            else:
                for dp, _, fs in os.walk(p):
                    for f in fs:
                        try:
                            freed += os.path.getsize(os.path.join(dp, f))
                        except OSError:
                            pass
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass  # in use - skip
    return freed


def clean_temp(log):
    log("Cleaning temp files...")
    freed = 0
    for folder in {os.environ.get("TEMP"), os.environ.get("TMP"), r"C:\Windows\Temp"}:
        freed += _delete_contents(folder)
    log(f"  Freed about {freed / 1048576:.1f} MB.")
    return freed


def clean_recycle(log):
    log("Emptying Recycle Bin...")
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        log("  Recycle Bin emptied.")
    except Exception as e:
        log(f"! Failed: {e}")


def clean_thumbs(log):
    log("Clearing thumbnail cache...")
    freed = 0
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\Explorer")
    for f in glob.glob(os.path.join(base, "thumbcache_*.db")):
        try:
            freed += os.path.getsize(f)
            os.remove(f)
        except OSError:
            pass
    log(f"  Freed about {freed / 1048576:.1f} MB.")


def clean_all(log):
    clean_temp(log)
    clean_thumbs(log)
    clean_recycle(log)
    run("ipconfig /flushdns")
    log("=== Cleanup complete ===")


def optimize_game(log, game):
    log(f"Optimizing {game['name']}...")
    set_power(log, "high")
    tweak_gamemode(log, True)
    for exe in game["exes"]:
        if is_admin():
            try:
                reg_set(winreg.HKEY_LOCAL_MACHINE,
                        rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe}\PerfOptions",
                        "CpuPriorityClass", 3)
                log(f"  {exe}: will always launch with HIGH CPU priority.")
            except OSError as e:
                log(f"! Priority rule failed: {e}")
        set_live_priority(exe)
    if not is_admin():
        log("! Not admin: permanent priority rule skipped (running copies still boosted).")
    log(f"{game['name']} is ready. Tip: {game['tip']}")


def undo_game(log, game):
    log(f"Removing priority rule for {game['name']}...")
    if not need_admin(log, "Removing the priority rule"):
        return
    for exe in game["exes"]:
        try:
            winreg.DeleteKey(
                winreg.HKEY_LOCAL_MACHINE,
                rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe}\PerfOptions")
        except OSError:
            pass
    log("Done.")


# ------------------------------------------------------------------ extra tweaks (switches)
GCS_KEY = r"System\GameConfigStore"
PT_KEY = r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling"
PRI_KEY = r"SYSTEM\CurrentControlSet\Control\PriorityControl"
DO_KEY = r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization"
BG_USER_KEY = r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications"
BG_SEARCH_KEY = r"Software\Microsoft\Windows\CurrentVersion\Search"
BG_POLICY_KEY = r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy"


def _t_bgapps(log, on):
    u = winreg.HKEY_CURRENT_USER
    reg_set(u, BG_USER_KEY, "GlobalUserDisabled", 1 if on else 0)
    reg_set(u, BG_SEARCH_KEY, "BackgroundAppGlobalToggle", 0 if on else 1)
    if is_admin():
        m = winreg.HKEY_LOCAL_MACHINE
        if on:
            reg_set(m, BG_POLICY_KEY, "LetAppsRunInBackground", 2)   # 2 = force deny
        else:
            reg_del(m, BG_POLICY_KEY, "LetAppsRunInBackground")
    elif on:
        log("  (Run as admin to also apply the system-wide background-apps policy.)")
    log("Background apps are OFF (Store apps can no longer run in the background)." if on
        else "Background apps back to the Windows default.")


def _c_bgapps():
    return reg_get(winreg.HKEY_CURRENT_USER, BG_USER_KEY, "GlobalUserDisabled") == 1


def _t_fso(log, on):
    u = winreg.HKEY_CURRENT_USER
    if on:
        reg_set(u, GCS_KEY, "GameDVR_FSEBehaviorMode", 2)
        reg_set(u, GCS_KEY, "GameDVR_HonorUserFSEBehaviorMode", 1)
        reg_set(u, GCS_KEY, "GameDVR_FSEBehavior", 2)
        reg_set(u, GCS_KEY, "GameDVR_DXGIHonorFSEWindowsCompatible", 1)
        log("Fullscreen optimizations OFF (games use true fullscreen = less input lag).")
    else:
        reg_set(u, GCS_KEY, "GameDVR_FSEBehaviorMode", 0)
        reg_set(u, GCS_KEY, "GameDVR_HonorUserFSEBehaviorMode", 0)
        reg_del(u, GCS_KEY, "GameDVR_FSEBehavior")
        reg_del(u, GCS_KEY, "GameDVR_DXGIHonorFSEWindowsCompatible")
        log("Fullscreen optimizations back to the Windows default.")


def _c_fso():
    return reg_get(winreg.HKEY_CURRENT_USER, GCS_KEY, "GameDVR_FSEBehaviorMode") == 2


def _t_throttle(log, on):
    m = winreg.HKEY_LOCAL_MACHINE
    if on:
        reg_set(m, PT_KEY, "PowerThrottlingOff", 1)
        log("CPU power throttling OFF (restart makes it fully active).")
    else:
        reg_del(m, PT_KEY, "PowerThrottlingOff")
        log("CPU power throttling back to the Windows default.")


def _c_throttle():
    return reg_get(winreg.HKEY_LOCAL_MACHINE, PT_KEY, "PowerThrottlingOff") == 1


def _t_prio(log, on):
    # 0x26 = short, variable-free quantum with the strongest foreground boost. Default is 2.
    reg_set(winreg.HKEY_LOCAL_MACHINE, PRI_KEY, "Win32PrioritySeparation", 38 if on else 2)
    log("Foreground apps now get the biggest CPU share (your game wins)." if on
        else "CPU scheduling back to the Windows default.")


def _c_prio():
    return reg_get(winreg.HKEY_LOCAL_MACHINE, PRI_KEY, "Win32PrioritySeparation") == 38


def _t_delivery(log, on):
    m = winreg.HKEY_LOCAL_MACHINE
    if on:
        reg_set(m, DO_KEY, "DODownloadMode", 0)   # 0 = HTTP only, no peer-to-peer uploads
        log("Windows Update peer-to-peer sharing OFF (no hidden uploads = steadier ping).")
    else:
        reg_del(m, DO_KEY, "DODownloadMode")
        log("Delivery Optimization back to the Windows default.")


def _c_delivery():
    return reg_get(winreg.HKEY_LOCAL_MACHINE, DO_KEY, "DODownloadMode") == 0


EXTRA_TWEAKS = [
    dict(key="bgapps", name="Disable background apps", admin=False, fn=_t_bgapps, check=_c_bgapps,
         desc="Stops Store apps from running in the background and eating CPU, RAM and network."),
    dict(key="fso", name="Fullscreen optimizations OFF", admin=False, fn=_t_fso, check=_c_fso,
         desc="Games use true fullscreen instead of the Windows compositor: lower input lag, steadier FPS."),
    dict(key="throttle", name="No CPU power throttling", admin=True, fn=_t_throttle, check=_c_throttle,
         desc="Stops Windows from slowing the CPU for apps it thinks are background. Uses more power on laptops."),
    dict(key="prio", name="Foreground app priority boost", admin=True, fn=_t_prio, check=_c_prio,
         desc="Gives the window you are using (your game) a bigger share of CPU time than background apps."),
    dict(key="delivery", name="Stop Windows Update uploading", admin=True, fn=_t_delivery, check=_c_delivery,
         desc="Turns off peer-to-peer update sharing so your connection is not used in the background (helps ping)."),
]


def tweak_is_on(t):
    if not IS_WIN:
        return False
    try:
        return bool(t["check"]())
    except Exception:
        return False


def apply_tweak(log, key, on=True):
    t = next((x for x in EXTRA_TWEAKS if x["key"] == key), None)
    if t is None:
        return
    if t["admin"] and not need_admin(log, t["name"]):
        return
    try:
        t["fn"](log, on)
    except OSError as e:
        log(f"! {t['name']} failed: {e}")


def _avail_mb():
    ms = MEMSTAT()
    ms.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
    return ms.ullAvailPhys / 1048576


def trim_ram(log):
    """Ask Windows to push idle memory of every process to the page file, freeing RAM for the game."""
    log("Trimming RAM from idle apps...")
    try:
        k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
        k32.OpenProcess.restype = ctypes.c_void_p
        k32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
        before = _avail_mb()
        arr = (ctypes.c_ulong * 4096)()
        needed = ctypes.c_ulong()
        psapi.EnumProcesses(ctypes.byref(arr), ctypes.sizeof(arr), ctypes.byref(needed))
        for pid in arr[: needed.value // ctypes.sizeof(ctypes.c_ulong)]:
            if pid <= 4:
                continue
            h = k32.OpenProcess(0x0100 | 0x0400, 0, pid)   # SET_QUOTA | QUERY_INFORMATION
            if h:
                psapi.EmptyWorkingSet(h)
                k32.CloseHandle(h)
        time.sleep(0.5)
        gained = _avail_mb() - before
        log(f"  Free RAM changed by about {gained:+.0f} MB (apps re-load what they need as you use them).")
    except Exception as e:
        log(f"! RAM trim failed: {e}")


# ------------------------------------------------------------------ process manager
# Windows' own processes: hidden from the list so nobody can break Windows by accident.
PROTECTED = {
    "system", "idle", "registry", "memory compression", "smss", "csrss", "wininit", "winlogon",
    "services", "lsass", "lsaiso", "svchost", "dwm", "explorer", "fontdrvhost", "sihost",
    "taskhostw", "ctfmon", "runtimebroker", "searchhost", "searchindexer", "searchapp",
    "startmenuexperiencehost", "shellexperiencehost", "textinputhost", "applicationframehost",
    "securityhealthsystray", "securityhealthservice", "msmpeng", "nissrv", "audiodg", "conhost",
    "spoolsv", "wudfhost", "dllhost", "unsecapp", "wmiprvse", "lockapp", "userinit",
    "python", "pythonw", "py", "powershell", "pwsh", "cmd", "windowsterminal", "openconsole",
}


def list_procs():
    """Every closable program in this user's session, grouped by name:
    [{name, pids, mb, title}] sorted by memory (title = a window title, '' = no window)."""
    script = ("$ErrorActionPreference='SilentlyContinue'; "
              "$s=(Get-Process -Id $PID).SessionId; "
              "Get-Process | Where-Object { $_.SessionId -eq $s } | ForEach-Object { "
              "$_.ProcessName+'|'+$_.Id+'|'+[math]::Round($_.WorkingSet64/1MB)+'|'+"
              "($_.MainWindowTitle -replace '\\|',' ') }")
    out = ps(script)
    me = {os.getpid(), os.getppid()}
    groups = {}
    for line in out.splitlines():
        parts = line.strip().split("|", 3)
        if len(parts) < 3:
            continue
        name = parts[0].strip()
        try:
            pid, mb = int(parts[1]), float(parts[2])
        except ValueError:
            continue
        title = parts[3].strip() if len(parts) > 3 else ""
        if not name or pid in me or name.lower() in PROTECTED:
            continue
        g = groups.setdefault(name.lower(), dict(name=name, pids=[], mb=0.0, title=""))
        g["pids"].append(pid)
        g["mb"] += mb
        if title and not g["title"]:
            g["title"] = title
    return sorted(groups.values(), key=lambda g: -g["mb"])


def close_procs(log, groups, force=False):
    """Close the given groups. Polite close first (apps may ask to save); force ends them instantly."""
    freed = 0.0
    for g in groups:
        log(("Force closing " if force else "Closing ") + f"{g['name']} ({len(g['pids'])} process(es))...")
        for pid in g["pids"]:
            run(["taskkill", "/PID", str(pid)] + (["/F"] if force else []))
    time.sleep(1 if force else 3)
    pids = [str(p) for g in groups for p in g["pids"]]
    out = ps("Get-Process -Id " + ",".join(pids) + " -ErrorAction SilentlyContinue | "
             "ForEach-Object { $_.ProcessName }") if pids else ""
    alive = {n.strip().lower() for n in out.splitlines() if n.strip()}
    closed = 0
    for g in groups:
        if g["name"].lower() in alive:
            log(f"! {g['name']} is still running"
                + ("" if force else " (it may be asking you to save, or needs Force close)."))
        else:
            closed += 1
            freed += g["mb"]
    log(f"=== Closed {closed} of {len(groups)} app(s), freed about {freed:.0f} MB ===")


def close_by_names(log, names, force=False):
    """Re-scan first so we never act on stale process IDs."""
    names = {n.lower() for n in names}
    groups = [g for g in list_procs() if g["name"].lower() in names]
    if not groups:
        log("Nothing to close - those apps are no longer running.")
        return
    close_procs(log, groups, force)


def boost_all(log):
    tweak_network(log)
    set_power(log, "ultimate")          # falls back to High Performance if the PC has no Ultimate plan
    tweak_gamemode(log, True)
    visuals(log, True)
    for t in EXTRA_TWEAKS:              # background apps, fullscreen opt, power throttling, priority, uploads
        apply_tweak(log, t["key"], True)
    mouse_accel(log, False)
    mouse_drag(log, True)
    clean_all(log)
    trim_ram(log)
    log("=== ALL DONE - restart your PC for the best result ===")


def restore_all(log):
    log("Restoring Windows defaults...")
    mouse_accel(log, True)
    mouse_drag(log, False)
    run(f"powercfg /setactive {BALANCED_PLAN}")
    visuals(log, False)
    tweak_gamemode(log, False)
    for t in EXTRA_TWEAKS:
        apply_tweak(log, t["key"], False)
    set_dns(log, "auto")
    if is_admin():
        run("netsh int tcp set global initialRto=3000")
        run("netsh int tcp set heuristics enabled")
        base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                    except OSError:
                        break
                    i += 1
                    reg_del(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, "TcpAckFrequency")
                    reg_del(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, "TCPNoDelay")
                    reg_del(winreg.HKEY_LOCAL_MACHINE, base + "\\" + sub, "TcpDelAckTicks")
        except OSError:
            pass
        prof = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        try:
            reg_set(winreg.HKEY_LOCAL_MACHINE, prof, "NetworkThrottlingIndex", 10)
            reg_set(winreg.HKEY_LOCAL_MACHINE, prof, "SystemResponsiveness", 20)
        except OSError:
            pass
    log("=== Defaults restored (restart for network settings) ===")


# ------------------------------------------------------------------ app
class App:
    HEADER, FOOT, SIDE = 72, 38, 220
    PROC_PER_PAGE = 10
    CX, CW = 240, 640
    RX = 900
    NAV_TOP, NAV_H = 100, 50

    def __init__(self):
        r = self.root = tk.Tk()
        r.title(APP_NAME + "  [timed-license build]")
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        r.geometry(f"{W}x{H}+{max(0, (sw - W) // 2)}+{max(0, (sh - H) // 2 - 20)}")
        r.resizable(False, False)
        r.configure(bg="#0b0a1f")
        try:
            self.icon = tk.PhotoImage(data="".join(ICON_B64.split()))
            r.iconphoto(True, self.icon)
        except Exception:
            pass
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
        except OSError:
            pass
        self.c = tk.Canvas(r, width=W, height=H, highlightthickness=0, bg="#0b0a1f")
        self.c.pack()

        self.q = queue.Queue()
        self.busy = False
        self.logs = deque(maxlen=9)
        self.scroll = 0.0
        self.target = 0.0
        self.max_scroll = 0.0
        self.nb = 0
        self.chips = {}
        self.sections = []
        self.sel_game = 0
        self.auto_boost = False
        self.boosted = set()
        self.ping_hist = deque(maxlen=30)
        self.ping_now = None
        self.ping_ver = 0
        self.shown_ver = -1
        self.cpu_prev = None
        self.nav_hover = False
        self.sb_active = False
        self.fc = 0
        self.trail_on = True
        self.trail_delay = 45
        self.trail_len = 24
        self.ov = None
        self.main_ready = False
        self.shake = []
        self.remember = True
        self.logo_imgs = []
        self.chip_cb = {}
        self.proc_all = []
        self.proc_sel = set()
        self.proc_page = 0
        self.proc_loading = False
        self.boost_closes = False
        self.tweak_sw = {}
        # Purple is the only supported theme; ignore any older saved theme choice.
        self.theme_mode = "normal"

        self.draw_bg()
        self.make_snow()
        self.gate_ring = None
        self.hw_text = {}
        clear_license()  # old "remembered" license files are wiped: key is needed on every launch
        self.build_gate()
        r.after(16, self.frame)

    def start_main(self):
        self.build_content()
        self.build_chrome()
        self.make_trail()
        self.bind_events()
        self.c.tag_raise("mask")
        self.c.tag_raise("fixed")
        self.select_game(0)
        self.update_scrollbar()
        self.proc_refresh()
        self.main_ready = True
        if IS_WIN:
            threading.Thread(target=self.ping_loop, daemon=True).start()
            threading.Thread(target=self.auto_loop, daemon=True).start()
        threading.Thread(target=self.hw_loop, daemon=True).start()
        self.log("Welcome! Pick a tweak, or hit BOOST EVERYTHING.")
        self.log("License: " + (self.license_user + " - " if self.license_user else "") +
                 (self.license_label + " - " if self.license_label else "") + self.license_text())
        if not IS_WIN:
            self.log("! The optimizer only works on Windows (visuals still run).")
        self.root.after(500, self.check_admin)
        self.root.after(1000, self.license_tick)

    # ---------------------------------------------------------- license gate
    def build_gate(self):
        c, cx = self.c, W // 2
        self.fails = 0
        self.lock_until = 0.0
        self.license_master = False
        self.license_expires = None   # datetime, or None = never expires
        self.license_key_shown = LICENSE_KEY
        self.license_user = ""
        self.license_label = ""
        self.sub_pill = None
        self.sub_card_text = None
        # soft glow layers + card
        for i, col in enumerate(("#0d0b25", "#110f2e", "#161339", "#1a1744")):
            pad = 26 - i * 7
            self.rr(cx - 270 - pad, 62 - pad, cx + 270 + pad, 700 + pad, 44, fill=col, outline="", tags="gate")
        self.rr(cx - 270, 56, cx + 270, 690, 34, fill=CARD, outline=BORDER, width=1, tags="gate")
        c.create_line(cx - 230, 58, cx + 230, 58, fill="#6a66b8", width=1, tags="gate")
        self.gate_ring = self.rr(cx - 270, 56, cx + 270, 690, 34, fill="", outline=PURPLE, width=2, tags="gate")

        self.logo_big = tk.PhotoImage(data="".join(LOGO_BIG_B64.split()))
        c.create_image(cx, 150, image=self.logo_big, tags="gate")
        c.create_text(cx, 252, text=APP_NAME, fill="white", font=("Segoe UI", 28, "bold"), tags="gate")
        c.create_text(cx, 290, text="ping  \u2022  fps  \u2022  mouse  \u2022  cleanup", fill=MUTED,
                      font=("Segoe UI", 10), tags="gate")
        # pill
        self.rr(cx - 100, 318, cx + 100, 346, 14, fill="#2c2863", outline="#7c70ee", tags="gate")
        c.create_text(cx, 332, text="\u25c6  LICENSE REQUIRED", fill=PURPLE2,
                      font=("Segoe UI", 9, "bold"), tags="gate")

        c.create_text(cx - 185, 392, text="LICENSE KEY", anchor="w", fill=MUTED,
                      font=("Segoe UI", 9, "bold"), tags="gate")
        self.keyvar = tk.StringVar()
        self.entry = tk.Entry(self.root, textvariable=self.keyvar, font=("Consolas", 17, "bold"),
                              justify="center", bg=INPUT, fg="white", insertbackground="white",
                              relief="flat", highlightthickness=2, highlightbackground="#3a3675",
                              highlightcolor=PURPLE, disabledbackground=INPUT, disabledforeground=GOOD)
        c.create_window(cx, 436, window=self.entry, width=370, height=52, tags="gate")

        def fmt(*_):
            raw = re.sub(r"[^A-Za-z0-9]", "", self.keyvar.get()).upper()[:16]
            out = "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))
            if out != self.keyvar.get():
                self.keyvar.set(out)
                self.entry.icursor("end")

        self.keyvar.trace_add("write", fmt)
        self.entry.bind("<Return>", lambda e: self.try_activate())
        self.entry.focus_set()
        c.create_text(cx, 482, text="Format:  XXXX-XXXX-XXXX-XXXX   (dashes are added for you)", fill="#6b68a3",
                      font=("Segoe UI", 9), tags="gate")

        btn = self.rr(cx - 185, 512, cx + 185, 564, 18, fill=PURPLE, outline="#d9d2ff",
                      tags=("gate", "gbtn"))
        c.create_text(cx, 538, text="\u2726   ACTIVATE   \u2726", fill="white", font=("Segoe UI", 13, "bold"),
                      tags=("gate", "gbtn"))
        c.tag_bind("gbtn", "<Enter>", lambda e: (c.itemconfig(btn, fill="#a897ff"), c.config(cursor="hand2")))
        c.tag_bind("gbtn", "<Leave>", lambda e: (c.itemconfig(btn, fill=PURPLE), c.config(cursor="")))
        c.tag_bind("gbtn", "<Button-1>", lambda e: self.try_activate())

        self.gmsg = c.create_text(cx, 596, text="", fill=MUTED, font=("Segoe UI", 11, "bold"), tags="gate")
        c.create_line(cx - 205, 616, cx + 205, 616, fill="#2a2757", tags="gate")

        # Discord free-license area: click the main invite button to open the server,
        # or use the smaller button to copy the invite URL.
        discord_url = "https://discord.gg/VBBzUX3v6"
        discord_tag = "discord_invite"
        copy_tag = "discord_copy"

        # Small Discord-style controller mark, drawn directly on the canvas.
        c.create_polygon(
            cx - 183, 642, cx - 178, 633, cx - 166, 629,
            cx - 153, 629, cx - 141, 633, cx - 136, 642,
            cx - 139, 658, cx - 147, 663, cx - 154, 657,
            cx - 165, 657, cx - 172, 663, cx - 180, 658,
            fill="white", outline="white", smooth=True, tags=("gate", discord_tag)
        )
        c.create_oval(cx - 169, 642, cx - 165, 646, fill="#1b1940", outline="", tags=("gate", discord_tag))
        c.create_oval(cx - 158, 642, cx - 154, 646, fill="#1b1940", outline="", tags=("gate", discord_tag))
        c.create_line(cx - 174, 648, cx - 168, 648, fill="#1b1940", width=2, tags=("gate", discord_tag))
        c.create_line(cx - 171, 645, cx - 171, 651, fill="#1b1940", width=2, tags=("gate", discord_tag))

        invite_shape = self.rr(cx - 126, 625, cx + 105, 669, 12,
                               fill="#5865F2", outline="#8992ff", width=1,
                               tags=("gate", discord_tag))
        c.create_text(cx - 10, 641, text="GET FREE LICENSE HERE", fill="white",
                      font=("Segoe UI", 10, "bold"), tags=("gate", discord_tag))
        c.create_text(cx - 10, 656, text="make a ticket", fill="#e4e6ff",
                      font=("Segoe UI", 8), tags=("gate", discord_tag))

        copy_shape = self.rr(cx + 115, 632, cx + 204, 662, 9,
                             fill="#1b1940", outline="#8992ff", width=1,
                             tags=("gate", copy_tag))
        c.create_text(cx + 159, 647, text="COPY LINK", fill="white",
                      font=("Segoe UI", 8, "bold"), tags=("gate", copy_tag))

        def open_discord(_event=None):
            webbrowser.open(discord_url)

        def copy_discord(_event=None):
            self.root.clipboard_clear()
            self.root.clipboard_append(discord_url)
            self.root.update_idletasks()
            c.itemconfig(self.gmsg, text="Discord invite link copied!", fill=GOOD)

        c.tag_bind(discord_tag, "<Enter>", lambda e: (c.itemconfig(invite_shape, fill="#7180ff"), c.config(cursor="hand2")))
        c.tag_bind(discord_tag, "<Leave>", lambda e: (c.itemconfig(invite_shape, fill="#5865F2"), c.config(cursor="")))
        c.tag_bind(discord_tag, "<Button-1>", open_discord)
        c.tag_bind(copy_tag, "<Enter>", lambda e: (c.itemconfig(copy_shape, fill="#2b2862"), c.config(cursor="hand2")))
        c.tag_bind(copy_tag, "<Leave>", lambda e: (c.itemconfig(copy_shape, fill="#1b1940"), c.config(cursor="")))
        c.tag_bind(copy_tag, "<Button-1>", copy_discord)
        admin_shape = self.rr(14, 718, 105, 746, 9, fill="#13112b", outline="#4a4585", tags=("gate", "admin_gate"))
        c.create_text(59, 732, text="For HEPE", fill=PURPLE2, font=("Segoe UI", 8, "bold"), tags=("gate", "admin_gate"))
        c.tag_bind("admin_gate", "<Enter>", lambda e: (c.itemconfig(admin_shape, fill="#262358"), c.config(cursor="hand2")))
        c.tag_bind("admin_gate", "<Leave>", lambda e: (c.itemconfig(admin_shape, fill="#13112b"), c.config(cursor="")))
        c.tag_bind("admin_gate", "<Button-1>", lambda e: self.open_license_admin())

    def load_generated_licenses(self):
        try:
            with open(ADMIN_LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_generated_licenses(self, data):
        os.makedirs(os.path.dirname(ADMIN_LICENSE_FILE), exist_ok=True)
        tmp = ADMIN_LICENSE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, ADMIN_LICENSE_FILE)

    def open_license_admin(self):
        from tkinter import simpledialog, messagebox

        password = simpledialog.askstring(
            "HEPE access", "Enter HEPE password:",
            show="*", parent=self.root
        )
        if password is None:
            return
        if password != ADMIN_PASSWORD:
            messagebox.showerror("Access denied", "Incorrect password.", parent=self.root)
            return

        # Build the window completely before grabbing focus.  Grabbing an
        # unfinished Toplevel can leave some Tk builds showing a blank/white
        # window after the password dialog closes.
        win = None
        admin_bg = "#100e29"  # Tkinter requires a color string, not the RGB tuple used by the app theme.
        try:
            win = tk.Toplevel(self.root)
            win.withdraw()
            win.title("HEPE - License generator")
            win.configure(bg=admin_bg)
            win.resizable(False, False)

            pad = tk.Frame(win, bg=admin_bg, padx=20, pady=18)
            pad.pack(fill="both", expand=True)

            tk.Label(
                pad, text="Generate a license", bg=admin_bg, fg="white",
                font=("Segoe UI", 15, "bold")
            ).pack(anchor="w", pady=(0, 14))

            tk.Label(pad, text="User / customer", bg=admin_bg, fg=MUTED).pack(anchor="w")
            user_var = tk.StringVar(master=win)
            user_entry = tk.Entry(
                pad, textvariable=user_var, width=36, bg="#17152f",
                fg="white", insertbackground="white", relief="flat"
            )
            user_entry.pack(fill="x", pady=(4, 12), ipady=6)

            tk.Label(pad, text="License duration", bg=admin_bg, fg=MUTED).pack(anchor="w")
            dur_row = tk.Frame(pad, bg=admin_bg)
            dur_row.pack(fill="x", pady=(4, 6))
            amount_var = tk.StringVar(master=win, value="1")
            amount_entry = tk.Entry(
                dur_row, textvariable=amount_var, width=8, justify="center",
                bg="#17152f", fg="white", insertbackground="white", relief="flat",
                disabledbackground="#121027", disabledforeground="#6f6c9c"
            )
            amount_entry.pack(side="left", ipady=6)
            unit_var = tk.StringVar(master=win, value="Days")
            unit_menu = tk.OptionMenu(dur_row, unit_var, *DURATION_UNITS, LIFETIME)
            unit_menu.configure(
                bg="#211f45", fg="white", activebackground="#4a4585",
                activeforeground="white", relief="flat", highlightthickness=0
            )
            unit_menu["menu"].configure(
                bg="#17152f", fg="white", activebackground=PURPLE,
                activeforeground="white"
            )
            unit_menu.pack(side="left", fill="x", expand=True, padx=(8, 0))

            def sync_amount_state(*_):
                amount_entry.config(state="disabled" if unit_var.get() == LIFETIME else "normal")

            unit_var.trace_add("write", sync_amount_state)

            def set_preset(amount, unit):
                unit_var.set(unit)
                amount_var.set(str(amount))

            preset_row = tk.Frame(pad, bg=admin_bg)
            preset_row.pack(fill="x", pady=(0, 12))
            for text, amt, unit in (
                ("15 min", 15, "Minutes"), ("1 hour", 1, "Hours"), ("1 day", 1, "Days"),
                ("7 days", 7, "Days"), ("30 days", 30, "Days"), ("Lifetime", 1, LIFETIME),
            ):
                tk.Button(
                    preset_row, text=text, command=lambda a=amt, u=unit: set_preset(a, u),
                    bg="#211f45", fg="white", activebackground="#4a4585",
                    activeforeground="white", relief="flat", padx=4, pady=3,
                    font=("Segoe UI", 8)
                ).pack(side="left", expand=True, fill="x", padx=1)

            result_var = tk.StringVar(master=win, value="")
            result_entry = tk.Entry(
                pad, textvariable=result_var, width=36, state="readonly",
                justify="center", readonlybackground="#17152f",
                fg="#d6ceff", relief="flat"
            )
            result_entry.pack(fill="x", pady=(0, 12), ipady=6)

            def generate():
                username = user_var.get().strip()
                if not username:
                    messagebox.showwarning(
                        "Missing user", "Enter the user/customer name first.",
                        parent=win
                    )
                    user_entry.focus_set()
                    return
                unit = unit_var.get()
                if unit == LIFETIME:
                    seconds, label = None, LIFETIME
                else:
                    try:
                        amount = int(amount_var.get().strip())
                    except ValueError:
                        amount = 0
                    if amount < 1:
                        messagebox.showwarning(
                            "Invalid duration",
                            "Enter a whole number of 1 or more.", parent=win
                        )
                        amount_entry.focus_set()
                        return
                    seconds = amount * DURATION_UNITS[unit]
                    if seconds > MAX_LICENSE_SECONDS:
                        messagebox.showwarning(
                            "Too long",
                            "That is over 100 years. Pick Lifetime instead.", parent=win
                        )
                        amount_entry.focus_set()
                        return
                    word = unit.split(" (")[0].lower()
                    if amount == 1:
                        word = word.rstrip("s")
                    label = f"{amount} {word}"
                raw = secrets.token_hex(8).upper()
                key = "-".join(raw[i:i+4] for i in range(0, 16, 4))
                db = self.load_generated_licenses()
                # The timer starts the first time the key is entered, so the
                # full chosen time is always available to the customer.
                db[key.replace("-", "")] = {
                    "key": key, "user": username,
                    "created": datetime.now().isoformat(timespec="seconds"),
                    "duration": label, "duration_seconds": seconds,
                    "activated": None, "expires": None
                }
                self.save_generated_licenses(db)
                result_var.set(key)
                result_entry.config(state="normal")
                result_entry.selection_range(0, "end")
                result_entry.config(state="readonly")
                note = ("Never expires." if seconds is None
                        else "The timer starts the first time the key is entered.")
                messagebox.showinfo(
                    "License created",
                    f"License created for {username}.\nDuration: {label}\n{note}",
                    parent=win
                )

            tk.Button(
                pad, text="GENERATE LICENSE", command=generate,
                bg=PURPLE, fg="white", activebackground="#7a68f0",
                activeforeground="white", relief="flat", padx=12, pady=9
            ).pack(fill="x", pady=(0, 8))
            tk.Button(
                pad, text="MANAGE LICENSES  (see active, revoke, extend)",
                command=lambda: self.open_license_manager(win),
                bg="#211f45", fg="white", activebackground="#4a4585",
                activeforeground="white", relief="flat", pady=8
            ).pack(fill="x", pady=(0, 8))
            tk.Button(
                pad, text="Close", command=win.destroy,
                bg="#211f45", fg="white", activebackground="#4a4585",
                activeforeground="white", relief="flat", pady=6
            ).pack(fill="x")

            win.update_idletasks()
            width = max(360, win.winfo_reqwidth())
            height = win.winfo_reqheight()
            x = self.root.winfo_rootx() + 70
            y = self.root.winfo_rooty() + 70
            win.geometry(f"{width}x{height}+{x}+{y}")
            win.deiconify()
            win.lift()
            win.focus_force()
            win.grab_set()
            user_entry.focus_set()

        except Exception as exc:
            try:
                if win is not None and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
            messagebox.showerror(
                "HEPE window error",
                f"The license generator could not open:\\n{exc}",
                parent=self.root
            )

    def open_license_manager(self, parent=None):
        from tkinter import ttk, simpledialog, messagebox

        parent = parent or self.root
        bg = "#100e29"
        mw = tk.Toplevel(parent)
        mw.withdraw()
        mw.title("HEPE - Manage licenses")
        mw.configure(bg=bg)
        mw.minsize(880, 480)

        st = ttk.Style(mw)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Hepe.Treeview", background="#17152f", fieldbackground="#17152f",
                     foreground="white", rowheight=26, borderwidth=0)
        st.configure("Hepe.Treeview.Heading", background="#211f45", foreground=PURPLE2,
                     relief="flat", font=("Segoe UI", 9, "bold"))
        st.map("Hepe.Treeview", background=[("selected", "#4a4585")], foreground=[("selected", "white")])
        st.map("Hepe.Treeview.Heading", background=[("active", "#2c2863")])

        top = tk.Frame(mw, bg=bg, padx=16, pady=12)
        top.pack(fill="x")
        tk.Label(top, text="Licenses", bg=bg, fg="white", font=("Segoe UI", 15, "bold")).pack(side="left")
        summary = tk.Label(top, text="", bg=bg, fg=MUTED, font=("Segoe UI", 9))
        summary.pack(side="right")

        cols = ("user", "key", "duration", "status", "left", "activated")
        heads = ("User", "Key", "Duration", "Status", "Time left", "Activated")
        widths = (150, 175, 90, 95, 140, 150)
        body = tk.Frame(mw, bg=bg, padx=16)
        body.pack(fill="both", expand=True)
        tree = ttk.Treeview(body, columns=cols, show="headings", style="Hepe.Treeview", selectmode="extended")
        for c_, h_, w_ in zip(cols, heads, widths):
            tree.heading(c_, text=h_)
            tree.column(c_, width=w_, anchor="w")
        vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        for kind, col in (("active", GOOD), ("lifetime", GOOD), ("unused", "#8fb4ff"),
                          ("expired", WARN), ("revoked", "#ff7a90")):
            tree.tag_configure(kind, foreground=col)

        def refresh():
            keep = set(tree.selection())
            tree.delete(*tree.get_children())
            db = self.load_generated_licenses()
            now = datetime.now()
            n = dict(active=0, unused=0, expired=0, revoked=0)
            for norm, info in sorted(db.items(), key=lambda kv: kv[1].get("created", ""), reverse=True):
                kind, text = license_status(info, now)
                n["active" if kind == "lifetime" else kind] += 1
                if kind == "active":
                    left = format_remaining(datetime.fromisoformat(info["expires"]))
                elif kind == "lifetime":
                    left = "Never expires"
                elif kind == "unused":
                    left = "starts on first use"
                else:
                    left = "-"
                act = (info.get("activated") or "-").replace("T", " ")
                tree.insert("", "end", iid=norm, tags=(kind,), values=(
                    info.get("user", "?"), info.get("key", norm), info.get("duration", "?"), text, left, act))
            keep &= set(tree.get_children())
            if keep:
                tree.selection_set(list(keep))
            summary.config(text=f"{len(db)} total   \u2022   {n['active']} active   \u2022   "
                                f"{n['unused']} unused   \u2022   {n['expired']} expired   \u2022   "
                                f"{n['revoked']} revoked")

        def picked():
            sel = list(tree.selection())
            if not sel:
                messagebox.showinfo("Select a license", "Click one or more licenses in the list first.", parent=mw)
            return sel

        def save(db):
            try:
                self.save_generated_licenses(db)
            except OSError as exc:
                messagebox.showerror("Could not save", str(exc), parent=mw)
            refresh()

        def copy_key():
            sel = picked()
            if sel:
                db = self.load_generated_licenses()
                mw.clipboard_clear()
                mw.clipboard_append("\n".join(db[k].get("key", k) for k in sel if k in db))

        def revoke():
            sel = picked()
            if not sel or not messagebox.askyesno(
                    "Revoke", f"Revoke {len(sel)} license(s)? They stop working "
                    "(a running copy locks within a few seconds).", parent=mw):
                return
            db = self.load_generated_licenses()
            for k in sel:
                if k in db:
                    db[k]["revoked"] = datetime.now().isoformat(timespec="seconds")
            save(db)

        def restore():
            sel = picked()
            if sel:
                db = self.load_generated_licenses()
                for k in sel:
                    if k in db:
                        db[k].pop("revoked", None)
                save(db)

        def add_time():
            sel = picked()
            if not sel:
                return
            txt = simpledialog.askstring("Add time", "How much time to add?\nExamples: 7 days, 12 hours, 2 weeks",
                                         parent=mw)
            if txt is None:
                return
            secs = parse_duration(txt)
            if not secs:
                messagebox.showwarning("Not understood", "Use a number and a unit, like '7 days' or '12 hours'.",
                                       parent=mw)
                return
            db = self.load_generated_licenses()
            now = datetime.now()
            skipped = 0
            for k in sel:
                info = db.get(k)
                if not info:
                    continue
                kind, _ = license_status(info, now)
                if info.get("expires") is None and not info.get("duration_seconds"):
                    skipped += 1                      # lifetime: nothing to extend
                elif info.get("expires") is None:     # not used yet: lengthen the budget
                    info["duration_seconds"] = int(info["duration_seconds"]) + secs
                    info["duration"] = fmt_seconds(info["duration_seconds"])
                else:                                 # running or expired: push the end date
                    try:
                        base = max(now, datetime.fromisoformat(info["expires"]))
                    except ValueError:
                        base = now
                    info["expires"] = (base + timedelta(seconds=secs)).isoformat(timespec="seconds")
            save(db)
            if skipped:
                messagebox.showinfo("Lifetime keys", f"{skipped} lifetime license(s) skipped - they never expire.",
                                    parent=mw)

        def delete():
            sel = picked()
            if not sel or not messagebox.askyesno(
                    "Delete", f"Permanently delete {len(sel)} license(s)? This cannot be undone.", parent=mw):
                return
            db = self.load_generated_licenses()
            for k in sel:
                db.pop(k, None)
            save(db)

        bar = tk.Frame(mw, bg=bg, padx=16, pady=12)
        bar.pack(fill="x")
        for text, cmd, colr in (("Refresh", refresh, "#211f45"), ("Copy key", copy_key, "#211f45"),
                                ("Add time", add_time, "#211f45"), ("Revoke", revoke, "#7a2a45"),
                                ("Restore", restore, "#211f45"), ("Delete", delete, "#7a2a45"),
                                ("Close", lambda: close(), PURPLE)):
            tk.Button(bar, text=text, command=cmd, bg=colr, fg="white", activebackground="#4a4585",
                      activeforeground="white", relief="flat", padx=14, pady=6).pack(side="left", padx=(0, 6))
        tk.Label(mw, text="Stored on this PC: " + ADMIN_LICENSE_FILE + "   (changes apply to this copy of the app)",
                 bg=bg, fg="#6b68a3", font=("Segoe UI", 8), anchor="w", padx=16).pack(fill="x", pady=(0, 10))

        job = {"id": None}

        def close():
            try:
                if job["id"]:
                    mw.after_cancel(job["id"])
                mw.destroy()
                parent.grab_set()                    # hand focus back to the generator window
            except Exception:
                pass

        def tick():
            try:
                if mw.winfo_exists():
                    refresh()
                    job["id"] = mw.after(5000, tick)
            except Exception:
                pass

        mw.protocol("WM_DELETE_WINDOW", close)
        refresh()
        mw.update_idletasks()
        mw.geometry(f"{max(880, mw.winfo_reqwidth())}x{max(480, mw.winfo_reqheight())}"
                    f"+{parent.winfo_rootx() + 40}+{parent.winfo_rooty() + 40}")
        mw.deiconify()
        mw.lift()
        mw.focus_force()
        mw.grab_set()
        job["id"] = mw.after(5000, tick)

    def resolve_license(self, norm):
        """Return (ok, expires_at, status). expires_at None = never expires."""
        if norm == LICENSE_KEY.replace("-", ""):
            return True, None, "master"
        db = self.load_generated_licenses()
        info = db.get(norm)
        if not info:
            return False, None, "invalid"
        if info.get("revoked"):
            return False, None, "revoked"
        now = datetime.now()
        secs = info.get("duration_seconds")
        expiry = info.get("expires")
        if expiry is None and secs:
            # First use: start the clock now.
            expires_at = now + timedelta(seconds=int(secs))
            info["activated"] = now.isoformat(timespec="seconds")
            info["expires"] = expires_at.isoformat(timespec="seconds")
            db[norm] = info
            try:
                self.save_generated_licenses(db)
            except OSError:
                pass
            return True, expires_at, "ok"
        if expiry is None:
            return True, None, "ok"  # lifetime
        try:
            expires_at = datetime.fromisoformat(expiry)
        except (TypeError, ValueError):
            expires_at = datetime.min
        if now >= expires_at:
            return False, None, "expired"
        return True, expires_at, "ok"

    def license_text(self):
        if self.license_master:
            return "Owner key"
        return format_remaining(self.license_expires)

    def license_tick(self):
        """Update the countdown once a second and lock the app when time is up."""
        try:
            self._lic_n = getattr(self, "_lic_n", 0) + 1
            if not self.license_master and getattr(self, "license_norm", "") and self._lic_n % 5 == 0:
                db = self.load_generated_licenses()
                info = db.get(self.license_norm)
                if db and (info is None or info.get("revoked")):
                    messagebox.showinfo("License revoked",
                                        "This license was revoked. Enter a valid key to continue.",
                                        parent=self.root)
                    self.do_lock()
                    return
                if info and info.get("expires"):
                    try:
                        self.license_expires = datetime.fromisoformat(info["expires"])  # picks up added time
                    except ValueError:
                        pass
            if not self.license_master and self.license_expires is not None:
                if datetime.now() >= self.license_expires:
                    messagebox.showinfo(
                        "License expired",
                        "Your license has expired. Enter a new key to continue.",
                        parent=self.root
                    )
                    self.do_lock()
                    return
                txt = self.license_text()
                for item, label in ((self.sub_pill, f"SUBSCRIPTION  \u2022  {txt}"),
                                    (self.sub_card_text, txt)):
                    try:
                        self.c.itemconfig(item, text=label)
                    except Exception:
                        pass
        except Exception:
            pass
        self.root.after(1000, self.license_tick)

    def try_activate(self):
        if time.time() < self.lock_until:
            return
        norm = re.sub(r"[^A-Za-z0-9]", "", self.keyvar.get()).upper()
        ok, expires_at, status = self.resolve_license(norm)
        if ok:
            self.license_master = (status == "master")
            self.license_norm = norm
            self.license_expires = expires_at
            info = self.load_generated_licenses().get(norm) or {}
            self.license_user = info.get("user", "")
            self.license_label = info.get("duration", "")
            self.license_key_shown = (LICENSE_KEY if self.license_master else
                                      "-".join(norm[i:i+4] for i in range(0, len(norm), 4)))
            self.c.itemconfig(self.gmsg, text=f"License accepted  \u2713   {self.license_text()}", fill=GOOD)
            self.entry.config(state="disabled")
            self.root.after(900, self.enter_main)
            return
        self.fails += 1
        self.shake = [6, -12, 12, -12, 12, -12, 12, -6]
        if self.fails >= 5:
            self.lock_until = time.time() + 15
            self.entry.config(state="disabled")
            self.c.itemconfig(self.gmsg, text="Too many tries - wait 15 seconds", fill=WARN)

            def unlock():
                self.fails = 0
                self.entry.config(state="normal")
                self.c.itemconfig(self.gmsg, text="", fill=MUTED)
                self.entry.focus_set()

            self.root.after(15000, unlock)
        else:
            left = 5 - self.fails
            what = {"expired": "This license has expired",
                    "revoked": "This license was revoked"}.get(status, "Invalid license key")
            self.c.itemconfig(self.gmsg, text=f"{what}   ({left} tries left)", fill="#ff7a90")

    def enter_main(self):
        self.gate_ring = None
        self.c.delete("gate")
        try:
            self.entry.destroy()
        except Exception:
            pass
        self.start_main()

    # ---------------------------------------------------------- theme
    def set_palette(self, mode="normal"):
        """Keep the original purple palette as the app's only theme."""
        global CARD, BORDER, PURPLE, PURPLE2, DEEP, INPUT, TEXT, MUTED, GOOD, WARN
        CARD, BORDER = "#1b1940", "#4a4590"
        PURPLE, PURPLE2, DEEP = "#8f7bff", "#cfc4ff", "#5846d8"
        INPUT, TEXT, MUTED = "#14122e", "#f3f1ff", "#a29fcf"
        GOOD, WARN = "#7cf0b6", "#ffd98a"
        self.theme_mode = "normal"

    def apply_theme(self, mode="normal"):
        """Compatibility method: restore and retain the original purple theme."""
        self.set_palette("normal")
        self.say("Normal purple theme restored ✦")

    # ---------------------------------------------------------- drawing prims
    def rr(self, x1, y1, x2, y2, r=14, tags=(), **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.c.create_polygon(pts, smooth=True, tags=tags, **kw)

    def R(self, x1, y1, x2, y2, r=14, tags=("content",), **kw):
        return self.rr(x1, self.HEADER + y1, x2, self.HEADER + y2, r, tags=tags, **kw)

    def T(self, x, y, text, size=11, bold=False, color=TEXT, anchor="nw", width=None,
          tags=("content",), mono=False):
        font = ("Consolas" if mono else "Segoe UI", size, "bold" if bold else "normal")
        kw = {"width": width} if width else {}
        return self.c.create_text(x, self.HEADER + y, text=text, fill=color, font=font,
                                  anchor=anchor, tags=tags, **kw)

    @staticmethod
    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))

    def draw_bg(self):
        """Deep indigo gradient with soft colour orbs for the glass panels to sit on."""
        c = self.c
        top, bot = (11, 10, 31), (22, 15, 52)
        c.configure(bg=self._mix(top, bot, 0.5))
        strips = 64
        sh = H / strips
        for i in range(strips):
            col = self._mix(top, bot, i / (strips - 1))
            c.create_rectangle(0, i * sh, W, (i + 1) * sh + 1, fill=col, outline="",
                               tags=("background",))
        # soft orbs: concentric discs fading from the backdrop colour to the glow colour
        for ox, oy, rad, glow, gain in ((150, 600, 330, (110, 80, 255), 0.30),
                                         (720, 90, 300, (60, 130, 255), 0.26),
                                         (1090, 640, 340, (200, 90, 255), 0.26)):
            base = self._mix(top, bot, oy / H)
            base_rgb = tuple(int(base[i:i + 2], 16) for i in (1, 3, 5))
            steps = 16
            for k in range(steps):
                f = k / (steps - 1)
                r = rad * (1 - f * 0.94)
                col = self._mix(base_rgb, glow, (f ** 1.7) * gain)
                c.create_oval(ox - r, oy - r, ox + r, oy + r, fill=col, outline="",
                              tags=("background",))

    # ---------------------------------------------------------- snow
    def make_snow(self):
        # Minimal snowfall: crisp, solid-white dots with no glow, rings, or tint.
        self.flakes = []
        for n in range(150):
            radius = random.uniform(1.0, 2.2)
            f = dict(
                x=random.uniform(0, W),
                y=random.uniform(0, H),
                vy=random.uniform(0.45, 1.25),
                ph=random.uniform(0, 6.28),
                sw=random.uniform(0.35, 0.8),
                kick_x=0.0,
                kick_y=0.0,
                tag=f"fl{n}",
            )
            self.c.create_oval(
                f["x"] - radius, f["y"] - radius,
                f["x"] + radius, f["y"] + radius,
                fill="#d9d6ff", outline="", tags=(f["tag"], "snow"),
            )
            self.flakes.append(f)
        self.t = 0.0

    def tick_snow(self):
        self.t += 0.03
        for f in self.flakes:
            dx = math.sin(self.t * f["sw"] + f["ph"]) * 0.28 + f["kick_x"]
            dy = f["vy"] + f["kick_y"]
            f["x"] += dx
            f["y"] += dy
            f["kick_x"] *= 0.91
            f["kick_y"] = f["kick_y"] * 0.91 + (f["vy"] - dy) * 0.08
            self.c.move(f["tag"], dx, dy)
            if f["y"] > H + 6:
                nx, ny = random.uniform(0, W), -6
                self.c.move(f["tag"], nx - f["x"], ny - f["y"])
                f["x"], f["y"] = nx, ny

    # ---------------------------------------------------------- widgets
    def hover(self, tag, shape, normal, over):
        self.c.tag_bind(tag, "<Enter>", lambda e: (self.c.itemconfig(shape, fill=over),
                                                    self.c.config(cursor="hand2")))
        self.c.tag_bind(tag, "<Leave>", lambda e: (self.c.itemconfig(shape, fill=normal),
                                                    self.c.config(cursor="")))

    def button(self, x, y, w, h, label, cmd, kind="normal"):
        self.nb += 1
        tag = f"b{self.nb}"
        fill, over, out = {"normal": (DEEP, "#6a58e8", "#7968ee"),
                           "primary": (PURPLE, "#a897ff", "#d9d2ff"),
                           "ghost": (INPUT, "#2a2766", "#3a3675")}[kind]
        shp = self.R(x, y, x + w, y + h, 16, tags=("content", tag), fill=fill, outline=out)
        self.T(x + w / 2, y + h / 2, label, 13 if kind == "primary" else 11, True, "white",
               "center", tags=("content", tag))
        self.hover(tag, shp, fill, over)
        self.c.tag_bind(tag, "<Button-1>", lambda e: cmd())

    def chip(self, group, value, x, y, w, h, label):
        self.nb += 1
        tag = f"b{self.nb}"
        shp = self.R(x, y, x + w, y + h, 12, tags=("content", tag), fill=INPUT, outline="#413c82")
        self.T(x + w / 2, y + h / 2, label, 10, True, TEXT, "center", tags=("content", tag))
        g = self.chips.setdefault(group, {"sel": None, "items": {}})
        g["items"][value] = shp
        self.c.tag_bind(tag, "<Enter>", lambda e: self.c.config(cursor="hand2"))
        self.c.tag_bind(tag, "<Leave>", lambda e: self.c.config(cursor=""))
        self.c.tag_bind(tag, "<Button-1>", lambda e: self.click_chip(group, value))

    def select_chip(self, group, value):
        g = self.chips[group]
        g["sel"] = value
        for v, s in g["items"].items():
            on = v == value
            self.c.itemconfig(s, fill=PURPLE if on else INPUT, outline=PURPLE2 if on else "#3a3675")

    def click_chip(self, group, value):
        self.select_chip(group, value)
        cb = self.chip_cb.get(group)
        if cb:
            cb(value)

    def switch(self, x, y, on, cmd):
        self.nb += 1
        tag = f"b{self.nb}"
        track = self.R(x, y, x + 46, y + 24, 12, tags=("content", tag), outline="")
        knob = self.c.create_oval(x + 3, self.HEADER + y + 3, x + 21, self.HEADER + y + 21,
                                  fill="white", outline="", tags=("content", tag))
        state = {"on": on}

        def paint():
            self.c.itemconfig(track, fill=PURPLE if state["on"] else "#2a2757")
            _, y0, _, y1 = self.c.coords(knob)
            nx = x + 25 if state["on"] else x + 3
            self.c.coords(knob, nx, y0, nx + 18, y1)

        def click(e):
            state["on"] = not state["on"]
            paint()
            cmd(state["on"])

        def setter(v):
            state["on"] = bool(v)
            paint()

        paint()
        self.c.tag_bind(tag, "<Enter>", lambda e: self.c.config(cursor="hand2"))
        self.c.tag_bind(tag, "<Leave>", lambda e: self.c.config(cursor=""))
        self.c.tag_bind(tag, "<Button-1>", click)
        return setter

    def slider(self, x, y, w, lo, hi, val, label, fmt, on_change, on_release=None):
        self.nb += 1
        tag = f"b{self.nb}"
        self.T(x, y, label, 11, True, TEXT, "nw")
        vt = self.T(x + w, y, fmt(val), 11, True, PURPLE2, "ne")
        ty = y + 38
        self.R(x, ty - 4, x + w, ty + 4, 4, tags=("content",), fill="#2a2757", outline="")
        frac = (val - lo) / (hi - lo)
        fill = self.c.create_rectangle(x, self.HEADER + ty - 4, x + w * frac, self.HEADER + ty + 4,
                                       fill=PURPLE, outline="", tags=("content", tag))
        px = x + w * frac
        knob = self.c.create_oval(px - 10, self.HEADER + ty - 10, px + 10, self.HEADER + ty + 10,
                                  fill="white", outline=PURPLE, width=3, tags=("content", tag))

        def setv(e):
            f = min(1, max(0, (e.x - x) / w))
            v = int(round(lo + f * (hi - lo)))
            fx0, fy0, fx1, fy1 = self.c.coords(fill)
            self.c.coords(fill, x, fy0, x + w * f, fy1)
            kx0, ky0, kx1, ky1 = self.c.coords(knob)
            self.c.coords(knob, x + w * f - 10, ky0, x + w * f + 10, ky1)
            self.c.itemconfig(vt, text=fmt(v))
            on_change(v)
            return v

        state = {"v": val}

        def press(e):
            state["v"] = setv(e)

        def release(e):
            if on_release:
                on_release(state["v"])

        self.c.tag_bind(tag, "<Button-1>", press)
        self.c.tag_bind(tag, "<B1-Motion>", press)
        self.c.tag_bind(tag, "<ButtonRelease-1>", release)
        self.c.tag_bind(tag, "<Enter>", lambda e: self.c.config(cursor="hand2"))
        self.c.tag_bind(tag, "<Leave>", lambda e: self.c.config(cursor=""))

    def glass(self, x1, y1, x2, y2, r=22):
        """Frosted panel in content space: soft shadow, rim light, top gloss."""
        self.R(x1 - 2, y1 + 4, x2 + 2, y2 + 10, r + 2, fill="#0c0a24", outline="")
        self.R(x1, y1 + 2, x2, y2 + 5, r, fill="#0a091f", outline="")
        self.R(x1, y1, x2, y2, r, fill=CARD, outline=BORDER)
        self.c.create_line(x1 + r, self.HEADER + y1 + 1.5, x2 - r, self.HEADER + y1 + 1.5,
                           fill="#6a66b8", width=1, tags=("content",))

    def card(self, y, h, title=None):
        self.glass(self.CX, y, self.CX + self.CW, y + h)
        if title:
            self.T(self.CX + 22, y + 20, title, 11, True, PURPLE2, "w")

    def section(self, name, icon, y, sub):
        self.sections.append((name, icon, y))
        self.T(self.CX, y, name, 24, True, "white")
        self.T(self.CX + 2, y + 38, sub, 10, False, MUTED)
        return y + 74

    # ---------------------------------------------------------- content
    def build_content(self):
        X, CW = self.CX, self.CW
        IN = CW - 44  # inner width
        y = 22

        # ===== Dashboard
        y = self.section("Dashboard", "◆", y, "Live status of your PC and one-click boost")
        self.card(y, 158, "Live status")
        self.stats = {}
        for i, (key, label) in enumerate((("cpu", "CPU"), ("ram", "MEMORY"), ("ping", "PING"))):
            tx = X + 22 + i * 204
            self.T(tx, y + 50, label, 9, True, MUTED)
            val = self.T(tx, y + 68, "--", 22, True, "white")
            sub = self.T(tx, y + 104, "", 9, False, MUTED)
            self.R(tx, y + 128, tx + 180, y + 136, 4, fill="#2a2757", outline="")
            bar = self.c.create_rectangle(tx, self.HEADER + y + 128, tx, self.HEADER + y + 136,
                                          fill=PURPLE, outline="", tags=("content",))
            self.stats[key] = (val, sub, bar, tx)
        y += 158 + 16

        self.card(y, 150, "Ping history  -  1.1.1.1")
        self.gx0, self.gx1 = X + 22, X + CW - 22
        self.gy0, self.gy1 = y + 50, y + 150 - 20
        for k in range(3):
            gy = self.gy0 + (self.gy1 - self.gy0) * k / 2
            self.c.create_line(self.gx0, self.HEADER + gy, self.gx1, self.HEADER + gy,
                               fill="#2a2757", tags=("content",))
        self.graph = self.c.create_line(self.gx0, self.HEADER + self.gy1, self.gx0 + 2, self.HEADER + self.gy1,
                                        fill=PURPLE2, width=2, tags=("content",))
        self.graph_txt = self.T(X + CW - 22, y + 20, "min -  avg -  max -", 9, False, MUTED, "e")
        y += 150 + 16

        self.card(y, 132, "Quick boost")
        self.T(X + 22, y + 44, "Ping, FPS, RAM, background apps, mouse and cleanup tweaks in one go.", 10, False, MUTED)
        self.button(X + 22, y + 70, IN, els := 44, "⚡  BOOST EVERYTHING", self.do_boost, "primary")
        y += 132 + 16

        self.card(y, 214, "Activity")
        self.log_items = []
        for i in range(9):
            self.log_items.append(self.T(X + 22, y + 48 + i * 17, "", 9, False, TEXT, "nw",
                                         width=IN, mono=True))
        y += 214 + 34

        # ===== System (hardware)
        y = self.section("System", "\u25a4", y, "Your PC parts: CPU, graphics card, RAM, motherboard, storage")
        hw_rows = (("cpu", "PROCESSOR", 54), ("cores", "CORES / CLOCK", 54), ("gpu", "GRAPHICS CARD", 54),
                   ("ram", "MEMORY", 54), ("board", "MOTHERBOARD", 54), ("os", "WINDOWS", 54),
                   ("disk", "STORAGE", 78))
        card_h = 50 + sum(r[2] for r in hw_rows) + 64
        self.card(y, card_h, "Hardware")
        self.hw_items = {}
        ry = y + 50
        for key, label, rh in hw_rows:
            self.T(X + 22, ry, label, 9, True, MUTED)
            self.hw_items[key] = self.T(X + 22, ry + 17, "detecting...", 10, True, TEXT, width=IN)
            ry += rh
        self.button(X + 22, ry + 4, 296, 44, "Refresh", self.do_refresh_hw)
        self.button(X + 330, ry + 4, 292, 44, "Copy specs", self.copy_specs, "ghost")
        y += card_h + 34

        # ===== Games
        y = self.section("Games", "▣", y, "Pick your game  •  drop PNG logos into the \"logos\" folder to show them")
        self.card(y, 384, "Choose a game")
        self.game_tiles = []
        if any(find_logo_file(g["slug"]) for g in GAMES):
            ensure_pil()
        for i, g in enumerate(GAMES):
            col, row = i % 3, i // 3
            tx = X + 22 + col * (192 + 11)
            ty = y + 52 + row * (70 + 12)
            tag = f"g{i}"
            shp = self.R(tx, ty, tx + 192, ty + 70, 14, tags=("content", tag), fill=INPUT, outline="#413c82")
            img = load_logo(g["slug"])
            icx, icy = tx + 38, self.HEADER + ty + 35
            if img is not None:
                self.logo_imgs.append(img)
                self.c.create_image(icx, icy, image=img, tags=("content", tag))
            else:  # clean white monogram emblem (no colours, no background)
                self.c.create_oval(icx - 20, icy - 20, icx + 20, icy + 20, outline="#ece8ff",
                                   width=2, tags=("content", tag))
                self.c.create_text(icx, icy, text=g["mono"], fill="white", tags=("content", tag),
                                   font=("Segoe UI", 9 if len(g["mono"]) > 3 else 11, "bold"))
            self.T(tx + 72, ty + 26, g["name"], 10, True, TEXT, "w", tags=("content", tag))
            self.T(tx + 72, ty + 48, g["genre"], 9, False, MUTED, "w", tags=("content", tag))
            self.c.tag_bind(tag, "<Enter>", lambda e: self.c.config(cursor="hand2"))
            self.c.tag_bind(tag, "<Leave>", lambda e: self.c.config(cursor=""))
            self.c.tag_bind(tag, "<Button-1>", lambda e, i=i: self.select_game(i))
            self.game_tiles.append(shp)
        y += 384 + 16

        self.card(y, 232, "Selected game")
        self.game_name = self.T(X + 22, y + 50, "", 17, True, "white")
        self.game_tip = self.T(X + 22, y + 84, "", 10, False, MUTED, width=IN)
        self.button(X + 22, y + 128, 380, 46, "Optimize this game", self.do_optimize_game, "primary")
        self.button(X + 414, y + 128, 204, 46, "Undo priority rule", self.do_undo_game, "ghost")
        self.T(X + 22, y + 198, "Auto-boost when the game launches", 11, False, TEXT, "w")
        self.switch(X + CW - 22 - 46, y + 186, False, self.set_auto)
        y += 232 + 34

        # ===== Network
        y = self.section("Network", "◎", y, "Lower ping, faster DNS, healthier connection")
        self.card(y, 262, "Ping & network")
        for i, (label, fn) in enumerate((("Ping Boost", tweak_network), ("Test Ping", ping_test))):
            self.button(X + 22 + i * 202, y + 50, 190, 46, label, lambda fn=fn: self.start(fn))
        self.button(X + 22 + 2 * 202, y + 50, 190, 46, "Reset Network", self.do_reset_net, "ghost")
        self.T(X + 22, y + 122, "DNS provider", 10, True, MUTED)
        for i, (key, label) in enumerate((("auto", "Automatic"), ("cloudflare", "Cloudflare"),
                                          ("google", "Google"), ("quad9", "Quad9"))):
            self.chip("dns", key, X + 22 + i * 152, y + 146, 140, 38, label)
        self.select_chip("dns", "cloudflare")
        self.button(X + 22, y + 200, IN, 46, "Apply DNS", lambda: self.start(set_dns, self.chips["dns"]["sel"]), "primary")
        y += 262 + 16
        self.card(y, 96)
        self.T(X + 22, y + 18, "Why it helps", 10, True, PURPLE2)
        self.T(X + 22, y + 40, "Ping Boost turns off Nagle's algorithm and network throttling. "
               "A faster DNS makes lookups quicker. Neither can beat your ISP's real distance to the server.",
               10, False, MUTED, width=IN)
        y += 96 + 34

        # ===== FPS
        y = self.section("FPS", "⚡", y, "Squeeze more frames out of your hardware")
        self.card(y, 168, "Power plan")
        for i, (key, label) in enumerate((("ultimate", "Ultimate"), ("high", "High Performance"),
                                          ("balanced", "Balanced (default)"))):
            self.chip("power", key, X + 22 + i * 202, y + 50, 190, 38, label)
        self.select_chip("power", "high")
        self.button(X + 22, y + 104, IN, 46, "Apply power plan",
                    lambda: self.start(set_power, self.chips["power"]["sel"]), "primary")
        y += 168 + 16
        self.card(y, 176, "Windows tweaks")
        self.button(X + 22, y + 50, 296, 46, "Game Mode + No Recording", lambda: self.start(tweak_gamemode, True))
        self.button(X + 330, y + 50, 296 - 4, 46, "Performance Visuals", lambda: self.start(visuals, True))
        self.button(X + 22, y + 108, 296, 46, "GPU Scheduling ON", lambda: self.start(gpu_sched))
        self.button(X + 330, y + 108, 296 - 4, 46, "Restore Visuals", lambda: self.start(visuals, False), "ghost")
        y += 176 + 16

        row_h = 66
        card_h = 50 + len(EXTRA_TWEAKS) * row_h + 6
        self.card(y, card_h, "Extra tweaks  -  switch ON to apply, OFF to undo")
        for i, t in enumerate(EXTRA_TWEAKS):
            ty = y + 48 + i * row_h
            self.T(X + 22, ty + 4, t["name"], 11, True, TEXT)
            self.T(X + 22, ty + 26, t["desc"], 9, False, MUTED, width=IN - 74)
            self.tweak_sw[t["key"]] = self.switch(X + CW - 22 - 46, ty + 8, tweak_is_on(t),
                                                  lambda on, t=t: self.toggle_tweak(t, on))
        y += card_h + 34

        # ===== Apps (process manager)
        y = self.section("Apps", "\u2630", y, "See what is open and pick exactly what to close")
        self.card(y, 590, "Running apps")
        self.proc_count = self.T(X + CW - 22, y + 20, "", 9, False, MUTED, "e")
        self.chip("procmode", "apps", X + 22, y + 46, 190, 34, "Open apps")
        self.chip("procmode", "bg", X + 224, y + 46, 220, 34, "Background processes")
        self.select_chip("procmode", "apps")
        self.chip_cb["procmode"] = self.proc_set_mode
        self.proc_rows = []
        for i in range(self.PROC_PER_PAGE):
            ry = y + 92 + i * 38
            tag = f"pr{i}"
            bg = self.R(X + 22, ry, X + CW - 22, ry + 34, 10, tags=("content", tag), fill=INPUT, outline="#34306b")
            box = self.R(X + 34, ry + 8, X + 52, ry + 26, 5, tags=("content", tag), fill=INPUT, outline="#6a66b8")
            tick = self.T(X + 43, ry + 17, "\u2713", 10, True, "white", "center", tags=("content", tag))
            name = self.T(X + 64, ry + 17, "", 10, True, TEXT, "w", tags=("content", tag))
            title = self.T(X + 262, ry + 17, "", 9, False, MUTED, "w", tags=("content", tag))
            mem = self.T(X + CW - 34, ry + 17, "", 10, True, PURPLE2, "e", tags=("content", tag))
            self.c.tag_bind(tag, "<Enter>", lambda e, bg=bg: (self.c.itemconfig(bg, fill="#211e52"),
                                                              self.c.config(cursor="hand2")))
            self.c.tag_bind(tag, "<Leave>", lambda e, bg=bg: (self.c.itemconfig(bg, fill=INPUT),
                                                              self.c.config(cursor="")))
            self.c.tag_bind(tag, "<Button-1>", lambda e, i=i: self.proc_toggle(i))
            self.proc_rows.append(dict(tag=tag, box=box, tick=tick, name=name, title=title, mem=mem))
        self.button(X + 22, y + 480, 120, 36, "\u25c0 Prev", self.proc_prev, "ghost")
        self.proc_page_txt = self.T(X + CW / 2, y + 498, "Page 1/1", 10, True, MUTED, "center")
        self.button(X + CW - 22 - 120, y + 480, 120, 36, "Next \u25b6", self.proc_next, "ghost")
        self.button(X + 22, y + 530, 190, 40, "Refresh", self.proc_refresh)
        self.button(X + 224, y + 530, 190, 40, "Select all", self.proc_select_all, "ghost")
        self.button(X + 426, y + 530, 192, 40, "Clear", self.proc_clear, "ghost")
        y += 590 + 16

        self.card(y, 244, "Close")
        self.proc_sel_txt = self.T(X + 22, y + 44, "", 10, False, MUTED, width=IN)
        self.button(X + 22, y + 82, 380, 46, "Close selected", self.do_close_selected, "primary")
        self.button(X + 414, y + 82, 204, 46, "Force close", lambda: self.do_close_selected(True), "ghost")
        self.T(X + 22, y + 154, "Also close my ticked apps when I hit BOOST", 11, False, TEXT, "w")
        self.switch(X + CW - 22 - 46, y + 142, False, lambda on: setattr(self, "boost_closes", on))
        self.T(X + 22, y + 182, "Close asks the app to quit (it may ask you to save). Force close ends it instantly "
               "and unsaved work is lost. Windows' own processes are hidden so you can't break Windows.",
               9, False, MUTED, width=IN)
        y += 244 + 34
        self.proc_paint()

        # ===== Mouse
        y = self.section("Mouse", "➤", y, "Clean 1:1 aim, snappy drag and the white trail")
        self.card(y, 312, "Pointer & trail")
        self.slider(X + 22, y + 48, IN, 1, 20, 10, "Pointer speed", lambda v: f"{v}/20",
                    lambda v: None, lambda v: pointer_speed(v) if IS_WIN else None)
        self.slider(X + 22, y + 118, IN, 0, 100, self.trail_delay, "Trail delay", lambda v: f"{v}%",
                    lambda v: setattr(self, "trail_delay", v))
        self.slider(X + 22, y + 188, IN, 6, 40, self.trail_len, "Trail length", lambda v: f"{v}",
                    lambda v: self.set_trail_len(v))
        self.T(X + 22, y + 270, "White mouse trail", 11, False, TEXT, "w")
        self.switch(X + CW - 22 - 46, y + 258, True, self.set_trail)
        y += 312 + 16
        self.card(y, 176, "Acceleration & drag")
        self.button(X + 22, y + 50, 296, 46, "Disable Acceleration", lambda: self.start(mouse_accel, False), "primary")
        self.button(X + 330, y + 50, 292, 46, "Restore Acceleration", lambda: self.start(mouse_accel, True), "ghost")
        self.button(X + 22, y + 108, 296, 46, "Snappy Drag (2px)", lambda: self.start(mouse_drag, True))
        self.button(X + 330, y + 108, 292, 46, "Default Drag (4px)", lambda: self.start(mouse_drag, False), "ghost")
        y += 176 + 34

        # ===== Cleanup
        y = self.section("Cleanup", "✧", y, "Free space and clear junk safely")
        self.card(y, 214, "Cleaner")
        self.button(X + 22, y + 50, 296, 46, "Clean Temp Files", lambda: self.start(clean_temp))
        self.button(X + 330, y + 50, 292, 46, "Empty Recycle Bin", lambda: self.start(clean_recycle))
        self.button(X + 22, y + 108, 296, 46, "Clear Thumbnail Cache", lambda: self.start(clean_thumbs))
        self.button(X + 330, y + 108, 292, 46, "Clean Everything", lambda: self.start(clean_all), "primary")
        self.T(X + 22, y + 176, "Files that are in use are skipped automatically.", 10, False, MUTED)
        y += 214 + 34

        # ===== Settings
        y = self.section("Settings", "⚙", y, "Looks, defaults and about")
        self.card(y, 198, "Appearance")
        self.T(X + 22, y + 48, "Purple theme enabled", 12, True, PURPLE2, "w")
        self.T(X + 22, y + 78, "Original HEPESmenu colors are restored.", 10, False, MUTED, "w")
        self.T(X + 22, y + 132, "Falling snow", 11, False, TEXT, "w")
        self.switch(X + CW - 22 - 46, y + 120, True, lambda on: self.c.itemconfig("snow", state="normal" if on else "hidden"))
        self.T(X + 22, y + 170, "Show the character", 11, False, TEXT, "w")
        self.switch(X + CW - 22 - 46, y + 158, True, lambda on: self.c.itemconfig("charitems", state="normal" if on else "hidden"))
        y += 198 + 16
        self.card(y, 150, "Defaults")
        self.T(X + 22, y + 46, "Undo everything HEPESmenu.free changed: mouse, power plan, DNS, visuals and network.",
               10, False, MUTED, width=IN)
        self.button(X + 22, y + 88, IN, 46, "Restore ALL defaults", self.do_restore, "ghost")
        y += 150 + 16
        self.card(y, 158, "License")
        ks = self.license_key_shown
        mk = ks[:4] + "-••••-••••-" + ks[-4:]
        self.T(X + 22, y + 48, "Key", 10, True, MUTED)
        self.T(X + 22, y + 66, mk, 14, True, TEXT, mono=True)
        self.T(X + CW - 22, y + 48, "Subscription", 10, True, MUTED, "ne")
        self.sub_card_text = self.T(X + CW - 22, y + 66, self.license_text(), 14, True, GOOD, "ne")
        self.button(X + 22, y + 104, IN, 40, "Lock now (ask for key again)", self.do_lock, "ghost")
        y += 158 + 16
        self.card(y, 120, "About")
        self.T(X + 22, y + 46, "HEPESmenu.free. Tweaks use normal Windows settings, so they are safe "
               "and reversible. A restart is recommended after Boost Everything.", 10, False, MUTED, width=IN)
        y += 120 + 30

        self.content_h = y
        self.view_h = H - self.HEADER - self.FOOT
        self.max_scroll = max(0, self.content_h - self.view_h)

    # ---------------------------------------------------------- chrome (fixed UI)
    def build_chrome(self):
        c = self.c
        # opaque masks hide content that scrolls out of view
        c.create_rectangle(0, 0, W, self.HEADER, fill="#100e29", outline="", tags="mask")
        c.create_line(0, self.HEADER, W, self.HEADER, fill="#38347a", width=1, tags="mask")
        c.create_rectangle(0, H - self.FOOT, W, H, fill="#100e29", outline="", tags="mask")
        c.create_line(0, H - self.FOOT, W, H - self.FOOT, fill="#2c2961", tags="mask")

        self.logo_small = tk.PhotoImage(data="".join(LOGO_SM_B64.split()))
        c.create_image(22, 36, image=self.logo_small, anchor="w", tags="fixed")
        c.create_text(98, 29, text=APP_NAME, anchor="w", fill="white",
                      font=("Segoe UI", 19, "bold"), tags="fixed")
        c.create_text(100, 53, text="ping  •  fps  •  mouse  •  cleanup", anchor="w", fill=MUTED,
                      font=("Segoe UI", 9), tags="fixed")
        # subscription + admin pills
        self.rr(W - 462, 22, W - 214, 50, 14, fill=INPUT, outline="#413c82", tags="fixed")
        self.sub_pill = c.create_text(W - 338, 36, text=f"SUBSCRIPTION  •  {self.license_text()}", fill=PURPLE2,
                      font=("Segoe UI", 9, "bold"), tags="fixed")
        adm = is_admin() if IS_WIN else False
        self.rr(W - 202, 22, W - 24, 50, 14, fill=INPUT, outline="#413c82", tags="fixed")
        self.badge = c.create_text(W - 113, 36, text="● ADMIN" if adm else "○ LIMITED (not admin)",
                                   fill=GOOD if adm else WARN, font=("Segoe UI", 9, "bold"), tags="fixed")

        self.status = c.create_text(24, H - self.FOOT / 2, text="Ready", anchor="w", fill=MUTED,
                                    font=("Segoe UI", 9), tags="fixed")
        c.create_text(W - 24, H - self.FOOT / 2, text=f"{APP_NAME}  •  scroll or use the menu",
                      anchor="e", fill="#6b68a3", font=("Segoe UI", 9), tags="fixed")

        # sidebar
        self.nav_pill = self.rr(14, self.NAV_TOP, 206, self.NAV_TOP + 40, 14, fill="#2c2863",
                                outline="#7c70ee", tags="fixed")
        self.nav_txt = []
        for i, (name, icon, _) in enumerate(self.sections):
            cy = self.NAV_TOP + i * self.NAV_H + 20
            c.create_text(36, cy, text=icon, fill=PURPLE2, font=("Segoe UI", 13, "bold"), tags="fixed")
            self.nav_txt.append(c.create_text(62, cy, text=name, anchor="w", fill=MUTED,
                                              font=("Segoe UI", 12, "bold"), tags="fixed"))
        self.nav_active = 0
        self.nav_y = float(self.NAV_TOP)
        self.pill_pos = float(self.NAV_TOP)
        self.paint_nav(0)

        # scrollbar
        self.sb_x = 890
        self.sb_top = self.HEADER + 12
        self.sb_bot = H - self.FOOT - 12
        c.create_line(self.sb_x, self.sb_top, self.sb_x, self.sb_bot, width=6, fill="#26235a",
                      capstyle="round", tags="fixed")
        self.sb_thumb = c.create_line(self.sb_x, self.sb_top, self.sb_x, self.sb_top + 60, width=6,
                                      fill=PURPLE, capstyle="round", tags="fixed")

        # character panel (no aura: soft floor shadow, twinkles, idle chatter)
        px0, py0, px1, py1 = self.RX, self.HEADER + 14, W - 20, H - self.FOOT - 14
        self.rr(px0 - 1, py0 + 3, px1 + 1, py1 + 8, 28, fill="#0a091f", outline="", tags=("fixed", "charitems"))
        self.rr(px0, py0, px1, py1, 26, fill="#15133a", outline="#4c4793", width=1, tags=("fixed", "charitems"))
        ccx = (px0 + px1) // 2
        self.sh_cx, self.sh_y = ccx, py1 - 14
        self.shadow = c.create_oval(0, 0, 0, 0, fill="#0a091f", outline="", tags=("fixed", "charitems"))
        self.shadow2 = c.create_oval(0, 0, 0, 0, fill="#070618", outline="", tags=("fixed", "charitems"))
        img_bottom = py1 - 26
        try:
            self.char_img = tk.PhotoImage(data="".join(IMG_B64.split()))
            self.char_image_item = c.create_image(ccx, img_bottom, image=self.char_img, anchor="s",
                           tags=("fixed", "charitems", "bob", "char"))
        except Exception:
            # Keep the UI usable if the optional character artwork is missing.
            try:
                self.char_img = tk.PhotoImage(data="".join(IMG_B64.split()))
                self.char_image_item = c.create_image(ccx, img_bottom, image=self.char_img, anchor="s",
                               tags=("fixed", "charitems", "bob", "char"))
            except Exception:
                pass
        mid = img_bottom - 260
        self.sparks = []
        for dx, dy, base, sp in ((-128, -215, 11, 0.050), (122, -185, 9, 0.037), (-142, -70, 8, 0.061),
                                 (134, -15, 12, 0.044), (-108, 95, 7, 0.055), (112, 150, 9, 0.040),
                                 (-62, -258, 7, 0.066)):
            item = c.create_polygon(star_pts(ccx + dx, mid + dy, 1), fill="#f1eeff", outline="",
                                    tags=("fixed", "charitems"))
            self.sparks.append(dict(item=item, x=ccx + dx, y=mid + dy, base=base, sp=sp,
                                    ph=random.uniform(0, 6.28)))
        bx0, by0, bx1, by1 = px0 + 22, py0 + 16, px1 - 22, py0 + 82
        self.rr(bx0, by0, bx1, by1, 16, fill="#232050", outline=PURPLE, width=2, tags=("fixed", "charitems"))
        c.create_polygon(ccx - 14, by1 - 1, ccx + 10, by1 - 1, ccx - 2, by1 + 14, fill="#232050",
                         outline=PURPLE, width=2, tags=("fixed", "charitems"))
        c.create_line(ccx - 12, by1 - 1, ccx + 8, by1 - 1, fill="#232050", width=3, tags=("fixed", "charitems"))
        self.bubble = c.create_text((bx0 + bx1) / 2, (by0 + by1) / 2, text=TALK[0],
                                    fill="white", font=("Segoe UI", 10, "bold"), width=bx1 - bx0 - 24,
                                    justify="center", tags=("fixed", "charitems"))
        c.tag_bind("char", "<Button-1>", lambda e: self.say(random.choice(TALK)))
        c.tag_bind("char", "<Enter>", lambda e: c.config(cursor="hand2"))
        c.tag_bind("char", "<Leave>", lambda e: c.config(cursor=""))

    def say(self, msg):
        self.c.itemconfig(self.bubble, text=msg)

    # ---------------------------------------------------------- events
    def bind_events(self):
        r, c = self.root, self.c
        r.bind_all("<MouseWheel>", lambda e: self.wheel(-e.delta * 1.2))
        r.bind_all("<Button-4>", lambda e: self.wheel(-120))
        r.bind_all("<Button-5>", lambda e: self.wheel(120))
        r.bind("<Up>", lambda e: self.wheel(-120))
        r.bind("<Down>", lambda e: self.wheel(120))
        r.bind("<Prior>", lambda e: self.wheel(-self.view_h * 0.9))
        r.bind("<Next>", lambda e: self.wheel(self.view_h * 0.9))
        r.bind("<Home>", lambda e: setattr(self, "target", 0.0))
        r.bind("<End>", lambda e: setattr(self, "target", self.max_scroll))
        c.bind("<Button-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<Motion>", self.on_motion)

    def wheel(self, d):
        self.target = min(self.max_scroll, max(0.0, self.target + d))

    def goto(self, idx):
        self.target = min(self.max_scroll, max(0.0, self.sections[idx][2] - 14))

    def nav_index(self, e):
        if e.x < self.SIDE and self.NAV_TOP <= e.y < self.NAV_TOP + len(self.sections) * self.NAV_H:
            return int((e.y - self.NAV_TOP) // self.NAV_H)
        return None

    def on_press(self, e):
        self.snow_click_reaction(e.x, e.y)
        idx = self.nav_index(e)
        if idx is not None:
            self.goto(idx)
        elif abs(e.x - self.sb_x) <= 9 and self.sb_top <= e.y <= self.sb_bot:
            self.sb_set(e.y)

    def snow_click_reaction(self, x, y):
        # A click sends nearby flakes drifting outward like a small snow puff.
        radius = 115.0
        for f in self.flakes:
            dx, dy = f["x"] - x, f["y"] - y
            dist = math.hypot(dx, dy)
            if 1.0 < dist < radius:
                strength = (1.0 - dist / radius) * 7.0
                f["kick_x"] += (dx / dist) * strength
                f["kick_y"] += (dy / dist) * strength - 1.8

    def on_drag(self, e):
        if abs(e.x - self.sb_x) <= 30 and self.sb_top - 20 <= e.y <= self.sb_bot + 20 and self.sb_dragging():
            self.sb_set(e.y)

    def sb_dragging(self):
        return True

    def sb_set(self, y):
        th = self.thumb_h()
        span = (self.sb_bot - self.sb_top) - th
        f = (y - self.sb_top - th / 2) / span if span > 0 else 0
        self.target = min(self.max_scroll, max(0.0, f * self.max_scroll))

    def on_motion(self, e):
        over = self.nav_index(e) is not None
        if over != self.nav_hover:
            self.nav_hover = over
            self.c.config(cursor="hand2" if over else "")

    def thumb_h(self):
        track = self.sb_bot - self.sb_top
        if self.max_scroll <= 0:
            return track
        return max(46, track * self.view_h / (self.view_h + self.max_scroll))

    def update_scrollbar(self):
        th = self.thumb_h()
        span = (self.sb_bot - self.sb_top) - th
        f = self.scroll / self.max_scroll if self.max_scroll > 0 else 0
        y0 = self.sb_top + span * f
        self.c.coords(self.sb_thumb, self.sb_x, y0 + 3, self.sb_x, y0 + th - 3)

    def paint_nav(self, idx):
        for i, t in enumerate(self.nav_txt):
            self.c.itemconfig(t, fill="white" if i == idx else MUTED)

    # ---------------------------------------------------------- actions
    def log(self, msg):
        self.q.put(msg)

    def start(self, fn, *args):
        if not IS_WIN:
            self.log("! Windows only.")
            return False
        if self.busy:
            self.log("...still working, one moment.")
            return False
        self.busy = True
        self.q.put(("say", "Working on it... ✦"))

        def worker():
            try:
                fn(self.log, *args)
                self.q.put(("say", "All done! ✦ Enjoy~"))
            except Exception as e:
                self.log(f"! Error: {e}")
                self.q.put(("say", "Oops, something went wrong."))
            finally:
                self.busy = False

        threading.Thread(target=worker, daemon=True).start()
        return True

    # ---------------------------------------------------------- extra tweaks / boost
    def toggle_tweak(self, t, on):
        snap_back = self.tweak_sw[t["key"]]
        if t["admin"] and IS_WIN and not is_admin():
            self.log(f"! {t['name']} needs Administrator - restart the app as admin.")
            snap_back(not on)
            return
        if not self.start(apply_tweak, t["key"], on):
            snap_back(not on)

    def do_boost(self):
        names = set(self.proc_sel) if self.boost_closes else set()
        if names:
            shown = [g["name"] for g in self.proc_all if g["name"].lower() in names] or sorted(names)
            lst = ", ".join(shown[:10]) + (" ..." if len(shown) > 10 else "")
            if not messagebox.askyesno("Boost + close apps",
                                       f"BOOST will also close:\n\n{lst}\n\n"
                                       "Unsaved work in them could be lost. Continue?"):
                return

        def job(log):
            if names:
                close_by_names(log, names, False)
            boost_all(log)
            self.q.put(("refresh", None))

        self.start(job)

    # ---------------------------------------------------------- apps / process manager
    @staticmethod
    def _fmt_mb(mb):
        return f"{mb / 1024:.1f} GB" if mb >= 1024 else f"{mb:.0f} MB"

    def proc_view(self):
        want_apps = self.chips["procmode"]["sel"] == "apps"
        return [g for g in self.proc_all if bool(g["title"]) == want_apps]

    def proc_chunk(self):
        view = self.proc_view()
        pages = max(1, -(-len(view) // self.PROC_PER_PAGE))
        self.proc_page = max(0, min(self.proc_page, pages - 1))
        s0 = self.proc_page * self.PROC_PER_PAGE
        return view[s0:s0 + self.PROC_PER_PAGE], pages, view

    def proc_paint(self):
        chunk, pages, view = self.proc_chunk()
        c = self.c
        for i, row in enumerate(self.proc_rows):
            if i >= len(chunk):
                c.itemconfig(row["tag"], state="hidden")
                continue
            g = chunk[i]
            on = g["name"].lower() in self.proc_sel
            c.itemconfig(row["tag"], state="normal")
            n = len(g["pids"])
            nm = g["name"][:22] + (f"  \u00d7{n}" if n > 1 else "")
            c.itemconfig(row["name"], text=nm)
            c.itemconfig(row["title"], text=(g["title"][:34] + ("..." if len(g["title"]) > 34 else "")))
            c.itemconfig(row["mem"], text=self._fmt_mb(g["mb"]))
            c.itemconfig(row["box"], fill=PURPLE if on else INPUT, outline=PURPLE2 if on else "#6a66b8")
            c.itemconfig(row["tick"], state="normal" if on else "hidden")
        kind = "apps" if self.chips["procmode"]["sel"] == "apps" else "processes"
        c.itemconfig(self.proc_count, text=f"{len(view)} {kind}  \u2022  {len(self.proc_sel)} selected")
        c.itemconfig(self.proc_page_txt, text=f"Page {self.proc_page + 1}/{pages}")
        sel = [g for g in self.proc_all if g["name"].lower() in self.proc_sel]
        if sel:
            names = ", ".join(g["name"] for g in sel[:6]) + (" ..." if len(sel) > 6 else "")
            c.itemconfig(self.proc_sel_txt,
                         text=f"Selected ({len(sel)}): {names}  -  about {self._fmt_mb(sum(g['mb'] for g in sel))} of RAM")
        else:
            c.itemconfig(self.proc_sel_txt, text="Nothing selected. Click rows above to tick the apps you want to close.")

    def proc_refresh(self):
        if not IS_WIN or self.proc_loading:
            return
        self.proc_loading = True
        self.c.itemconfig(self.proc_count, text="scanning...")

        def work():
            try:
                data = list_procs()
            except Exception:
                data = []
            self.q.put(("procs", data))

        threading.Thread(target=work, daemon=True).start()

    def proc_set_mode(self, _v=None):
        self.proc_page = 0
        self.proc_paint()

    def proc_toggle(self, i):
        chunk, _, _ = self.proc_chunk()
        if i < len(chunk):
            key = chunk[i]["name"].lower()
            self.proc_sel.symmetric_difference_update({key})
            self.proc_paint()

    def proc_prev(self):
        self.proc_page -= 1
        self.proc_paint()

    def proc_next(self):
        self.proc_page += 1
        self.proc_paint()

    def proc_select_all(self):
        self.proc_sel |= {g["name"].lower() for g in self.proc_view()}
        self.proc_paint()

    def proc_clear(self):
        self.proc_sel.clear()
        self.proc_paint()

    def do_close_selected(self, force=False):
        sel = [g for g in self.proc_all if g["name"].lower() in self.proc_sel]
        if not sel:
            self.log("Tick at least one app first (click a row in the Apps list).")
            return
        lst = ", ".join(g["name"] for g in sel[:12]) + (" ..." if len(sel) > 12 else "")
        how = ("FORCE close (instant, unsaved work is lost)" if force
               else "Close (apps may ask you to save first)")
        if not messagebox.askyesno("Close apps", f"{how}:\n\n{lst}\n\nContinue?"):
            return
        names = {g["name"].lower() for g in sel}

        def job(log):
            close_by_names(log, names, force)
            self.q.put(("refresh", None))

        self.start(job)

    def select_game(self, i):
        self.sel_game = i
        self.boosted.clear()
        for k, s in enumerate(self.game_tiles):
            on = k == i
            self.c.itemconfig(s, fill="#2f2b6b" if on else INPUT, outline=PURPLE2 if on else "#3a3675")
        g = GAMES[i]
        self.c.itemconfig(self.game_name, text=g["name"])
        self.c.itemconfig(self.game_tip, text=g["tip"])

    def do_optimize_game(self):
        self.start(optimize_game, GAMES[self.sel_game])

    def do_undo_game(self):
        self.start(undo_game, GAMES[self.sel_game])

    def set_auto(self, on):
        self.auto_boost = on
        self.log("Auto-boost ON: I'll boost the game when it starts." if on else "Auto-boost OFF.")

    def do_reset_net(self):
        if messagebox.askyesno("Reset network",
                               "This resets Winsock and the IP stack and needs a restart.\n\nContinue?"):
            self.start(reset_network)

    def do_restore(self):
        if messagebox.askyesno("Restore defaults", "Restore Windows defaults for everything changed here?"):
            self.start(restore_all)

    def do_lock(self):
        try:
            subprocess.Popen([sys.executable, os.path.abspath(__file__)])
        except Exception:
            self.log("! Could not restart.")
            return
        self.root.destroy()
        sys.exit(0)

    def do_refresh_hw(self):
        for it in self.hw_items.values():
            self.c.itemconfig(it, text="detecting...")
        threading.Thread(target=self.hw_loop, daemon=True).start()

    def copy_specs(self):
        names = (("cpu", "CPU"), ("cores", "Cores"), ("gpu", "GPU"), ("ram", "RAM"),
                 ("board", "Board"), ("os", "OS"), ("disk", "Storage"))
        txt = "\n".join(f"{n}: {self.hw_text.get(k, '?')}" for k, n in names)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self.log("Specs copied to clipboard.")
        except Exception:
            self.log("! Could not copy.")

    def hw_loop(self):
        try:
            info = get_hw_info()
        except Exception as e:
            info = {k: f"error: {e}" for k in ("cpu", "cores", "gpu", "ram", "board", "os", "disk")}
        self.q.put(("hw", info))

    def check_admin(self):
        if not IS_WIN or is_admin():
            return
        if messagebox.askyesno("Administrator needed",
                               "Network, DNS and GPU tweaks need Administrator rights.\n\n"
                               "Restart HEPESmenu.free as admin now?"):
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                    f'"{os.path.abspath(__file__)}"', None, 1)
                self.root.destroy()
                sys.exit(0)
            except Exception:
                self.log("! Could not elevate.")

    # ---------------------------------------------------------- background threads
    def ping_loop(self):
        while True:
            out = run("ping -n 1 -w 1000 1.1.1.1")
            m = re.search(r"[=<]\s*(\d+)\s*ms", out)
            self.ping_now = int(m.group(1)) if m else None
            if self.ping_now is not None:
                self.ping_hist.append(self.ping_now)
            self.ping_ver += 1
            time.sleep(2.5)

    def auto_loop(self):
        while True:
            time.sleep(5)
            if not self.auto_boost:
                continue
            for exe in GAMES[self.sel_game]["exes"]:
                out = run(f'tasklist /FI "IMAGENAME eq {exe}" /NH').lower()
                running = exe[:20].lower() in out
                if running and exe not in self.boosted:
                    set_live_priority(exe)
                    self.boosted.add(exe)
                    self.log(f"Auto-boosted {exe} to HIGH priority.")
                elif not running:
                    self.boosted.discard(exe)

    # ---------------------------------------------------------- live stats
    def set_stat(self, key, text, sub, frac, color=PURPLE):
        val, subt, bar, tx = self.stats[key]
        self.c.itemconfig(val, text=text)
        self.c.itemconfig(subt, text=sub)
        x0, y0, x1, y1 = self.c.coords(bar)
        self.c.coords(bar, tx, y0, tx + 180 * min(1, max(0.0, frac)), y1)
        self.c.itemconfig(bar, fill=color)

    def update_stats(self):
        if IS_WIN:
            try:
                idle, ker, usr = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
                ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(ker), ctypes.byref(usr))
                cur = (idle.value, ker.value, usr.value)
                if self.cpu_prev:
                    di = cur[0] - self.cpu_prev[0]
                    dt = (cur[1] - self.cpu_prev[1]) + (cur[2] - self.cpu_prev[2])
                    pct = 100 * (1 - di / dt) if dt else 0
                    self.set_stat("cpu", f"{pct:.0f}%", "processor load", pct / 100,
                                  PURPLE if pct < 80 else WARN)
                self.cpu_prev = cur
                ms = MEMSTAT()
                ms.dwLength = ctypes.sizeof(MEMSTAT)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
                used = (ms.ullTotalPhys - ms.ullAvailPhys) / 1073741824
                tot = ms.ullTotalPhys / 1073741824
                self.set_stat("ram", f"{ms.dwMemoryLoad}%", f"{used:.1f} / {tot:.1f} GB",
                              ms.dwMemoryLoad / 100, PURPLE if ms.dwMemoryLoad < 85 else WARN)
            except Exception:
                pass
            p = self.ping_now
            if p is None:
                self.set_stat("ping", "-- ms", "waiting / timeout", 0)
            else:
                col = GOOD if p < 40 else (PURPLE if p < 90 else WARN)
                self.set_stat("ping", f"{p} ms", "to 1.1.1.1", p / 200, col)
        else:
            self.set_stat("cpu", "n/a", "windows only", 0)

    def update_graph(self):
        pts = list(self.ping_hist)
        if len(pts) < 2:
            return
        top = max(60, max(pts) * 1.2)
        n = len(pts)
        coords = []
        for i, v in enumerate(pts):
            x = self.gx0 + (self.gx1 - self.gx0) * i / (n - 1)
            y = self.gy1 - (self.gy1 - self.gy0) * (v / top)
            coords += [x, self.HEADER + y - self.scroll]
        self.c.coords(self.graph, *coords)
        self.c.itemconfig(self.graph_txt,
                          text=f"min {min(pts)}   avg {sum(pts) // n}   max {max(pts)} ms")

    # ---------------------------------------------------------- mouse trail
    def set_trail(self, on):
        self.trail_on = on
        if self.ov is not None:
            self.ov.deiconify() if on else self.ov.withdraw()

    def set_trail_len(self, n):
        self.trail_len = n
        self.paint_trail()

    def paint_trail(self):
        n = self.trail_len
        for item in self.dots:
            self.oc.itemconfig(item, fill="#ffffff")

    def make_trail(self):
        try:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.ov = tk.Toplevel(self.root)
            self.ov.overrideredirect(True)
            self.ov.geometry(f"{sw}x{sh}+0+0")
            self.ov.attributes("-topmost", True)
            key = "#010101"
            self.ov.configure(bg=key)
            self.ov.attributes("-transparentcolor", key)
            self.oc = tk.Canvas(self.ov, width=sw, height=sh, bg=key, highlightthickness=0)
            self.oc.pack()
            self.trail_line = self.oc.create_line(
                0, 0, 0, 0, fill="#ffffff", width=4,
                smooth=True, splinesteps=18, capstyle=tk.ROUND, joinstyle=tk.ROUND
            )
            self.dots = [self.oc.create_oval(0, 0, 0, 0, fill="#ffffff", outline="") for _ in range(40)]
            self.hist = deque(maxlen=40)
            self.head = None
            self.paint_trail()
            self.ov.update_idletasks()
            if IS_WIN:
                hwnd = ctypes.windll.user32.GetParent(self.ov.winfo_id()) or self.ov.winfo_id()
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20 | 0x80)
        except Exception:
            self.ov = None

    def tick_trail(self):
        if not self.trail_on or self.ov is None:
            return
        px, py = self.root.winfo_pointerxy()
        if self.head is None:
            self.head = [px, py]
        ease = 0.45 - 0.0037 * self.trail_delay
        self.head[0] += (px - self.head[0]) * ease
        self.head[1] += (py - self.head[1]) * ease
        self.hist.append((self.head[0], self.head[1]))
        n = self.trail_len
        pts = list(self.hist)[-n:]
        pad = n - len(pts)
        if len(pts) >= 2:
            line_coords = [coord for point in pts for coord in point]
            self.oc.coords(self.trail_line, *line_coords)
        else:
            self.oc.coords(self.trail_line, 0, 0, 0, 0)
        for k, item in enumerate(self.dots):
            j = k - pad
            if k >= n or j < 0:
                self.oc.coords(item, 0, 0, 0, 0)
                continue
            x, y = pts[j]
            r = 1.2 + 5.6 * (k / max(1, n - 1))
            self.oc.coords(item, x - r, y - r, x + r, y + r)

    # ---------------------------------------------------------- main loop
    def frame(self):
        self.fc += 1
        self.tick_snow()
        if self.shake:
            self.c.move("gate", self.shake.pop(0), 0)
        if self.gate_ring is not None and not self.main_ready:
            k = (math.sin(self.fc * 0.05) + 1) / 2
            ca, cb = (0x3a, 0x36, 0x80), (0xa9, 0x9c, 0xff)
            col = "#%02x%02x%02x" % tuple(int(x + (y - x) * k) for x, y in zip(ca, cb))
            self.c.itemconfig(self.gate_ring, outline=col)
        if self.main_ready:
            self.main_frame()
        self.root.after(8, self.frame)

    def main_frame(self):
        diff = self.target - self.scroll
        if abs(diff) > 0.3:
            step = diff * 0.17
            self.c.move("content", 0, -step)
            self.scroll += step
            self.update_scrollbar()
        elif diff != 0:
            self.c.move("content", 0, -diff)
            self.scroll = self.target
            self.update_scrollbar()

        # which section is on screen -> nav highlight
        idx = 0
        for i, (_, _, sy) in enumerate(self.sections):
            if sy - 90 <= self.scroll:
                idx = i
        if self.max_scroll > 0 and self.scroll >= self.max_scroll - 4:
            idx = len(self.sections) - 1
        if idx != self.nav_active:
            self.nav_active = idx
            self.paint_nav(idx)
        goal = self.NAV_TOP + idx * self.NAV_H
        self.nav_y += (goal - self.nav_y) * 0.22
        self.c.move(self.nav_pill, 0, self.nav_y - self.pill_pos)
        self.pill_pos = self.nav_y

        # anime girl: gentle float + sway, shadow breathes, sparkles twinkle
        a = self.fc * 0.0225
        self.c.move("bob", math.cos(self.fc * 0.015) * 0.025, math.sin(a) * 0.11)
        sc = 1 - math.cos(a) * 4.9 / 28
        cx, cy = self.sh_cx, self.sh_y
        self.c.coords(self.shadow, cx - 62 * sc, cy - 8 * sc, cx + 62 * sc, cy + 8 * sc)
        self.c.coords(self.shadow2, cx - 40 * sc, cy - 5 * sc, cx + 40 * sc, cy + 5 * sc)
        for sp in self.sparks:
            k = abs(math.sin(self.fc * sp["sp"] * 0.5 + sp["ph"])) ** 3
            self.c.coords(sp["item"], *star_pts(sp["x"], sp["y"], max(0.6, sp["base"] * k)))
        if self.fc % 720 == 0 and not self.busy:
            self.say(random.choice(TALK))

        self.tick_trail()

        if self.fc % 45 == 1:
            self.update_stats()
        if self.shown_ver != self.ping_ver:
            self.shown_ver = self.ping_ver
            self.update_graph()

        # drain log queue
        try:
            while True:
                m = self.q.get_nowait()
                if isinstance(m, tuple):
                    if m[0] == "hw":
                        self.hw_text = m[1]
                        for k, it in self.hw_items.items():
                            self.c.itemconfig(it, text=m[1].get(k, "unknown"))
                        self.log("Hardware info loaded.")
                    elif m[0] == "procs":
                        self.proc_loading = False
                        self.proc_all = m[1]
                        self.proc_sel &= {g["name"].lower() for g in m[1]}
                        self.proc_paint()
                    elif m[0] == "refresh":
                        self.proc_refresh()
                    else:
                        self.say(m[1])
                    continue
                self.logs.append(m)
                self.c.itemconfig(self.status, text=m)
                off = 9 - len(self.logs)
                for i, it in enumerate(self.log_items):
                    self.c.itemconfig(it, text=self.logs[i - off] if i >= off else "")
        except queue.Empty:
            pass

    def go(self):
        self.root.mainloop()


IMG_B64 = "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"
LOGO_SM_B64 = "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"
LOGO_BIG_B64 = "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"
ICON_B64 = "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"

if __name__ == "__main__":
    App().go()
