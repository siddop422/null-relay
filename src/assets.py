"""
Procedural pixel-art generation + simple synthesized SFX.
Everything is created at runtime so the .exe never looks for missing files.
"""
import pygame
import math
import random
from typing import Dict, Tuple, List

# Native resolution (crisp nearest-neighbor scaling)
NATIVE_W, NATIVE_H = 320, 180
SCALE = 4  # final window ≈ 1280×720

def make_pixel_surface(w: int, h: int) -> pygame.Surface:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    return s

def draw_pixel_rect(surf: pygame.Surface, x: int, y: int, w: int, h: int, color: Tuple[int, int, int, int]):
    pygame.draw.rect(surf, color, (x, y, w, h))

# ---------- Palette ----------
PAL = {
    "black": (8, 6, 12),
    "dark": (18, 14, 22),
    "mid": (40, 32, 48),
    "light": (90, 78, 110),
    "white": (220, 210, 230),
    "blood": (140, 20, 30),
    "warn": (200, 80, 40),
    "green": (40, 160, 90),
    "cyan": (60, 180, 200),
    "purple": (120, 60, 160),
    "flicker": (255, 240, 180),
}

def generate_player_frames() -> Dict[str, List[pygame.Surface]]:
    frames = {"idle": [], "walk": [], "run": []}
    for i in range(4):
        s = make_pixel_surface(12, 16)
        # body
        draw_pixel_rect(s, 4, 4, 4, 6, (*PAL["light"], 255))
        # head
        draw_pixel_rect(s, 3, 1, 6, 4, (*PAL["white"], 255))
        # legs
        offset = (i % 2) * 1
        draw_pixel_rect(s, 3 + offset, 10, 2, 5, (*PAL["mid"], 255))
        draw_pixel_rect(s, 7 - offset, 10, 2, 5, (*PAL["mid"], 255))
        # flashlight held
        draw_pixel_rect(s, 8, 6, 3, 2, (*PAL["flicker"], 255))
        frames["idle"].append(s)
        frames["walk"].append(s.copy())
        frames["run"].append(s.copy())
    return frames

def generate_entity_frames() -> Dict[str, List[pygame.Surface]]:
    """Glitchy signal entity – morphing silhouette."""
    frames = {"idle": [], "patrol": [], "chase": [], "attack": [], "glitch": []}
    for state, count in [("idle", 4), ("patrol", 6), ("chase", 4), ("attack", 3), ("glitch", 5)]:
        for i in range(count):
            s = make_pixel_surface(20, 28)
            # base tall form
            body_col = PAL["purple"] if state != "glitch" else random.choice([PAL["blood"], PAL["cyan"], PAL["purple"]])
            draw_pixel_rect(s, 6, 4, 8, 16, (*body_col, 220))
            # head / sensor
            draw_pixel_rect(s, 5, 0, 10, 6, (*PAL["black"], 255))
            draw_pixel_rect(s, 7, 1, 6, 3, (*PAL["cyan"], 255))
            # tendrils / glitch
            for t in range(3):
                tx = 4 + t * 4 + (i % 3) - 1
                ty = 18 + (i % 2)
                draw_pixel_rect(s, tx, ty, 2, 6 + (i % 3), (*body_col, 180))
            if state == "glitch":
                # noise pixels
                for _ in range(12):
                    px = random.randint(0, 19)
                    py = random.randint(0, 27)
                    s.set_at((px, py), random.choice([PAL["cyan"], PAL["blood"], PAL["white"]]))
            frames[state].append(s)
    return frames

def generate_tiles() -> Dict[str, pygame.Surface]:
    tiles = {}
    # floor
    floor = make_pixel_surface(16, 16)
    floor.fill(PAL["dark"])
    for y in range(0, 16, 4):
        for x in range(0, 16, 4):
            if (x + y) % 8 == 0:
                draw_pixel_rect(floor, x, y, 2, 2, (*PAL["mid"], 80))
    tiles["floor"] = floor

    # wall
    wall = make_pixel_surface(16, 16)
    wall.fill(PAL["black"])
    draw_pixel_rect(wall, 0, 0, 16, 3, (*PAL["mid"], 255))
    draw_pixel_rect(wall, 0, 13, 16, 3, (*PAL["mid"], 255))
    tiles["wall"] = wall

    # door
    door = make_pixel_surface(16, 16)
    door.fill(PAL["mid"])
    draw_pixel_rect(door, 2, 2, 12, 12, (*PAL["dark"], 255))
    draw_pixel_rect(door, 6, 6, 4, 4, (*PAL["cyan"], 180))
    tiles["door"] = door

    # blood
    blood = make_pixel_surface(16, 16)
    blood.fill((0, 0, 0, 0))
    for _ in range(8):
        bx = random.randint(2, 12)
        by = random.randint(4, 14)
        draw_pixel_rect(blood, bx, by, random.randint(1, 3), random.randint(1, 2), (*PAL["blood"], 200))
    tiles["blood"] = blood

    # generator / console
    gen = make_pixel_surface(16, 16)
    gen.fill(PAL["dark"])
    draw_pixel_rect(gen, 2, 4, 12, 10, (*PAL["mid"], 255))
    draw_pixel_rect(gen, 4, 6, 3, 2, (*PAL["green"], 255))
    draw_pixel_rect(gen, 9, 6, 3, 2, (*PAL["warn"], 255))
    tiles["console"] = gen

    # note / log
    note = make_pixel_surface(16, 16)
    note.fill((0, 0, 0, 0))
    draw_pixel_rect(note, 3, 3, 10, 12, (*PAL["white"], 220))
    draw_pixel_rect(note, 4, 5, 8, 1, (*PAL["dark"], 255))
    draw_pixel_rect(note, 4, 8, 6, 1, (*PAL["dark"], 255))
    tiles["note"] = note

    return tiles

def generate_flashlight_mask(radius: int = 70) -> pygame.Surface:
    """Soft circular falloff for the flashlight cone (pre-rendered)."""
    size = radius * 2
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            dx = x - radius
            dy = y - radius
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < radius:
                alpha = int(255 * (1.0 - (dist / radius) ** 1.6))
                mask.set_at((x, y), (255, 240, 200, max(0, min(255, alpha))))
    return mask

def generate_vignette(w: int, h: int) -> pygame.Surface:
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    max_d = math.sqrt(cx * cx + cy * cy)
    for y in range(h):
        for x in range(w):
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            a = int(180 * (d / max_d) ** 2.2)
            vig.set_at((x, y), (0, 0, 0, min(220, a)))
    return vig

# Simple procedural SFX (short noise bursts)
def make_beep(freq: int = 440, duration_ms: int = 80, volume: float = 0.3) -> pygame.mixer.Sound:
    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        val = int(127 + 127 * volume * math.sin(2 * math.pi * freq * t) * (1 - t * 8))
        buf.append(max(0, min(255, val)))
    sound = pygame.mixer.Sound(buffer=bytes(buf))
    return sound

def make_noise(duration_ms: int = 120, volume: float = 0.25) -> pygame.mixer.Sound:
    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray(random.randint(0, 255) for _ in range(n_samples))
    # simple envelope
    for i in range(n_samples):
        env = 1.0 - (i / n_samples)
        buf[i] = int(buf[i] * volume * env)
    return pygame.mixer.Sound(buffer=bytes(buf))
