import pygame
import random
import math
import time

pygame.init()

WIDTH, HEIGHT = 900, 720
SIDEBAR_W = 240
CANVAS_W = WIDTH - SIDEBAR_W

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sablier Génératif")
clock = pygame.time.Clock()

FONT_TITLE = pygame.font.SysFont("Arial", 26, bold=True)
FONT_LABEL = pygame.font.SysFont("Arial", 16)
FONT_LABEL_BOLD = pygame.font.SysFont("Arial", 16, bold=True)
FONT_SMALL = pygame.font.SysFont("Arial", 13)
FONT_BIG = pygame.font.SysFont("Arial", 22, bold=True)
FONT_HUGE = pygame.font.SysFont("Arial", 40, bold=True)

PALETTES = [
    {"name": "Coucher de soleil", "colors": [(255, 220, 120), (255, 150, 90), (200, 90, 70)]},
    {"name": "Aurore", "colors": [(120, 200, 255), (170, 130, 255), (255, 130, 190)]},
    {"name": "Forêt", "colors": [(120, 255, 180), (80, 180, 120), (220, 255, 150)]},
]

BG_DARK = (16, 17, 23)
BG_PANEL = (24, 26, 34)
BG_PANEL_LIGHT = (32, 35, 46)
TEXT_MUTED = (150, 152, 165)
TEXT_BRIGHT = (235, 235, 240)
BORDER = (50, 53, 66)


def lerp(a, b, t):
    return a + (b - a) * t


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

        text = FONT_LABEL_BOLD.render(self.label, True, TEXT_BRIGHT)
        surface.blit(text, (
            self.rect.centerx - text.get_width() // 2,
            self.rect.centery - text.get_height() // 2
        ))


def ask_number(title, subtitle, default_value, min_val=1, max_val=100000):
    text = ""
    button = Button((WIDTH // 2 - 90, 440, 180, 46), "Valider")

    while True:
        mouse_pos = pygame.mouse.get_pos()
        button.hover = button.contains(mouse_pos)

        screen.fill(BG_DARK)

        title_surf = FONT_BIG.render(title, True, TEXT_BRIGHT)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 150))

        subtitle_surf = FONT_LABEL.render(subtitle, True, TEXT_MUTED)
        screen.blit(subtitle_surf, (WIDTH // 2 - subtitle_surf.get_width() // 2, 210))

        box = pygame.Rect(WIDTH // 2 - 140, 290, 280, 56)
        pygame.draw.rect(screen, BG_PANEL_LIGHT, box, border_radius=12)
        pygame.draw.rect(screen, BORDER, box, 2, border_radius=12)

        display_text = text if text else str(default_value)
        color = TEXT_BRIGHT if text else TEXT_MUTED
        value_surf = FONT_BIG.render(display_text, True, color)

        screen.blit(value_surf, (
            box.centerx - value_surf.get_width() // 2,
            box.centery - value_surf.get_height() // 2
        ))

        hint = FONT_SMALL.render(
            "Entrée pour valider ou cliquez sur le bouton",
            True,
            TEXT_MUTED
        )
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 380))

        button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if text.isdigit() and min_val <= int(text) <= max_val:
                        return int(text)
                    return default_value

                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]

                elif event.unicode.isdigit() and len(text) < 6:
                    text += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button.contains(mouse_pos):
                    if text.isdigit() and min_val <= int(text) <= max_val:
                        return int(text)
                    return default_value

        pygame.display.flip()
        clock.tick(60)


duration = ask_number("Durée du sablier", "En secondes", 60, 5, 36000)
grain_count = ask_number("Nombre de grains de sable", "Effet plus réaliste", 300, 20, 4000)


class AppState:
    def __init__(self):
        self.palette_index = 0

    def palette(self):
        return PALETTES[self.palette_index]["colors"]


state = AppState()


def random_palette_color():
    return random.choice(state.palette())


NECK_Y = 350
TOP_Y = 80
BOTTOM_FLOOR_Y = 605

HALF_TOP = 150
HALF_NECK = 8
HALF_BOTTOM = 165


def top_chamber_half_width(y):
    t = (y - TOP_Y) / (NECK_Y - TOP_Y)
    t = max(0, min(1, t))
    return lerp(HALF_TOP, HALF_NECK, t)


class Grain:
    def __init__(self):
        self.color = random_palette_color()
        self.size = random.choice([2, 2, 3])
        self.top_y = random.uniform(TOP_Y + 20, NECK_Y - 40)

        hw = top_chamber_half_width(self.top_y) - 5
        self.start_x = random.uniform(-hw, hw)

        self.fall_x = random.triangular(
            -HALF_BOTTOM * 0.75,
            HALF_BOTTOM * 0.75,
            0
        )

        self.state = "waiting"
        self.fall_y = self.top_y
        self.fall_speed = 0
        self.rest_y = BOTTOM_FLOOR_Y

    def neck_x(self):
        return self.fall_x * 0.05

    def draw_waiting(self, surface, cx):
        pygame.draw.circle(surface, self.color, (int(cx + self.start_x), int(self.top_y)), self.size)

    def draw_falling(self, surface, cx):
        if self.state == "falling_top":
            t = (self.fall_y - self.top_y) / max(1, NECK_Y - self.top_y)
            x = lerp(self.start_x, self.neck_x(), min(1, max(0, t)))
        else:
            t = (self.fall_y - NECK_Y) / max(1, BOTTOM_FLOOR_Y - NECK_Y)
            x = lerp(self.neck_x(), self.fall_x, min(1, max(0, t)))

        pygame.draw.circle(surface, self.color, (int(cx + x), int(self.fall_y)), self.size)

    def draw_landed(self, surface, cx):
        pygame.draw.circle(surface, self.color, (int(cx + self.fall_x), int(self.rest_y)), self.size)


class Hourglass:
    def __init__(self, duration, grain_count):
        self.duration = duration
        self.grain_count = grain_count
        self.grains = [Grain() for _ in range(grain_count)]

        self.start_time = time.time()
        self.paused = False
        self.pause_start = 0
        self.total_pause = 0

        self.active_falls = []
        self.next_to_drop = 0

        self.pile_res = 3
        self.pile_cols = int((HALF_BOTTOM * 2) / self.pile_res) + 1
        self.pile_heights = [0 for _ in range(self.pile_cols)]

    def reset(self):
        self.grains = [Grain() for _ in range(self.grain_count)]
        self.start_time = time.time()
        self.paused = False
        self.pause_start = 0
        self.total_pause = 0
        self.active_falls = []
        self.next_to_drop = 0
        self.pile_heights = [0 for _ in range(self.pile_cols)]

    def toggle_pause(self):
        if self.paused:
            self.total_pause += time.time() - self.pause_start
            self.paused = False
        else:
            self.pause_start = time.time()
            self.paused = True

    def elapsed_time(self):
        if self.paused:
            return self.pause_start - self.start_time - self.total_pause
        return time.time() - self.start_time - self.total_pause

    def remaining_time(self):
        return max(0, int(math.ceil(self.duration - self.elapsed_time())))

    def progress(self):
        return min(1, max(0, self.elapsed_time() / self.duration))

    def column_index(self, x):
        index = int((x + HALF_BOTTOM) / self.pile_res)
        return max(0, min(self.pile_cols - 1, index))

    def pile_height_at(self, x):
        return self.pile_heights[self.column_index(x)]

    def deposit(self, x, size):
        index = self.column_index(x)
        self.pile_heights[index] += size * 2

        for offset in range(1, 8):
            value = max(0, size * 2 - offset * 0.6)

            if index - offset >= 0:
                self.pile_heights[index - offset] += value * 0.25

            if index + offset < self.pile_cols:
                self.pile_heights[index + offset] += value * 0.25

    def landed_count(self):
        return sum(1 for g in self.grains if g.state == "landed")

    def update(self, dt):
        if self.paused:
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

            if g.state == "falling_top" and g.fall_y >= NECK_Y:
                g.state = "falling_bottom"

            if g.state == "falling_bottom":
                pile_top = BOTTOM_FLOOR_Y - self.pile_height_at(g.fall_x)

                if g.fall_y >= pile_top:
                    g.rest_y = pile_top
                    g.state = "landed"
                    self.deposit(g.fall_x, g.size)
                    continue

            still_falling.append(g)

        self.active_falls = still_falling

    def add_grains(self, n):
        for _ in range(n):
            self.grains.append(Grain())
        self.grain_count = len(self.grains)

    def remove_grains(self, n):
        if self.grain_count > n + 20:
            self.grains = self.grains[:-n]
            self.grain_count = len(self.grains)
            self.next_to_drop = min(self.next_to_drop, self.grain_count)

    def recolor(self):
        for g in self.grains:
            g.color = random_palette_color()

    def draw(self, surface, cx):
        progress = self.progress()

        def shift(p):
            return (p[0] + cx, p[1])

        glass_points = [shift(p) for p in [
            (-150, 50),
            (150, 50),
            (20, NECK_Y),
            (180, BOTTOM_FLOOR_Y + 15),
            (-180, BOTTOM_FLOOR_Y + 15),
            (-20, NECK_Y),
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

        if self.next_to_drop < self.grain_count and not self.paused:
            pygame.draw.line(surface, (230, 190, 110), shift((0, NECK_Y)), shift((0, NECK_Y + 160)), 2)

        ring_center = (cx, 56)
        ring_r = 26

        pygame.draw.circle(surface, BG_PANEL_LIGHT, ring_center, ring_r)
        pygame.draw.circle(surface, BORDER, ring_center, ring_r, 3)

        percent_text = FONT_SMALL.render(f"{int(progress * 100)}%", True, TEXT_BRIGHT)
        surface.blit(percent_text, (
            ring_center[0] - percent_text.get_width() // 2,
            ring_center[1] - percent_text.get_height() // 2
        ))

        time_label = "En pause" if self.paused else f"{self.remaining_time()} secondes restantes"
        time_surf = FONT_LABEL_BOLD.render(time_label, True, TEXT_BRIGHT)
        surface.blit(time_surf, (cx - time_surf.get_width() // 2, 90))

        if self.remaining_time() == 0 and not self.active_falls:
            done_surf = FONT_HUGE.render("Terminé", True, (255, 140, 140))
            surface.blit(done_surf, (cx - done_surf.get_width() // 2, HEIGHT - 70))


pause_btn = Button((20, 100, SIDEBAR_W - 40, 44), "Pause")
reset_btn = Button((20, 152, SIDEBAR_W - 40, 44), "Réinitialiser")
more_btn = Button((20, 204, 84, 40), "+ Grains")
less_btn = Button((116, 204, 84, 40), "- Grains")
palette_btn = Button((20, 304, SIDEBAR_W - 40, 44), "Changer palette")

hourglass = Hourglass(duration, grain_count)

running = True
last_t = time.time()

while running:
    now = time.time()
    dt = min(now - last_t, 0.05)
    last_t = now
    mouse_pos = pygame.mouse.get_pos()

    for btn in [pause_btn, reset_btn, more_btn, less_btn, palette_btn]:
        btn.hover = btn.contains(mouse_pos)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                hourglass.toggle_pause()
            elif event.key == pygame.K_r:
                hourglass.reset()
            elif event.key == pygame.K_c:
                state.palette_index = (state.palette_index + 1) % len(PALETTES)
                hourglass.recolor()
            elif event.key == pygame.K_ESCAPE:
                running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pause_btn.contains(mouse_pos):
                hourglass.toggle_pause()
            elif reset_btn.contains(mouse_pos):
                hourglass.reset()
            elif more_btn.contains(mouse_pos):
                hourglass.add_grains(50)
            elif less_btn.contains(mouse_pos):
                hourglass.remove_grains(50)
            elif palette_btn.contains(mouse_pos):
                state.palette_index = (state.palette_index + 1) % len(PALETTES)
                hourglass.recolor()

    hourglass.update(dt)

    screen.fill(BG_DARK)

    canvas_rect = pygame.Rect(SIDEBAR_W, 0, CANVAS_W, HEIGHT)
    canvas = screen.subsurface(canvas_rect)
    canvas.fill(BG_DARK)

    hourglass.draw(canvas, CANVAS_W // 2)

    pygame.draw.rect(screen, BG_PANEL, (0, 0, SIDEBAR_W, HEIGHT))
    pygame.draw.line(screen, BORDER, (SIDEBAR_W, 0), (SIDEBAR_W, HEIGHT))

    title = FONT_TITLE.render("Sablier", True, TEXT_BRIGHT)
    screen.blit(title, (20, 20))

    subtitle = FONT_SMALL.render("Art génératif interactif", True, TEXT_MUTED)
    screen.blit(subtitle, (20, 52))

    pause_btn.label = "Reprendre" if hourglass.paused else "Pause"

    pause_btn.draw(screen)
    reset_btn.draw(screen)
    more_btn.draw(screen)
    less_btn.draw(screen)
    palette_btn.draw(screen)

    grain_text = FONT_SMALL.render(f"{hourglass.grain_count} grains", True, TEXT_MUTED)
    screen.blit(grain_text, (20, 260))

    fallen_text = FONT_SMALL.render(f"{hourglass.landed_count()} grains tombés", True, TEXT_MUTED)
    screen.blit(fallen_text, (20, 280))

    palette_title = FONT_LABEL_BOLD.render("Palette actuelle", True, TEXT_BRIGHT)
    screen.blit(palette_title, (20, 365))

    palette_text = FONT_SMALL.render(PALETTES[state.palette_index]["name"], True, TEXT_MUTED)
    screen.blit(palette_text, (20, 390))

    x_start = 25
    y_palette = 430

    for i, color in enumerate(PALETTES[state.palette_index]["colors"]):
        pygame.draw.circle(screen, color, (x_start + i * 45, y_palette), 16)
        pygame.draw.circle(screen, TEXT_BRIGHT, (x_start + i * 45, y_palette), 16, 1)

    palette_hint = FONT_SMALL.render("Bouton ou C pour changer", True, TEXT_MUTED)
    screen.blit(palette_hint, (20, 465))

    controls = [
        "Espace : pause / reprise",
        "R : réinitialiser",
        "C : changer palette",
        "Échap : quitter"
    ]

    y = HEIGHT - 110
    for line in controls:
        surf = FONT_SMALL.render(line, True, TEXT_MUTED)
        screen.blit(surf, (20, y))
        y += 22

    pygame.display.flip()
    clock.tick(60)

pygame.quit()