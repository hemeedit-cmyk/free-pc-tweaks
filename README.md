# HEPESmenu.free

A Windows PC/gaming optimizer with a purple-themed UI: ping and network
tweaks, FPS/power tweaks, a running-apps manager, mouse tweaks, and
one-click cleanup.

---

## 1. Requirements

- **Windows 10 or 11** (the tweaks use Windows-only APIs; on other OSes
  only the UI runs, with optimization features disabled)
- **Python 3.10+** — https://www.python.org/downloads/
  - When installing, check **"Add python.exe to PATH"**
  - Also keep **"tcl/tk and IDLE"** checked (this gives you `tkinter`,
    which the app's UI is built with)
- Internet access the first time you run it, so `requirements.bat` can
  install Pillow (used only for the game logo icons; optional)

No other accounts or paid services are required to run the app itself.

---

## 2. Folder layout

```
HEPESmenu/
├── HEPESmenu.py        the app
├── requirements.bat     one-click setup + launcher
├── README.md             this file
└── logos/               optional game logo images (created automatically)
```

### Adding game logos (optional)

Drop PNG (or WEBP/JPG) files into the `logos` folder, named to match the
game's slug:

| File name           | Game              |
|---------------------|-------------------|
| `fortnite.png`       | Fortnite          |
| `valorant.png`       | Valorant          |
| `cs2.png`             | CS2               |
| `apex.png`            | Apex Legends      |
| `lol.png`              | League of Legends |
| `overwatch.png`       | Overwatch 2       |
| `gta5.png`             | GTA V             |
| `cod.png`              | Call of Duty      |
| `rocketleague.png`   | Rocket League     |
| `roblox.png`           | Roblox            |
| `r6.png`                | Rainbow Six Siege |
| `minecraft.png`       | Minecraft (Java)  |

If a game has no matching file, the app draws a simple white monogram
instead — this is optional and the app works fine without any logos.

---

## 3. Setup and first run

1. Put `HEPESmenu.py`, `requirements.bat`, and `README.md` in the same
   folder.
2. Double-click **`requirements.bat`**.
   - It checks that Python is installed and on PATH.
   - It checks the Python version (3.8+ required, 3.10+ recommended).
   - It makes sure `tkinter` is available.
   - It installs **Pillow** if it's missing (for logo icons).
   - It then launches the app automatically.
3. On first launch you'll see a license key screen. Enter your key in
   the format `XXXX-XXXX-XXXX-XXXX` (dashes are added for you as you
   type) and press **Activate**. If you don't have a key, use the
   **"GET FREE LICENSE HERE"** button on that screen to open the
   app's Discord server and request one.

After activating, the app restarts into the main dashboard.

### Running it again later

Just double-click `requirements.bat` again — it re-checks everything
and launches the app. You can also run it directly with:

```
python HEPESmenu.py
```

from a command prompt in the app's folder (once Python/Pillow are set
up).

---

## 4. Using the app

The app is organized into sections, reachable from the left sidebar or
by scrolling:

- **Dashboard** — live CPU/RAM/ping stats, a ping history graph, an
  activity log, and the **BOOST EVERYTHING** button that runs all the
  tweaks below in one go.
- **System** — detected CPU, GPU, RAM, motherboard, Windows version,
  and storage info (with a "copy specs" button).
- **Games** — pick a game to boost its process priority, see a quick
  in-game settings tip, and optionally turn on auto-boost so the app
  boosts it automatically whenever it launches.
- **Network** — ping/Nagle tweaks, a ping tester, a full network
  reset, and DNS provider switching (Cloudflare/Google/Quad9/Automatic).
- **FPS** — power plan switching (Balanced/High/Ultimate), Game Mode,
  performance visuals, GPU scheduling, and a set of toggle switches for
  background apps, fullscreen optimizations, CPU throttling, foreground
  priority, and Windows Update uploads.
- **Apps** — see everything running (open apps or background
  processes), tick items, and close or force-close them; optionally
  have ticked apps close automatically whenever you hit BOOST.
- **Mouse** — pointer speed, acceleration on/off, drag sensitivity, and
  a white mouse trail with adjustable length/delay.
- **Cleanup** — clear temp files, empty the Recycle Bin, clear the
  thumbnail cache, or do all three at once.
- **Settings** — toggle the snow/character effects, restore all
  Windows defaults the app has changed, and re-lock the app (asks for
  the license key again).

### Administrator rights

Several tweaks (network/Nagle settings, DNS changes, GPU scheduling,
CPU throttling/priority tweaks, Windows Update upload blocking) need
the app to run **as Administrator**. If you're not running elevated,
the app will offer to restart itself as admin on launch, and any admin
action you try otherwise will be skipped with a note in the Activity
log telling you it needs elevation.

### Restoring defaults

If you want to undo everything the app has changed (mouse settings,
power plan, DNS, visuals, network tweaks), go to **Settings → Restore
ALL defaults**.

---

## 5. Troubleshooting

**"Python was not found on this PC"**
Install Python from python.org and make sure "Add python.exe to PATH"
was checked, then run `requirements.bat` again.

**Logos don't show up / look like plain circles with text**
That's the fallback monogram — either you haven't added a logo file for
that game yet, or Pillow failed to install. Re-run `requirements.bat`
to retry installing Pillow, or add PNG files to the `logos` folder as
described above.

**Network/DNS/GPU scheduling tweaks say "needs Administrator - skipped"**
Right-click `requirements.bat` (or a shortcut to it) and choose **Run as
administrator**, or allow the app's own "Restart as Administrator?"
prompt when it appears on launch.

**The app won't start / closes immediately**
Run it from a command prompt instead of double-clicking, so you can see
the error message:
```
python HEPESmenu.py
```

**License key issues (invalid, expired, revoked, too many tries)**
Use the **"GET FREE LICENSE HERE"** button on the license screen to
reach the app's Discord server and request help with your key.

---

## 6. Notes

- Everything the app changes uses normal, documented Windows settings
  (registry values, `netsh`, `powercfg`), so the changes are visible
  and reversible from **Settings → Restore ALL defaults**.
- A restart is recommended after running **BOOST EVERYTHING** so all
  tweaks take full effect.
- This app only works on Windows; on other platforms the window opens
  but optimization buttons are disabled.
