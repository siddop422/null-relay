import pygame
import math
import random
from player import Player
from entity import HorrorEntity
from world import World
from ui import UI
from assets import (
    NATIVE_W, NATIVE_H, SCALE, PAL,
    generate_flashlight_mask, generate_vignette,
    make_beep, make_noise
)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.screen = pygame.display.set_mode((NATIVE_W * SCALE, NATIVE_H * SCALE))
        pygame.display.set_caption("Null Relay")
        self.clock = pygame.time.Clock()
        self.native = pygame.Surface((NATIVE_W, NATIVE_H))
        self.running = True
        self.dt = 0.0

        self.world = World()
        self.player = Player(48, 48)
        self.entity = HorrorEntity(280, 140)
        self.entity.set_patrol([(200, 80), (300, 100), (250, 160), (180, 120)])
        self.ui = UI(NATIVE_W, NATIVE_H)

        self.light_mask = generate_flashlight_mask(72)
        self.vignette = generate_vignette(NATIVE_W, NATIVE_H)
        self.dark_overlay = pygame.Surface((NATIVE_W, NATIVE_H), pygame.SRCALPHA)
        self.dark_overlay.fill((0, 0, 0, 210))

        self.sfx_beep = make_beep(880, 60, 0.2)
        self.sfx_noise = make_noise(180, 0.15)
        self.sfx_hit = make_noise(90, 0.35)

        self.cam_x = 0.0
        self.cam_y = 0.0
        self.shake = 0.0
        self.heartbeat_timer = 0.0
        self.noise_level = 0.0
        self.time_alive = 0.0
        self.ending_timer = 0.0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.ui.ending:
                        self.running = False
                    else:
                        self.ui.pause = not self.ui.pause
                if event.key == pygame.K_TAB:
                    self.ui.journal_open = not self.ui.journal_open
                if event.key == pygame.K_f:
                    self.player.toggle_light()
                    self.sfx_beep.play()
                if event.key in (pygame.K_e, pygame.K_SPACE) and self.player.interact_cooldown <= 0:
                    msg = self.world.interact(self.player.x, self.player.y)
                    if msg:
                        self.ui.show_message(msg)
                        self.player.notes_read.append(msg)
                        self.player.interact_cooldown = 0.6
                        self.sfx_beep.play()
                        if "surface lock" in msg.lower() and self.world.exit_open:
                            self.ui.ending = "escape"
                            self.ending_timer = 5.0

        if not self.ui.pause and not self.ui.journal_open and not self.ui.ending:
            self.player.update(self.dt, keys, self.world)

            # noise from sprinting
            if self.player.state == "run":
                self.noise_level = min(1.0, self.noise_level + 2.5 * self.dt)
            else:
                self.noise_level = max(0.0, self.noise_level - 1.8 * self.dt)

    def update(self):
        if self.ui.ending:
            self.ending_timer -= self.dt
            if self.ending_timer <= 0:
                self.running = False
            return

        if self.ui.pause or self.ui.journal_open:
            return

        self.time_alive += self.dt
        self.entity.update(self.dt, self.player, self.world, self.noise_level)

        # camera follow
        self.cam_x = self.player.x - NATIVE_W // 2 + self.player.w // 2
        self.cam_y = self.player.y - NATIVE_H // 2 + self.player.h // 2
        self.cam_x = max(0, min(self.cam_x, self.world.w * 16 - NATIVE_W))
        self.cam_y = max(0, min(self.cam_y, self.world.h * 16 - NATIVE_H))

        # tension effects
        if self.player.sanity < 40:
            self.shake = (40 - self.player.sanity) * 0.08
            self.heartbeat_timer += self.dt
            if self.heartbeat_timer > 0.7:
                self.heartbeat_timer = 0
                self.sfx_noise.play()
        else:
            self.shake *= 0.9

        if self.player.sanity <= 0:
            self.ui.ending = "trapped"
            self.ending_timer = 4.0
            self.sfx_hit.play()

        # truth ending – reach far right containment area with high awareness of lore
        if self.player.x > 520 and len(self.player.notes_read) >= 3:
            self.ui.ending = "truth"
            self.ending_timer = 5.0

        self.ui.update(self.dt)

    def draw(self):
        self.native.fill(PAL["black"])

        # world
        self.world.draw(self.native, self.cam_x, self.cam_y, NATIVE_W, NATIVE_H)

        # entity (only if somewhat near)
        ex = self.entity.x - self.cam_x
        ey = self.entity.y - self.cam_y
        if -40 < ex < NATIVE_W + 40 and -40 < ey < NATIVE_H + 40:
            self.entity.draw(self.native, self.cam_x, self.cam_y)

        # player
        self.player.draw(self.native, self.cam_x, self.cam_y)

        # darkness + flashlight
        self.native.blit(self.dark_overlay, (0, 0))
        if self.player.light_on and self.player.battery > 0:
            lx = int(self.player.x - self.cam_x + self.player.w // 2 - self.light_mask.get_width() // 2)
            ly = int(self.player.y - self.cam_y + self.player.h // 2 - self.light_mask.get_height() // 2)
            # slight facing bias
            lx += self.player.facing * 8
            self.native.blit(self.light_mask, (lx, ly), special_flags=pygame.BLEND_RGBA_ADD)

        # vignette + sanity pulse
        self.native.blit(self.vignette, (0, 0))
        if self.player.sanity < 50:
            pulse = abs(math.sin(self.time_alive * 3)) * (50 - self.player.sanity) * 1.5
            pulse_surf = pygame.Surface((NATIVE_W, NATIVE_H), pygame.SRCALPHA)
            pulse_surf.fill((80, 0, 20, int(min(90, pulse))))
            self.native.blit(pulse_surf, (0, 0))

        # HUD
        self.ui.draw_hud(self.native, self.player)
        if self.ui.journal_open:
            self.ui.draw_journal(self.native, self.player.notes_read)
        if self.ui.ending:
            self.ui.draw_ending(self.native, self.ui.ending)

        # scale nearest-neighbor (crisp pixels)
        scaled = pygame.transform.scale(self.native, (NATIVE_W * SCALE, NATIVE_H * SCALE))
        # screen shake
        ox = oy = 0
        if self.shake > 0.5:
            ox = random.randint(-int(self.shake), int(self.shake))
            oy = random.randint(-int(self.shake), int(self.shake))
        self.screen.fill(PAL["black"])
        self.screen.blit(scaled, (ox, oy))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0
            self.handle_input()
            self.update()
            self.draw()
        pygame.quit()
