import pygame
from assets import PAL

class UI:
    def __init__(self, native_w: int, native_h: int):
        self.w = native_w
        self.h = native_h
        self.font = pygame.font.SysFont("courier", 8)
        self.big_font = pygame.font.SysFont("courier", 12)
        self.message = ""
        self.message_timer = 0.0
        self.journal_open = False
        self.pause = False
        self.ending = None  # "escape", "truth", "trapped"

    def show_message(self, text: str, duration: float = 4.0):
        self.message = text
        self.message_timer = duration

    def update(self, dt: float):
        if self.message_timer > 0:
            self.message_timer -= dt

    def draw_hud(self, surface: pygame.Surface, player):
        # stamina bar
        pygame.draw.rect(surface, PAL["dark"], (6, 6, 50, 5))
        sw = int(48 * (player.stamina / player.max_stamina))
        pygame.draw.rect(surface, PAL["green"], (7, 7, sw, 3))

        # battery
        pygame.draw.rect(surface, PAL["dark"], (6, 13, 50, 5))
        bw = int(48 * (player.battery / player.max_battery))
        col = PAL["cyan"] if player.light_on else PAL["mid"]
        pygame.draw.rect(surface, col, (7, 14, bw, 3))

        # sanity
        pygame.draw.rect(surface, PAL["dark"], (6, 20, 50, 5))
        sanw = int(48 * (player.sanity / player.max_sanity))
        scol = PAL["purple"] if player.sanity > 40 else PAL["blood"]
        pygame.draw.rect(surface, scol, (7, 21, sanw, 3))

        if self.message_timer > 0:
            # word wrap simple
            words = self.message.split()
            lines = []
            cur = ""
            for w in words:
                if len(cur) + len(w) < 38:
                    cur += w + " "
                else:
                    lines.append(cur)
                    cur = w + " "
            if cur:
                lines.append(cur)
            y = self.h - 12 - len(lines) * 9
            for line in lines:
                txt = self.font.render(line.strip(), True, PAL["white"])
                surface.blit(txt, (8, y))
                y += 9

    def draw_journal(self, surface: pygame.Surface, notes: list):
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        title = self.big_font.render("FIELD JOURNAL", True, PAL["cyan"])
        surface.blit(title, (20, 12))
        y = 30
        for n in notes[-6:]:
            for i in range(0, len(n), 42):
                line = n[i:i+42]
                txt = self.font.render(line, True, PAL["white"])
                surface.blit(txt, (18, y))
                y += 9
            y += 4
        hint = self.font.render("[TAB] close", True, PAL["light"])
        surface.blit(hint, (20, self.h - 14))

    def draw_ending(self, surface: pygame.Surface, ending: str):
        surface.fill(PAL["black"])
        if ending == "escape":
            lines = ["You restored surface power.", "The lock cycles open.", "You climb into the cold night air.", "Behind you the station goes silent.", "ENDING: ESCAPE"]
        elif ending == "truth":
            lines = ["You reach the core.", "The signal is not a message.", "It is a mouth.", "You understand why the crew never left.", "ENDING: TRUTH"]
        else:
            lines = ["The light dies.", "Something finds you in the dark.", "Your last thought is static.", "ENDING: TRAPPED"]
        y = 50
        for line in lines:
            txt = self.big_font.render(line, True, PAL["white"])
            surface.blit(txt, (self.w // 2 - txt.get_width() // 2, y))
            y += 16
