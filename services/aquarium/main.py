import pygame
import random
import math
import asyncio
import base64
import io
from js import window, console

pygame.init()

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aquarium procédural")

clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 20)
FONT_BIG = pygame.font.SysFont("Arial", 32, bold=True)
FONT_SMALL = pygame.font.SysFont("Arial", 16)

PALETTES = [
    {
        "name": "Océan bleu",
        "background": (10, 60, 120),
        "water": (20, 120, 180),
        "sand": (230, 200, 130)
    },
    {
        "name": "Récif tropical",
        "background": (0, 90, 120),
        "water": (0, 170, 190),
        "sand": (240, 210, 150)
    },
    {
        "name": "Nuit sous-marine",
        "background": (5, 15, 45),
        "water": (20, 60, 100),
        "sand": (160, 140, 100)
    }
]

palette_index = 0

def current_palette():
    return PALETTES[palette_index]

# ---- Fish ----
class Fish:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else random.randint(50, WIDTH - 50)
        self.y = y if y is not None else random.randint(100, HEIGHT - 150)
        self.size = random.randint(18, 45)
        self.speed = random.uniform(1.0, 3.0)
        self.direction = random.choice([-1, 1])
        self.color = random.choice([
            (255, 120, 90), (255, 200, 80), (120, 220, 255),
            (180, 120, 255), (120, 255, 160), (255, 140, 200)
        ])
        self.wave = random.uniform(0, math.pi * 2)

    def update(self):
        self.x += self.speed * self.direction
        self.wave += 0.06
        self.y += math.sin(self.wave) * 0.5
        if self.x < -80:
            self.x = WIDTH + 80
        if self.x > WIDTH + 80:
            self.x = -80

    def draw(self, surface):
        body_rect = pygame.Rect(
            self.x - self.size,
            self.y - self.size // 2,
            self.size * 2,
            self.size
        )
        pygame.draw.ellipse(surface, self.color, body_rect)

        if self.direction == 1:
            tail = [
                (self.x - self.size, self.y),
                (self.x - self.size - 22, self.y - 15),
                (self.x - self.size - 22, self.y + 15)
            ]
            eye_x = self.x + self.size // 2
        else:
            tail = [
                (self.x + self.size, self.y),
                (self.x + self.size + 22, self.y - 15),
                (self.x + self.size + 22, self.y + 15)
            ]
            eye_x = self.x - self.size // 2

        pygame.draw.polygon(surface, self.color, tail)
        pygame.draw.circle(surface, (255, 255, 255), (int(eye_x), int(self.y - 5)), 4)
        pygame.draw.circle(surface, (0, 0, 0), (int(eye_x), int(self.y - 5)), 2)

# ---- Bubble ----
class Bubble:
    def __init__(self):
        self.x = random.randint(20, WIDTH - 20)
        self.y = random.randint(HEIGHT, HEIGHT + 300)
        self.radius = random.randint(3, 10)
        self.speed = random.uniform(1, 3)

    def update(self):
        self.y -= self.speed
        self.x += math.sin(self.y * 0.03) * 0.4
        if self.y < -20:
            self.y = random.randint(HEIGHT, HEIGHT + 200)
            self.x = random.randint(20, WIDTH - 20)

    def draw(self, surface):
        pygame.draw.circle(surface, (210, 240, 255), (int(self.x), int(self.y)), self.radius, 1)

# ---- Seaweed ----
class Seaweed:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(60, 140)
        self.color = random.choice([(40, 180, 90), (30, 140, 80), (70, 210, 120)])
        self.phase = random.random() * math.pi * 2

    def draw(self, surface, time_value):
        base_y = HEIGHT - 55
        points = []
        for i in range(0, self.height, 10):
            sway = math.sin(time_value * 2 + self.phase + i * 0.1) * 8
            points.append((self.x + sway, base_y - i))
        if len(points) > 1:
            pygame.draw.lines(surface, self.color, False, points, 4)

# ---- Aquarium ----
class Aquarium:
    def __init__(self):
        self.fishes = [Fish() for _ in range(12)]
        self.bubbles = [Bubble() for _ in range(45)]
        self.seaweeds = [Seaweed(x) for x in range(40, WIDTH, 70)]

    def regenerate(self):
        self.fishes = [Fish() for _ in range(12)]
        self.bubbles = [Bubble() for _ in range(45)]
        self.seaweeds = [Seaweed(x) for x in range(40, WIDTH, 70)]

    def add_fish(self, x, y):
        self.fishes.append(Fish(x, y))

    def add_bubbles(self):
        for _ in range(15):
            self.bubbles.append(Bubble())

    def update(self):
        for fish in self.fishes:
            fish.update()
        for bubble in self.bubbles:
            bubble.update()

    def draw_background(self, surface):
        palette = current_palette()
        surface.fill(palette["background"])
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            color = (
                int(palette["background"][0] * (1 - ratio) + palette["water"][0] * ratio),
                int(palette["background"][1] * (1 - ratio) + palette["water"][1] * ratio),
                int(palette["background"][2] * (1 - ratio) + palette["water"][2] * ratio)
            )
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))
        pygame.draw.rect(surface, palette["sand"], (0, HEIGHT - 55, WIDTH, 55))
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(HEIGHT - 50, HEIGHT - 5)
            pygame.draw.circle(surface, (190, 160, 100), (x, y), 1)

    def draw(self, surface, time_value):
        self.draw_background(surface)
        for bubble in self.bubbles:
            bubble.draw(surface)
        for seaweed in self.seaweeds:
            seaweed.draw(surface, time_value)
        for fish in self.fishes:
            fish.draw(surface)

# ---- App ----
class AquariumApp:
    def __init__(self):
        self.screen = screen
        self.clock = clock
        self.aquarium = Aquarium()
        self.time_value = 0
        self.paused = False

    def capture_aquarium(self):
        """Capture only the aquarium scene (no UI text) on the same background."""
        surf = pygame.Surface((WIDTH, HEIGHT))
        self.aquarium.draw(surf, self.time_value)
        buf = io.BytesIO()
        pygame.image.save(surf, buf, "png")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        return b64

    def toggle_pause(self):
        self.paused = not self.paused

    def reset(self):
        self.aquarium.regenerate()
        self.time_value = 0

    def change_palette(self):
        global palette_index
        palette_index = (palette_index + 1) % len(PALETTES)
        # No need to recolor fish; they keep their colors.
        # The background will change on next redraw.

    def add_bubbles(self):
        self.aquarium.add_bubbles()

    async def run(self):
        running = True
        while running:
            self.time_value += 0.02

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_b:
                        self.add_bubbles()
                    elif event.key == pygame.K_c:
                        self.change_palette()
                    elif event.key == pygame.K_SPACE:
                        self.toggle_pause()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not self.paused:
                    x, y = pygame.mouse.get_pos()
                    self.aquarium.add_fish(x, y)

            if not self.paused:
                self.aquarium.update()

            # Draw
            self.screen.fill((0, 0, 0))
            self.aquarium.draw(self.screen, self.time_value)

            # UI Text (always on top)
            title = FONT_BIG.render("Aquarium procédural", True, (255, 255, 255))
            self.screen.blit(title, (20, 20))

            info = FONT.render(
                "Clic : ajouter poisson | B : bulles | C : ambiance | R : régénérer | Échap : quitter",
                True, (255, 255, 255)
            )
            self.screen.blit(info, (20, 60))

            count = FONT.render(
                f"Poissons : {len(self.aquarium.fishes)} | Bulles : {len(self.aquarium.bubbles)} | Palette : {current_palette()['name']}",
                True, (255, 255, 255)
            )
            self.screen.blit(count, (20, 90))

            if self.paused:
                pause_text = FONT_SMALL.render("⏸ PAUSÉ", True, (255, 255, 100))
                self.screen.blit(pause_text, (WIDTH - pause_text.get_width() - 20, 20))

            pygame.display.flip()
            self.clock.tick(60)
            await asyncio.sleep(0)

        pygame.quit()

# ---- JS EXPOSURE ----
app_instance = None

def js_capture_aquarium():
    if app_instance is None:
        return ""
    return app_instance.capture_aquarium()

window.captureAquarium = js_capture_aquarium

# ---- RUN ----
if __name__ == "__main__":
    app = AquariumApp()
    app_instance = app
    asyncio.run(app.run())