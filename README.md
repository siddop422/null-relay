# Null Relay

Atmospheric 2D pixel-art survival / psychological horror game written in Python with Pygame.

You are a field technician sent into the sealed subterranean Signal Relay Station **Null-7**. The previous crew vanished during a deep-band amplification experiment. Something answered the signal. Repair the generators, read the logs, manage your light and sanity, and decide whether to escape, confront the truth, or stay forever.

## Features
- Procedural pixel-art sprites, tiles, lighting and SFX (no external asset files required)
- Flashlight + battery, stamina, sanity/tension systems
- Horror entity with full state-machine AI (patrol → investigate → stalk → chase)
- Environmental storytelling via readable logs and blood trails
- Three endings: Escape / Truth / Trapped
- Clean nearest-neighbor scaling (320×180 native)
- Ready for single-file Windows `.exe` via PyInstaller

## Controls
| Key | Action |
|-----|--------|
| WASD / Arrows | Move |
| Shift | Sprint (stamina) |
| F | Toggle flashlight |
| E / Space | Interact (notes, generators) |
| Tab | Journal |
| Esc | Pause / quit on ending |

## Run from source
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Build single Windows .exe
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name NullRelay --paths src src/main.py
```
The executable appears in `dist/NullRelay.exe`. All art and sound are generated at runtime — zero missing-asset errors.

## Endings
- **Escape** – stabilize both generator nodes and reach the surface lock.
- **Truth** – collect the major logs and enter the far containment zone.
- **Trapped** – let sanity reach zero.

## License
MIT – do whatever you want with it.
