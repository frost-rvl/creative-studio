import pygame
import random
import math
import asyncio
import base64
import io
from js import window, console

pygame.init()

# ---- CONSTANTS ----
WIDTH, HEIGHT = 900, 720
SIDEBAR_W = 240
CANVAS_W = WIDTH - SIDEBAR_W

# ---- COLORS ----
BG_DARK = (16, 17, 23)
BG_PANEL = (24, 26, 34)
BG_PANEL_LIGHT = (32, 35, 46)
TEXT_MUTED = (150, 152, 165)
TEXT_BRIGHT = (235, 235, 240)
BORDER = (50, 53, 66)

PALETTES = [
    {"name": "Coucher de soleil", "colors": [(255, 220, 120), (255, 150, 90), (200, 90, 70)]},
    {"name": "Aurore", "colors": [(120, 200, 255), (170, 130, 255), (255, 130, 190)]},
    {"name": "Forêt", "colors": [(120, 255, 180), (80, 180, 120), (220, 255, 150)]},
]

# ---- HELPERS ----
def lerp(a, b, t):
    return a + (b - a) * t

# ---- BUTTON ----
class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.hover = False

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface):
        color = BG_PANEL_LIGHT if not self.hover else (45, 48, 62)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BORDER, self.rect, 1, border_radius=10)
        font = pygame.font.SysFont("Arial", 16, bold=True)
        text = font.render(self.label, True, TEXT_BRIGHT)
        surface.blit(text, (
            self.rect.centerx - text.get_width() // 2,
            self.rect.centery - text.get_height() // 2
        ))

# ---- GRAIN ----
class Grain:
    def __init__(self, palette):
        self.color = random.choice(palette)
        self.size = random.choice([2, 2, 3])
        self.top_y = random.uniform(80 + 20, 350 - 40)
        hw = self._top_half_width(self.top_y) - 5
        self.start_x = random.uniform(-hw, hw)
        self.fall_x = random.triangular(-165 * 0.75, 165 * 0.75, 0)
        self.state = "waiting"
        self.fall_y = self.top_y
        self.fall_speed = 0
        self.rest_y = 605

    def _top_half_width(self, y):
        t = (y - 80) / (350 - 80)
        t = max(0, min(1, t))
        return lerp(150, 8, t)

    def neck_x(self):
        return self.fall_x * 0.05

    def draw_waiting(self, surface, cx):
        pygame.draw.circle(surface, self.color, (int(cx + self.start_x), int(self.top_y)), self.size)

    def draw_falling(self, surface, cx):
        if self.state == "falling_top":
            t = (self.fall_y - self.top_y) / max(1, 350 - self.top_y)
            x = lerp(self.start_x, self.neck_x(), min(1, max(0, t)))
        else:
            t = (self.fall_y - 350) / max(1, 605 - 350)
            x = lerp(self.neck_x(), self.fall_x, min(1, max(0, t)))
        pygame.draw.circle(surface, self.color, (int(cx + x), int(self.fall_y)), self.size)

    def draw_landed(self, surface, cx):
        pygame.draw.circle(surface, self.color, (int(cx + self.fall_x), int(self.rest_y)), self.size)

# ---- HOURGLASS ----
class Hourglass:
    def __init__(self, duration, grain_count, palette):
        self.duration = duration
        self.grain_count = grain_count
        self.palette = palette
        self.grains = [Grain(palette) for _ in range(grain_count)]
        self.start_time = 0
        self.paused = False
        self.pause_start = 0
        self.total_pause = 0
        self.active_falls = []
        self.next_to_drop = 0
        self.pile_res = 3
        self.pile_cols = int((165 * 2) / self.pile_res) + 1
        self.pile_heights = [0 for _ in range(self.pile_cols)]
        self.running = False

    def start(self):
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.running = True

    def reset(self):
        self.grains = [Grain(self.palette) for _ in range(self.grain_count)]
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.paused = False
        self.pause_start = 0
        self.total_pause = 0
        self.active_falls = []
        self.next_to_drop = 0
        self.pile_heights = [0 for _ in range(self.pile_cols)]
        self.running = True

    def toggle_pause(self):
        if self.paused:
            self.total_pause += pygame.time.get_ticks() / 1000.0 - self.pause_start
            self.paused = False
        else:
            self.pause_start = pygame.time.get_ticks() / 1000.0
            self.paused = True

    def elapsed_time(self):
        if self.paused:
            return self.pause_start - self.start_time - self.total_pause
        return pygame.time.get_ticks() / 1000.0 - self.start_time - self.total_pause

    def remaining_time(self):
        return max(0, int(math.ceil(self.duration - self.elapsed_time())))

    def progress(self):
        return min(1, max(0, self.elapsed_time() / self.duration))

    def column_index(self, x):
        idx = int((x + 165) / self.pile_res)
        return max(0, min(self.pile_cols - 1, idx))

    def pile_height_at(self, x):
        return self.pile_heights[self.column_index(x)]

    def deposit(self, x, size):
        idx = self.column_index(x)
        self.pile_heights[idx] += size * 2
        for offset in range(1, 8):
            val = max(0, size * 2 - offset * 0.6)
            if idx - offset >= 0:
                self.pile_heights[idx - offset] += val * 0.25
            if idx + offset < self.pile_cols:
                self.pile_heights[idx + offset] += val * 0.25

    def landed_count(self):
        return sum(1 for g in self.grains if g.state == "landed")

    def update(self, dt):
        if self.paused or not self.running:
            return
        target = int(self.progress() * self.grain_count)
        current = self.landed_count() + len(self.active_falls)
        to_spawn = min(max(0, target - current), 8)
        for _ in range(to_spawn):
            if self.next_to_drop < self.grain_count:
                g = self.grains[self.next_to_drop]
                g.state = "falling_top"
                g.fall_y = g.top_y
                g.fall_speed = 40
                self.active_falls.append(g)
                self.next_to_drop += 1
        still_falling = []
        for g in self.active_falls:
            g.fall_speed += 1800 * dt
            g.fall_y += g.fall_speed * dt
            if g.state == "falling_top" and g.fall_y >= 350:
                g.state = "falling_bottom"
            if g.state == "falling_bottom":
                pile_top = 605 - self.pile_height_at(g.fall_x)
                if g.fall_y >= pile_top:
                    g.rest_y = pile_top
                    g.state = "landed"
                    self.deposit(g.fall_x, g.size)
                    continue
            still_falling.append(g)
        self.active_falls = still_falling

    def add_grains(self, n):
        for _ in range(n):
            self.grains.append(Grain(self.palette))
        self.grain_count = len(self.grains)

    def remove_grains(self, n):
        if self.grain_count > n + 20:
            self.grains = self.grains[:-n]
            self.grain_count = len(self.grains)
            self.next_to_drop = min(self.next_to_drop, self.grain_count)

    def recolor(self):
        for g in self.grains:
            g.color = random.choice(self.palette)

    def draw(self, surface, cx):
        progress = self.progress()

        def shift(p):
            return (p[0] + cx, p[1])

        glass_points = [shift(p) for p in [
            (-150, 50), (150, 50), (20, 350),
            (180, 605 + 15), (-180, 605 + 15), (-20, 350)
        ]]
        pygame.draw.polygon(surface, (60, 63, 78), glass_points)
        pygame.draw.polygon(surface, (210, 212, 225), glass_points, 3)

        for g in self.grains:
            if g.state == "waiting":
                g.draw_waiting(surface, cx)
        for g in self.active_falls:
            g.draw_falling(surface, cx)
        for g in self.grains:
            if g.state == "landed":
                g.draw_landed(surface, cx)

        # Ring
        ring_center = (cx, 56)
        pygame.draw.circle(surface, BG_PANEL_LIGHT, ring_center, 26)
        pygame.draw.circle(surface, BORDER, ring_center, 26, 3)
        font_small = pygame.font.SysFont("Arial", 13)
        pct = font_small.render(f"{int(progress * 100)}%", True, TEXT_BRIGHT)
        surface.blit(pct, (ring_center[0] - pct.get_width() // 2, ring_center[1] - pct.get_height() // 2))

        # Timer text
        font_bold = pygame.font.SysFont("Arial", 16, bold=True)
        label = "En pause" if self.paused else f"{self.remaining_time()} secondes restantes"
        timer = font_bold.render(label, True, TEXT_BRIGHT)
        surface.blit(timer, (cx - timer.get_width() // 2, 90))

        if self.remaining_time() == 0 and not self.active_falls:
            done = pygame.font.SysFont("Arial", 40, bold=True).render("Terminé", True, (255, 140, 140))
            surface.blit(done, (cx - done.get_width() // 2, 700 - 70))

# ---- APP ----
class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 13)

        self.duration = 60
        self.grain_count = 300
        self.palette_index = 0
        self.palette = PALETTES[self.palette_index]["colors"]

        self.hourglass = Hourglass(self.duration, self.grain_count, self.palette)
        self.hourglass.start()

        self.pause_btn = Button((20, 100, SIDEBAR_W - 40, 44), "Pause")
        self.reset_btn = Button((20, 152, SIDEBAR_W - 40, 44), "Réinitialiser")
        self.more_btn = Button((20, 204, 84, 40), "+ Grains")
        self.less_btn = Button((116, 204, 84, 40), "- Grains")
        self.palette_btn = Button((20, 304, SIDEBAR_W - 40, 44), "Changer palette")

    def capture_art(self):
        """Capture the hourglass shape and grains on the UI background."""
        canvas_surf = pygame.Surface((CANVAS_W, HEIGHT))
        canvas_surf.fill(BG_DARK)
        cx = CANVAS_W // 2

        # Draw the glass (same as Hourglass.draw)
        def shift(p):
            return (p[0] + cx, p[1])

        glass_points = [shift(p) for p in [
            (-150, 50), (150, 50), (20, 350),
            (180, 605 + 15), (-180, 605 + 15), (-20, 350)
        ]]
        pygame.draw.polygon(canvas_surf, (60, 63, 78), glass_points)
        pygame.draw.polygon(canvas_surf, (210, 212, 225), glass_points, 3)

        # Draw the grains
        for g in self.hourglass.grains:
            if g.state == "waiting":
                g.draw_waiting(canvas_surf, cx)
            elif g.state == "landed":
                g.draw_landed(canvas_surf, cx)
        for g in self.hourglass.active_falls:
            g.draw_falling(canvas_surf, cx)

        buf = io.BytesIO()
        pygame.image.save(canvas_surf, buf, "png")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        return b64

    async def run(self):
        running = True
        last_t = pygame.time.get_ticks() / 1000.0
        while running:
            now = pygame.time.get_ticks() / 1000.0
            dt = min(now - last_t, 0.05)
            last_t = now
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.hourglass.toggle_pause()
                    elif event.key == pygame.K_r:
                        self.hourglass.reset()
                    elif event.key == pygame.K_c:
                        self.palette_index = (self.palette_index + 1) % len(PALETTES)
                        self.palette = PALETTES[self.palette_index]["colors"]
                        self.hourglass.palette = self.palette
                        self.hourglass.recolor()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.pause_btn.contains(mouse_pos):
                        self.hourglass.toggle_pause()
                    elif self.reset_btn.contains(mouse_pos):
                        self.hourglass.reset()
                    elif self.more_btn.contains(mouse_pos):
                        self.hourglass.add_grains(50)
                    elif self.less_btn.contains(mouse_pos):
                        self.hourglass.remove_grains(50)
                    elif self.palette_btn.contains(mouse_pos):
                        self.palette_index = (self.palette_index + 1) % len(PALETTES)
                        self.palette = PALETTES[self.palette_index]["colors"]
                        self.hourglass.palette = self.palette
                        self.hourglass.recolor()

            self.hourglass.update(dt)

            self.screen.fill(BG_DARK)

            canvas_rect = pygame.Rect(SIDEBAR_W, 0, CANVAS_W, HEIGHT)
            canvas = self.screen.subsurface(canvas_rect)
            canvas.fill(BG_DARK)
            self.hourglass.draw(canvas, CANVAS_W // 2)

            pygame.draw.rect(self.screen, BG_PANEL, (0, 0, SIDEBAR_W, HEIGHT))
            pygame.draw.line(self.screen, BORDER, (SIDEBAR_W, 0), (SIDEBAR_W, HEIGHT))

            title = self.font_title.render("Sablier", True, TEXT_BRIGHT)
            self.screen.blit(title, (20, 20))
            sub = self.font_small.render("Art génératif interactif", True, TEXT_MUTED)
            self.screen.blit(sub, (20, 52))

            self.pause_btn.label = "Reprendre" if self.hourglass.paused else "Pause"
            for btn in (self.pause_btn, self.reset_btn, self.more_btn, self.less_btn, self.palette_btn):
                btn.hover = btn.contains(mouse_pos)
                btn.draw(self.screen)

            grain_text = self.font_small.render(f"{self.hourglass.grain_count} grains", True, TEXT_MUTED)
            self.screen.blit(grain_text, (20, 260))
            fallen = self.font_small.render(f"{self.hourglass.landed_count()} grains tombés", True, TEXT_MUTED)
            self.screen.blit(fallen, (20, 280))

            pal_title = pygame.font.SysFont("Arial", 16, bold=True).render("Palette actuelle", True, TEXT_BRIGHT)
            self.screen.blit(pal_title, (20, 365))
            pal_name = self.font_small.render(PALETTES[self.palette_index]["name"], True, TEXT_MUTED)
            self.screen.blit(pal_name, (20, 390))
            for i, col in enumerate(PALETTES[self.palette_index]["colors"]):
                pygame.draw.circle(self.screen, col, (25 + i * 45, 430), 16)
                pygame.draw.circle(self.screen, TEXT_BRIGHT, (25 + i * 45, 430), 16, 1)
            hint = self.font_small.render("Bouton ou C pour changer", True, TEXT_MUTED)
            self.screen.blit(hint, (20, 465))

            controls = ["Espace : pause / reprise", "R : réinitialiser", "C : changer palette", "Échap : quitter"]
            y = HEIGHT - 110
            for line in controls:
                surf = self.font_small.render(line, True, TEXT_MUTED)
                self.screen.blit(surf, (20, y))
                y += 22

            pygame.display.flip()
            self.clock.tick(60)
            await asyncio.sleep(0)

        pygame.quit()

# ---- JS EXPOSURE ----
app_instance = None

def js_capture_art():
    if app_instance is None:
        return ""
    return app_instance.capture_art()

window.captureArt = js_capture_art

# ---- RUN ----
if __name__ == "__main__":
    app = App()
    app_instance = app
    asyncio.run(app.run())