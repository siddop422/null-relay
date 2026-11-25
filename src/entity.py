import pygame
import math
import random
from typing import Tuple, List
from assets import generate_entity_frames, PAL

class HorrorEntity:
    """Primary stalker – state machine AI."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.w = 16
        self.h = 24
        self.speed = 38.0
        self.chase_speed = 78.0
        self.state = "patrol"          # patrol, investigate, stalk, chase, search, cooldown
        self.frames = generate_entity_frames()
        self.anim_timer = 0.0
        self.anim_idx = 0
        self.target_x = x
        self.target_y = y
        self.awareness = 0.0          # 0–100
        self.cooldown = 0.0
        self.patrol_points: List[Tuple[float, float]] = []
        self.patrol_idx = 0
        self.last_seen_x = 0.0
        self.last_seen_y = 0.0
        self.attack_timer = 0.0

    def set_patrol(self, points: List[Tuple[float, float]]):
        self.patrol_points = points
        if points:
            self.target_x, self.target_y = points[0]

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def can_see(self, px: float, py: float, light_on: bool, world) -> bool:
        # simple line-of-sight + light bonus
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)
        if dist > 140:
            return False
        # rough occlusion check (sample a few points)
        steps = max(3, int(dist / 12))
        for i in range(1, steps):
            t = i / steps
            tx = self.x + dx * t
            ty = self.y + dy * t
            if world.collides(tx, ty, 4, 4):
                return False
        # flashlight makes player more visible
        visibility = 1.0
        if light_on:
            visibility = 1.6
        return dist < 90 * visibility

    def update(self, dt: float, player, world, noise_level: float):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.attack_timer = max(0.0, self.attack_timer - dt)

        px, py = player.x + player.w / 2, player.y + player.h / 2
        dx = px - (self.x + self.w / 2)
        dy = py - (self.y + self.h / 2)
        dist = math.hypot(dx, dy)

        sees = self.can_see(px, py, player.light_on, world)
        hears = noise_level > 0.4 and dist < 110

        # State machine
        if self.state == "cooldown":
            if self.cooldown <= 0:
                self.state = "patrol"
            return

        if sees or hears:
            self.awareness = min(100, self.awareness + 55 * dt)
            self.last_seen_x = px
            self.last_seen_y = py
            if self.awareness > 70 or dist < 45:
                self.state = "chase"
            else:
                self.state = "stalk"
        else:
            self.awareness = max(0, self.awareness - 12 * dt)
            if self.state in ("chase", "stalk") and self.awareness < 15:
                self.state = "search"
                self.target_x = self.last_seen_x
                self.target_y = self.last_seen_y

        # Movement
        speed = self.speed
        if self.state == "chase":
            speed = self.chase_speed
            self.target_x = px
            self.target_y = py
        elif self.state == "stalk":
            # keep distance, circle
            angle = math.atan2(dy, dx) + 0.4
            self.target_x = px - math.cos(angle) * 55
            self.target_y = py - math.sin(angle) * 55
        elif self.state == "search":
            if abs(self.x - self.target_x) < 8 and abs(self.y - self.target_y) < 8:
                self.state = "patrol"
        elif self.state == "patrol":
            if self.patrol_points:
                tx, ty = self.patrol_points[self.patrol_idx]
                if abs(self.x - tx) < 10 and abs(self.y - ty) < 10:
                    self.patrol_idx = (self.patrol_idx + 1) % len(self.patrol_points)
                self.target_x, self.target_y = self.patrol_points[self.patrol_idx]

        # Move toward target
        tdx = self.target_x - self.x
        tdy = self.target_y - self.y
        tdist = math.hypot(tdx, tdy)
        if tdist > 2:
            tdx /= tdist
            tdy /= tdist
            nx = self.x + tdx * speed * dt
            ny = self.y + tdy * speed * dt
            if not world.collides(nx, self.y, self.w, self.h):
                self.x = nx
            if not world.collides(self.x, ny, self.w, self.h):
                self.y = ny

        # Attack
        if dist < 22 and self.state == "chase" and self.attack_timer <= 0:
            player.sanity = max(0, player.sanity - 28)
            player.stamina = max(0, player.stamina - 20)
            self.attack_timer = 1.4
            self.state = "cooldown"
            self.cooldown = 2.8

        # Animation
        self.anim_timer += dt
        if self.anim_timer > 0.1:
            self.anim_timer = 0
            self.anim_idx = (self.anim_idx + 1) % 6

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        key = "chase" if self.state == "chase" else "patrol" if self.state == "patrol" else "idle"
        if self.state == "cooldown":
            key = "glitch"
        frame_list = self.frames.get(key, self.frames["idle"])
        frame = frame_list[self.anim_idx % len(frame_list)]
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        surface.blit(frame, (sx - 2, sy - 4))
