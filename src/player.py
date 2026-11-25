import pygame
import math
from typing import Tuple, List, Dict, Optional
from assets import PAL, generate_player_frames

class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.w = 10
        self.h = 14
        self.speed = 55.0
        self.sprint_mult = 1.7
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.stamina_drain = 28.0
        self.stamina_regen = 18.0
        self.battery = 100.0
        self.max_battery = 100.0
        self.light_on = True
        self.light_drain = 4.5          # per second when on
        self.sanity = 100.0
        self.max_sanity = 100.0
        self.facing = 1                 # 1 right, -1 left
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.frames = generate_player_frames()
        self.anim_timer = 0.0
        self.anim_idx = 0
        self.state = "idle"
        self.inventory: List[str] = []
        self.notes_read: List[str] = []
        self.hiding = False
        self.interact_cooldown = 0.0

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, world):
        self.interact_cooldown = max(0.0, self.interact_cooldown - dt)

        # Movement
        dx = dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
            self.facing = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
            self.facing = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        sprinting = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.stamina > 5
        speed = self.speed * (self.sprint_mult if sprinting else 1.0)

        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self.vel_x = dx * speed
            self.vel_y = dy * speed
            self.state = "run" if sprinting else "walk"
            if sprinting:
                self.stamina = max(0, self.stamina - self.stamina_drain * dt)
            else:
                self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen * 0.4 * dt)
        else:
            self.vel_x = self.vel_y = 0
            self.state = "idle"
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen * dt)

        # Collision with world
        new_x = self.x + self.vel_x * dt
        new_y = self.y + self.vel_y * dt
        if not world.collides(new_x, self.y, self.w, self.h):
            self.x = new_x
        if not world.collides(self.x, new_y, self.w, self.h):
            self.y = new_y

        # Light
        if self.light_on and self.battery > 0:
            self.battery = max(0, self.battery - self.light_drain * dt)
            if self.battery <= 0:
                self.light_on = False
        elif not self.light_on:
            # slight regen when off (emergency cells)
            self.battery = min(self.max_battery, self.battery + 1.2 * dt)

        # Sanity – dark + entity proximity hurts it
        if not self.light_on or self.battery < 15:
            self.sanity = max(0, self.sanity - 6.0 * dt)
        else:
            self.sanity = min(self.max_sanity, self.sanity + 3.5 * dt)

        # Animation
        self.anim_timer += dt
        if self.anim_timer > 0.12:
            self.anim_timer = 0
            self.anim_idx = (self.anim_idx + 1) % 4

    def toggle_light(self):
        if self.battery > 2:
            self.light_on = not self.light_on

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        frame_list = self.frames.get(self.state, self.frames["idle"])
        frame = frame_list[self.anim_idx % len(frame_list)]
        if self.facing < 0:
            frame = pygame.transform.flip(frame, True, False)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        surface.blit(frame, (sx - 1, sy - 2))
