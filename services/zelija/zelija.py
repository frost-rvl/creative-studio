import pygame
import math

pygame.init()

# ---- GRID & WINDOW ----
GRID_SIZE = 8
CELL_SIZE = 90
GRID_WIDTH = GRID_SIZE * CELL_SIZE
UI_WIDTH = 380
WIDTH = GRID_WIDTH + UI_WIDTH
HEIGHT = GRID_WIDTH

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zellij Builder")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("arial", 16)
BIG_FONT = pygame.font.SysFont("arial", 20, bold=True)

# ---- COLORS ----
PALETTE = [
    (192, 57, 43), (241, 196, 15), (41, 128, 185),
    (39, 174, 96), (230, 126, 34), (149, 165, 166)
]

# ---- SHAPES ----
class Shape:
    def __init__(self, color, size):
        self.color = color
        self.size = size
        self.rotation = 0

    def rotate(self, angle):
        self.rotation = (self.rotation + angle) % 360

    def rotate_points(self, points, center):
        rad = math.radians(self.rotation)
        rotated = []
        for x, y in points:
            dx, dy = x - center[0], y - center[1]
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)
            rotated.append((center[0] + rx, center[1] + ry))
        return rotated

class Circle(Shape):
    def draw(self, surf, rect):
        pygame.draw.circle(
            surf, self.color, rect.center,
            max(10, self.size // 2 - 12)
        )

class Square(Shape):
    def draw(self, surf, rect):
        s = self.size
        surf2 = pygame.Surface((s, s), pygame.SRCALPHA)
        pygame.draw.rect(surf2, self.color, (0, 0, s, s))
        rot = pygame.transform.rotate(surf2, self.rotation)
        r = rot.get_rect(center=rect.center)
        surf.blit(rot, r)

class Triangle(Shape):
    def draw(self, surf, rect):
        cx, cy = rect.center
        s = self.size // 2
        points = [
            (cx, cy - s),
            (cx - s, cy + s),
            (cx + s, cy + s)
        ]
        points = self.rotate_points(points, rect.center)
        pygame.draw.polygon(surf, self.color, points)

class Star(Shape):
    def draw(self, surf, rect):
        cx, cy = rect.center
        s = self.size // 2
        points = [
            (cx, cy - s), (cx + s//3, cy - s//3),
            (cx + s, cy - s//6), (cx + s//3, cy + s//3),
            (cx + s//2, cy + s),
            (cx, cy + s//2),
            (cx - s//2, cy + s),
            (cx - s//3, cy + s//3),
            (cx - s, cy - s//6),
            (cx - s//3, cy - s//3)
        ]
        points = self.rotate_points(points, rect.center)
        pygame.draw.polygon(surf, self.color, points)

SHAPE_CLASSES = {
    "Circle": Circle,
    "Square": Square,
    "Triangle": Triangle,
    "Star": Star
}

# ---- CELL ----
class Cell:
    def __init__(self, r, c):
        self.rect = pygame.Rect(
            c * CELL_SIZE,
            r * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        self.shape = None

    def draw(self, surf, selected):
        color = (255, 255, 255) if selected else (60, 60, 60)
        pygame.draw.rect(surf, color, self.rect, 3, border_radius=6)
        if self.shape:
            self.shape.draw(surf, self.rect)



# ---- APP ----
class App:
    def __init__(self):
        self.cells = [[Cell(r, c) for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]
        self.selected_shape = Circle
        self.selected_color = PALETTE[0]
        self.selected_cell = None
        self.delete_mode = False

    def get_counts(self):
        counts = {"Circle":0, "Square":0, "Triangle":0, "Star":0}
        for row in self.cells:
            for cell in row:
                if cell.shape:
                    counts[cell.shape.__class__.__name__] += 1
        return counts

    def draw_ui(self):
        x = GRID_WIDTH + 20

        draw("ZELLIJ BUILDER", x, 20, big=True)

        instructions = [
            "1–4 : select shape",
            "Click cell : place / select",
            "Q / E : rotate selected",
            "+ / - : resize selected",
            "D : delete mode",
            "C : clear grid"
        ]

        for i, t in enumerate(instructions):
            draw(t, x, 60 + i*24)

        draw("SHAPE REFERENCE", x, 220, big=True)
        refs = ["1 : Circle", "2 : Square", "3 : Triangle", "4 : Star"]
        for i, r in enumerate(refs):
            draw(r, x, 250 + i*22)

        draw("COLORS", x, 350, big=True)
        for i, col in enumerate(PALETTE):
            rect = pygame.Rect(x + (i%3)*50, 380 + (i//3)*50, 40, 40)
            pygame.draw.rect(screen, col, rect, border_radius=8)
            if col == self.selected_color:
                pygame.draw.rect(screen, (255,255,255), rect, 3, border_radius=8)

        draw("SHAPE COUNT", x, 500, big=True)
        y = 530
        for k, v in self.get_counts().items():
            draw(f"{k}: {v}", x, y)
            y += 22

        if self.delete_mode:
            draw("DELETE MODE ON", x, HEIGHT-40, color=(255,80,80), big=True)

    def run(self):
        running = True
        while running:
            clock.tick(60)
            screen.fill((30, 32, 40))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: self.selected_shape = Circle
                    if event.key == pygame.K_2: self.selected_shape = Square
                    if event.key == pygame.K_3: self.selected_shape = Triangle
                    if event.key == pygame.K_4: self.selected_shape = Star

                    if event.key == pygame.K_d:
                        self.delete_mode = not self.delete_mode

                    if event.key == pygame.K_c:
                        for row in self.cells:
                            for cell in row:
                                cell.shape = None
                        self.selected_cell = None

                    if self.selected_cell and self.selected_cell.shape:
                        if event.key == pygame.K_q:
                            self.selected_cell.shape.rotate(-15)
                        if event.key == pygame.K_e:
                            self.selected_cell.shape.rotate(15)
                        if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                            self.selected_cell.shape.size = min(
                                CELL_SIZE, self.selected_cell.shape.size + 6)
                        if event.key == pygame.K_MINUS:
                            self.selected_cell.shape.size = max(
                                20, self.selected_cell.shape.size - 6)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos

                    # palette
                    for i, col in enumerate(PALETTE):
                        rect = pygame.Rect(
                            GRID_WIDTH + 20 + (i%3)*50,
                            380 + (i//3)*50,
                            40, 40
                        )
                        if rect.collidepoint(mx, my):
                            self.selected_color = col

                    # grid
                    for row in self.cells:
                        for cell in row:
                            if cell.rect.collidepoint(mx, my):
                                if self.delete_mode:
                                    cell.shape = None
                                    if cell == self.selected_cell:
                                        self.selected_cell = None
                                else:
                                    if cell.shape:
                                        self.selected_cell = cell
                                    else:
                                        cell.shape = self.selected_shape(
                                            self.selected_color, CELL_SIZE)
                                        self.selected_cell = cell

            for row in self.cells:
                for cell in row:
                    cell.draw(screen, cell == self.selected_cell)

            self.draw_ui()
            pygame.display.flip()

        pygame.quit()

# ---- DRAW TEXT ----
def draw(text, x, y, color=(220,220,220), big=False):
    font = BIG_FONT if big else FONT
    screen.blit(font.render(text, True, color), (x, y))

# ---- RUN ----
# App().run()
