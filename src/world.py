import pygame
from typing import List, Tuple, Dict, Optional
from assets import generate_tiles, PAL

# Simple tile map (0=floor, 1=wall, 2=door, 3=blood, 4=console, 5=note)
# Multi-room layout: Lobby → Corridor → Power → Archives → Containment
MAP_DATA = [
    # 0-19 y, 0-39 x   (each tile 16 px → 640×320 world)
    "1111111111111111111111111111111111111111",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1000000040000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1111111100000000000000000000011111111111",
    "1000000100000000000000000000010000000001",
    "1000000100000000000000000000010000000001",
    "1000000100000000000000000000010000000001",
    "1000000100000000000000000000010000000001",
    "1000000100000000000000000000010000000001",
    "1000000111111111111111111111110000000001",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1000000000000000000000000000000000000001",
    "1111111111111111111111111111111111111111",
]

NOTES = {
    (8, 3): "LOG 01 – Dr. Voss: Amplification test scheduled. Crew reports 'voices' in the static. Ignore.",
    (25, 9): "LOG 04 – Technician R.: Power fluctuations in Containment. Something is drawing current that isn't on the grid.",
    (12, 15): "PERSONAL – I can hear it breathing when the lights flicker. It knows when I turn the flashlight on.",
    (30, 5): "FINAL ENTRY – We opened a door that should have stayed closed. The signal is not ours. It is using the relay to call more of itself.",
}

class World:
    def __init__(self):
        self.tiles = generate_tiles()
        self.tile_size = 16
        self.map: List[str] = MAP_DATA
        self.h = len(self.map)
        self.w = len(self.map[0])
        self.notes = NOTES.copy()
        self.generators_fixed = 0
        self.exit_open = False
        self.blood_trails: List[Tuple[int, int]] = [(15, 8), (18, 9), (22, 10)]

    def collides(self, x: float, y: float, w: float, h: float) -> bool:
        # check four corners + center
        points = [
            (x, y), (x + w, y), (x, y + h), (x + w, y + h),
            (x + w / 2, y + h / 2)
        ]
        for px, py in points:
            tx = int(px // self.tile_size)
            ty = int(py // self.tile_size)
            if tx < 0 or ty < 0 or tx >= self.w or ty >= self.h:
                return True
            if self.map[ty][tx] == "1":
                return True
        return False

    def get_tile(self, tx: int, ty: int) -> str:
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.map[ty][tx]
        return "1"

    def interact(self, px: float, py: float) -> Optional[str]:
        tx = int((px + 5) // self.tile_size)
        ty = int((py + 7) // self.tile_size)
        key = (tx, ty)
        if key in self.notes:
            text = self.notes.pop(key)
            return text
        tile = self.get_tile(tx, ty)
        if tile == "4":  # console
            self.generators_fixed += 1
            if self.generators_fixed >= 2:
                self.exit_open = True
            return "GENERATOR NODE STABILIZED. Power routed to surface lock."
        return None

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float, view_w: int, view_h: int):
        start_tx = max(0, int(cam_x // self.tile_size) - 1)
        end_tx = min(self.w, int((cam_x + view_w) // self.tile_size) + 2)
        start_ty = max(0, int(cam_y // self.tile_size) - 1)
        end_ty = min(self.h, int((cam_y + view_h) // self.tile_size) + 2)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                t = self.map[ty][tx]
                sx = int(tx * self.tile_size - cam_x)
                sy = int(ty * self.tile_size - cam_y)
                if t == "1":
                    surface.blit(self.tiles["wall"], (sx, sy))
                elif t == "0":
                    surface.blit(self.tiles["floor"], (sx, sy))
                elif t == "4":
                    surface.blit(self.tiles["floor"], (sx, sy))
                    surface.blit(self.tiles["console"], (sx, sy))
                else:
                    surface.blit(self.tiles["floor"], (sx, sy))

                # notes still present
                if (tx, ty) in self.notes:
                    surface.blit(self.tiles["note"], (sx, sy))

        # blood
        for bx, by in self.blood_trails:
            sx = int(bx * self.tile_size - cam_x)
            sy = int(by * self.tile_size - cam_y)
            surface.blit(self.tiles["blood"], (sx, sy))
