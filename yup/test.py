import pygame
import random
import json
import os

# ---------------------------
# Instellingen
# ---------------------------
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60
pygame.init()
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Patty Dadies Runner - Complete Editie")
FONT = pygame.font.SysFont("arial", 24, bold=True)
big_font = pygame.font.SysFont("arial", 36, bold=True)

clock = pygame.time.Clock()
running = True
current_state = "menu"

# Data bestand
SAVE_FILE = "patty_runner_data.json"

# Player constants
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 50
PLAYER_Y_BASE = WINDOW_HEIGHT - 120
PLAYER_X_START = WINDOW_WIDTH // 2 - PLAYER_WIDTH // 2
PLAYER_JUMP_VELOCITY = -20
PLAYER_MOVE_SPEED = 8
GRAVITY = 0.6
MAX_JUMPS = 1
mountains = []

class Mountain:
    def __init__(self, x, base, width, height, color, speed):
        self.x = x
        self.base = base
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed

    def draw(self, surface):
        peak_x = self.x + self.width // 2
        pygame.draw.polygon(
            surface,
            self.color,
            [
                (self.x, self.base),  # Links onder
                (peak_x, self.base - self.height),  # Top
                (self.x + self.width, self.base),  # Rechts onder
            ],
        )

    def update(self):
        self.x -= self.speed
        if self.x + self.width < 0:
            # Reset naar rechts en randomize hoogte/breedte
            self.x = WINDOW_WIDTH
            self.width = random.randint(120, 240)
            self.height = random.randint(40, 140)

for _ in range(5):
    x = random.randint(0, WINDOW_WIDTH)
    base = PLAYER_Y_BASE + PLAYER_HEIGHT  # Onderkant bergen op grasniveau
    width = random.randint(120, 240)
    height = random.randint(40, 140)
    color = (110, 90, 70)  # Bruin/grijs
    speed = random.uniform(0.5, 1.2)
    mountains.append(Mountain(x, base, width, height, color, speed))
    
# Player visuals
burger_image = pygame.image.load("./burger.png").convert_alpha()
burger_image = pygame.transform.scale(burger_image, (PLAYER_WIDTH, PLAYER_HEIGHT))

# Vallende objecten
FALL_SPEED_MIN = 5
FALL_SPEED_MAX = 12
SPAWN_INTERVAL_MIN = 300
SPAWN_INTERVAL_MAX = 800

# Objecten
TRASH_SIZE = 32
OBSTACLE_WIDTH = 44
OBSTACLE_HEIGHT = 60

# Kleuren
SKY_TOP = (135, 206, 250)
SKY_BOTTOM = (176, 224, 230)
GRASS = (50, 200, 70)
TEXT_COLOR = (255, 255, 255)
TEXT_SHADOW = (0, 0, 0)
MENU_BG = (40, 40, 60)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)

class Object:
    def __init__(self, height, width, color, x, y):
        self.height = height
        self.width = width
        self.color = color
        self.x = x
        self.y = y

    def Draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
    
    def MoveDown(self, speed):
        self.y += speed
    
    def get_rect(self):
        """Return pygame.Rect for collision detection"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def collides_with(self, other):
        """Check collision with another Object"""
        return self.get_rect().colliderect(other.get_rect())

class Player(Object):
    def __init__(self, height, width, color, x, y):
        super().__init__(height, width, color, x, y)
        self.y_velocity = 0.0
        self.jumps_left = MAX_JUMPS

    def MoveLeft(self, speed):
        self.x -= speed
        self.x = max(0, self.x)  # Don't go off left edge

    def MoveRight(self, speed):
        self.x += speed
        self.x = min(self.x, WINDOW_WIDTH - self.width)  # Don't go off right edge
    
    def Jump(self):
        if self.jumps_left > 0:
            self.y_velocity = PLAYER_JUMP_VELOCITY
            self.jumps_left -= 1
    
    def Update(self):
        """Update player physics"""
        self.y_velocity += GRAVITY
        self.y += int(self.y_velocity)
        
        # Ground collision
        if self.y >= PLAYER_Y_BASE:
            self.y = PLAYER_Y_BASE
            self.y_velocity = 0.0
            self.jumps_left = MAX_JUMPS
        
        # Ceiling collision
        if self.y < 20:
            self.y = 20
            self.y_velocity = 0.0
    
    def DrawBurger(self, surface, alpha=255):
        temp_image = burger_image.copy()
        temp_image.set_alpha(alpha)
        surface.blit(temp_image, (self.x, self.y))

class FallingItem(Object):
    def __init__(self, x, y, width, height, fall_speed, item_type, colors=None):
        # Use first color as default, or white if no colors provided
        color = colors[0] if colors else (255, 255, 255)
        super().__init__(height, width, color, x, y)
        self.fall_speed = fall_speed
        self.type = item_type
        self.colors = colors or [(255, 255, 255)]
        self.color_index = random.randint(0, len(self.colors) - 1)
        self.color = self.colors[self.color_index]
   
    def Update(self):
        self.MoveDown(self.fall_speed)
   
    def is_off_screen(self):
        return self.y > WINDOW_HEIGHT
    
    def DrawTrash(self, surface):
        """Draw as trash with custom colors"""
        pygame.draw.rect(surface, self.color, self.get_rect(), border_radius=6)
        pygame.draw.rect(surface, (230, 230, 230), 
                        (self.x + self.width // 4, self.y, self.width // 2, 6), border_radius=3)
    
    def DrawObstacle(self, surface):
        """Draw as obstacle (trash can) with custom colors"""
        rect = self.get_rect()
        pygame.draw.rect(surface, self.colors[0], rect, border_radius=6)
        pygame.draw.rect(surface, self.colors[1], (self.x, self.y, self.width, 8))
        pygame.draw.rect(surface, self.colors[2], 
                        (self.x + 6, self.y + 10, self.width - 12, self.height - 20))

# Shop items
TRASH_COLORS = {
    "Standaard": [(200, 30, 30), (30, 30, 200), (200, 200, 30)],
    "Galaxy": [(138, 43, 226), (72, 61, 139), (25, 25, 112)],
    "Neon": [(57, 255, 20), (255, 20, 147), (0, 191, 255)],
    "Goud": [(255, 215, 0), (255, 140, 0), (218, 165, 32)],
    "Regenboog": [(255, 0, 127), (127, 255, 0), (0, 127, 255)]
}

OBSTACLE_COLORS = {
    "Standaard": [(100, 100, 100), (150, 150, 150), (60, 60, 60)],
    "Roest": [(139, 69, 19), (160, 82, 45), (101, 67, 33)],
    "Chrome": [(192, 192, 192), (220, 220, 220), (169, 169, 169)],
    "Groen": [(34, 139, 34), (50, 205, 50), (0, 100, 0)],
    "Paars": [(75, 0, 130), (138, 43, 226), (147, 112, 219)]
}

ITEM_PRICES = {
    "Galaxy": 50, "Neon": 100, "Goud": 200, "Regenboog": 500,
    "Roest": 30, "Chrome": 80, "Groen": 120, "Paars": 300
}

# ---------------------------
# Data management
# ---------------------------
def load_game_data():
    """Laad opgeslagen data"""
    default_data = {
        "high_score": 0,
        "total_trash": 0,
        "sound_enabled": True,
        "owned_trash_colors": ["Standaard"],
        "owned_obstacle_colors": ["Standaard"],
        "selected_trash_color": "Standaard",
        "selected_obstacle_color": "Standaard"
    }
   
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                # Zorg dat alle vereiste keys bestaan
                for key, default_value in default_data.items():
                    if key not in data:
                        data[key] = default_value
                return data
        except:
            return default_data
    return default_data

def save_game_data(data):
    """Sla data op"""
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

# ---------------------------
# Tekenfuncties
# ---------------------------
def draw_background(surface, clouds):
    """Gradient lucht + grasgrond + wolken"""
    for y in range(WINDOW_HEIGHT):
        ratio = y / WINDOW_HEIGHT
        r = int(SKY_TOP[0] * (1 - ratio) + SKY_BOTTOM[0] * ratio)
        g = int(SKY_TOP[1] * (1 - ratio) + SKY_BOTTOM[1] * ratio)
        b = int(SKY_TOP[2] * (1 - ratio) + SKY_BOTTOM[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))
    pygame.draw.rect(surface, GRASS, (0, PLAYER_Y_BASE + PLAYER_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT))
    for cloud in clouds:
        pygame.draw.ellipse(surface, (255, 255, 255), cloud)
    # In drawbackground
    for mountain in mountains:
        mountain.draw(surface)

def render_text(surface, text, font, pos, color, shadow_color=None):
    """Tekst met optionele schaduw"""
    if shadow_color:
        shadow = font.render(text, True, shadow_color)
        surface.blit(shadow, (pos[0] + 2, pos[1] + 2))
    surf = font.render(text, True, color)
    surface.blit(surf, pos)

def draw_button(surface, rect, text, font, hovered=False):
    """Teken knop"""
    color = BUTTON_HOVER if hovered else BUTTON_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=10)
    pygame.draw.rect(surface, (255, 255, 255), rect, 3, border_radius=10)
    text_surf = font.render(text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

# ---------------------------
# Button class
# ---------------------------
class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
   
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                return True
        return False
   
    def draw(self, surface):
        draw_button(surface, self.rect, self.text, self.font, self.hovered)

# ---------------------------
# Game States
# ---------------------------
def show_start_menu(screen, font, big_font, game_data):
    """Toon startscherm met opties"""
    clock = pygame.time.Clock()
   
    # Knoppen
    start_btn = Button(WINDOW_WIDTH//2 - 100, 200, 200, 50, "START SPEL", font)
    shop_btn = Button(WINDOW_WIDTH//2 - 100, 270, 200, 50, "SHOP", font)
    sound_btn = Button(WINDOW_WIDTH//2 - 100, 340, 200, 50,
                      f"GELUID: {'AAN' if game_data['sound_enabled'] else 'UIT'}", font)
    quit_btn = Button(WINDOW_WIDTH//2 - 100, 410, 200, 50, "AFSLUITEN", font)
   
    buttons = [start_btn, shop_btn, sound_btn, quit_btn]
   
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            for i, button in enumerate(buttons):
                if button.handle_event(event):
                    if i == 0:  # Start
                        return "play"
                    elif i == 1:  # Shop
                        return "shop"
                    elif i == 2:  # Sound toggle
                        game_data['sound_enabled'] = not game_data['sound_enabled']
                        sound_btn.text = f"GELUID: {'AAN' if game_data['sound_enabled'] else 'UIT'}"
                        save_game_data(game_data)
        
                        # Muziek starten of stoppen op basis van de toggle
                        if game_data['sound_enabled']:
                            try:
                                pygame.mixer.music.load(MUSIC_FILE)
                                pygame.mixer.music.play(-1)
                            except:
                                print("Muziekbestand niet gevonden of kan niet geladen worden")
                        else:
                            pygame.mixer.music.stop()
                        
                    elif i == 3:  # Quit
                        return "quit" 
        # Tekenen
        screen.fill(MENU_BG)
        
        # Titel
        title = big_font.render("PATTY DADIES RUNNER", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
        screen.blit(title, title_rect)
        
        # Stats
        stats_y = 480
        render_text(screen, f"Hoogste Score: {game_data['high_score']}", font, (50, stats_y), TEXT_COLOR)
        render_text(screen, f"Totaal Afval: {game_data['total_trash']}", font, (50, stats_y + 30), TEXT_COLOR)
        
        # Knoppen
        for button in buttons:
            button.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

def show_shop(screen, font, big_font, game_data):
    """Professional shop interface with modern design"""
    clock = pygame.time.Clock()
    scroll_offset = 0
    max_scroll = 0
    animation_time = 0
    selected_category = "trash"  # "trash" or "obstacles"

    # Professional color scheme
    SHOP_BG = (25, 28, 35)
    CARD_BG = (40, 44, 52)
    ACCENT_COLOR = (88, 166, 255)
    SUCCESS_COLOR = (46, 204, 113)
    WARNING_COLOR = (255, 193, 7)
    DANGER_COLOR = (231, 76, 60)
    TEXT_PRIMARY = (248, 249, 250)
    TEXT_SECONDARY = (173, 181, 189)
    BORDER_COLOR = (73, 80, 87)

    # Enhanced fonts
    title_font = pygame.font.SysFont("arial", 32, bold=True)
    subtitle_font = pygame.font.SysFont("arial", 20, bold=True)
    body_font = pygame.font.SysFont("arial", 16)
    small_font = pygame.font.SysFont("arial", 14)

    # Header buttons
    back_btn = Button(30, 30, 120, 45, "← TERUG", font)
    trash_tab = Button(200, 90, 150, 40, "AFVAL", font)
    obstacle_tab = Button(360, 90, 150, 40, "OBSTAKELS", font)

    def draw_professional_button(surface, rect, text, font, style="primary", hovered=False, disabled=False):
        """Draw modern button with various styles"""
        if disabled:
            bg_color = (52, 58, 64)
            text_color = (108, 117, 125)
        elif style == "success":
            bg_color = SUCCESS_COLOR if not hovered else (40, 180, 99)
            text_color = (255, 255, 255)
        elif style == "warning":
            bg_color = WARNING_COLOR if not hovered else (241, 196, 15)
            text_color = (33, 37, 41)
        elif style == "danger":
            bg_color = DANGER_COLOR if not hovered else (192, 57, 43)
            text_color = (255, 255, 255)
        else:  # primary
            bg_color = ACCENT_COLOR if not hovered else (74, 144, 226)
            text_color = (255, 255, 255)

        if hovered and not disabled:
            bg_color = tuple(min(255, c + 20) for c in bg_color)

        # Draw button with shadow
        shadow_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
        pygame.draw.rect(surface, (0, 0, 0, 50), shadow_rect, border_radius=8)
        pygame.draw.rect(surface, bg_color, rect, border_radius=8)

        # Border
        if not disabled:
            pygame.draw.rect(surface, tuple(min(255, c + 30) for c in bg_color), rect, 2, border_radius=8)

        # Text
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    def draw_item_card(surface, x, y, width, height, item_data, hovered=False):
        """Draw professional item card"""
        card_rect = pygame.Rect(x, y, width, height)

        # Card shadow
        shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
        pygame.draw.rect(surface, (0, 0, 0, 30), shadow_rect, border_radius=12)

        # Card background
        card_color = CARD_BG
        if hovered:
            card_color = tuple(min(255, c + 15) for c in CARD_BG)

        pygame.draw.rect(surface, card_color, card_rect, border_radius=12)
        pygame.draw.rect(surface, BORDER_COLOR, card_rect, 2, border_radius=12)

        # Content
        name = item_data['name']
        colors = item_data['colors']
        price = item_data['price']
        owned = item_data['owned']
        selected = item_data['selected']
        can_afford = item_data['can_afford']

        # Item name
        name_surf = subtitle_font.render(name, True, TEXT_PRIMARY)
        surface.blit(name_surf, (x + 20, y + 15))

        # Color preview
        preview_x = x + 20
        preview_y = y + 50
        for i, color in enumerate(colors):
            color_rect = pygame.Rect(preview_x + i * 35, preview_y, 30, 30)
            pygame.draw.rect(surface, color, color_rect, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), color_rect, 2, border_radius=6)

        # Status and price
        if owned:
            status_text = "GEKOCHT"
            status_color = SUCCESS_COLOR

            # Selection indicator
            if selected:
                indicator_rect = pygame.Rect(x + width - 40, y + 15, 25, 25)
                pygame.draw.circle(surface, SUCCESS_COLOR, indicator_rect.center, 12)
                pygame.draw.circle(surface, (255, 255, 255), indicator_rect.center, 6)
        else:
            status_text = f"{price} afval"
            status_color = TEXT_PRIMARY if can_afford else DANGER_COLOR

        status_surf = body_font.render(status_text, True, status_color)
        surface.blit(status_surf, (x + 20, y + 90))

        # Action buttons for owned items
        if owned:
            use_btn_rect = pygame.Rect(x + width - 180, y + height - 45, 80, 30)
            deselect_btn_rect = pygame.Rect(x + width - 90, y + height - 45, 80, 30)

            # Use button
            use_style = "warning" if not selected else "success"
            use_text = "ACTIEF" if selected else "GEBRUIK"
            draw_professional_button(surface, use_btn_rect, use_text, small_font, use_style, False, selected)

            # Deselect button (only if selected)
            if selected:
                draw_professional_button(surface, deselect_btn_rect, "RESET", small_font, "danger")

            return use_btn_rect, deselect_btn_rect if selected else None
        else:
            # Buy button
            buy_btn_rect = pygame.Rect(x + width - 100, y + height - 45, 90, 30)
            buy_style = "success" if can_afford else "danger"
            buy_text = "KOPEN" if can_afford else "TE DUUR"
            draw_professional_button(surface, buy_btn_rect, buy_text, small_font, buy_style, False, not can_afford)
            return buy_btn_rect, None

    def calculate_max_scroll():
        """Calculate maximum scroll based on content"""
        items_count = len(TRASH_COLORS) + len(OBSTACLE_COLORS) - 2  # -2 for "Standaard" items
        cards_per_row = 2
        rows = (items_count + cards_per_row - 1) // cards_per_row
        content_height = rows * 180 + 200  # 180 per row + padding
        return max(0, content_height - (WINDOW_HEIGHT - 200))

    max_scroll = calculate_max_scroll()

    while True:
        animation_time += clock.get_time()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            # Smooth scrolling
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * 40
                scroll_offset = max(0, min(max_scroll, scroll_offset))

            # Back button
            if back_btn.handle_event(event):
                return "menu"

            # Tab switching
            if trash_tab.handle_event(event):
                selected_category = "trash"
            if obstacle_tab.handle_event(event):
                selected_category = "obstacles"

            # Item interactions
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Calculate item positions and handle clicks
                card_y = 180 - scroll_offset
                card_width = 380
                card_height = 160
                cards_per_row = 2
                margin = 20

                current_items = TRASH_COLORS if selected_category == "trash" else OBSTACLE_COLORS
                owned_key = 'owned_trash_colors' if selected_category == "trash" else 'owned_obstacle_colors'
                selected_key = 'selected_trash_color' if selected_category == "trash" else 'selected_obstacle_color'

                item_index = 0
                for name, colors in current_items.items():
                    if name == "Standaard":
                        continue

                    row = item_index // cards_per_row
                    col = item_index % cards_per_row

                    x = 50 + col * (card_width + margin)
                    y = card_y + row * (card_height + margin)

                    if y > -card_height and y < WINDOW_HEIGHT:  # Only check visible cards
                        owned = name in game_data[owned_key]
                        price = ITEM_PRICES.get(name, 0)
                        can_afford = game_data['total_trash'] >= price
                        selected = game_data[selected_key] == name

                        card_rect = pygame.Rect(x, y, card_width, card_height)

                        if owned:
                            use_btn_rect = pygame.Rect(x + card_width - 180, y + card_height - 45, 80, 30)
                            deselect_btn_rect = pygame.Rect(x + card_width - 90, y + card_height - 45, 80, 30)

                            if use_btn_rect.collidepoint(mouse_pos) and not selected:
                                game_data[selected_key] = name
                                save_game_data(game_data)
                            elif selected and deselect_btn_rect.collidepoint(mouse_pos):
                                game_data[selected_key] = "Standaard"
                                save_game_data(game_data)
                        else:
                            buy_btn_rect = pygame.Rect(x + card_width - 100, y + card_height - 45, 90, 30)
                            if buy_btn_rect.collidepoint(mouse_pos) and can_afford:
                                game_data['total_trash'] -= price
                                game_data[owned_key].append(name)
                                game_data[selected_key] = name
                                save_game_data(game_data)

                    item_index += 1

        # DRAWING
        screen.fill(SHOP_BG)

        # Animated background pattern
        for i in range(0, WINDOW_WIDTH + 100, 100):
            for j in range(0, WINDOW_HEIGHT + 100, 100):
                alpha = (50 + 20 * pygame.math.Vector2(i, j).length() / 100 + animation_time * 0.05) % 100
                color = (*ACCENT_COLOR[:3], int(alpha))
                pygame.draw.circle(screen, color, (i, j), 2)

        # Header with gradient
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 150)
        for y in range(150):
            ratio = y / 150
            color = tuple(int(SHOP_BG[i] * (1 - ratio) + CARD_BG[i] * ratio) for i in range(3))
            pygame.draw.line(screen, color, (0, y), (WINDOW_WIDTH, y))

        # Title
        title_surf = title_font.render("PREMIUM SHOP", True, TEXT_PRIMARY)
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)

        # Navigation tabs
        back_btn.draw(screen)

        # Category tabs
        trash_active = selected_category == "trash"
        obstacle_active = selected_category == "obstacles"

        trash_color = ACCENT_COLOR if trash_active else BORDER_COLOR
        obstacle_color = ACCENT_COLOR if obstacle_active else BORDER_COLOR

        pygame.draw.rect(screen, trash_color, trash_tab.rect, border_radius=8)
        pygame.draw.rect(screen, obstacle_color, obstacle_tab.rect, border_radius=8)

        if trash_active:
            pygame.draw.rect(screen, (255, 255, 255), trash_tab.rect, 2, border_radius=8)
        if obstacle_active:
            pygame.draw.rect(screen, (255, 255, 255), obstacle_tab.rect, 2, border_radius=8)

        trash_text = subtitle_font.render("AFVAL", True, TEXT_PRIMARY)
        obstacle_text = subtitle_font.render("OBSTAKELS", True, TEXT_PRIMARY)

        screen.blit(trash_text, trash_text.get_rect(center=trash_tab.rect.center))
        screen.blit(obstacle_text, obstacle_text.get_rect(center=obstacle_tab.rect.center))

        # Content area with clipping
        content_rect = pygame.Rect(0, 150, WINDOW_WIDTH, WINDOW_HEIGHT - 200)
        screen.set_clip(content_rect)

        # Draw items
        current_items = TRASH_COLORS if selected_category == "trash" else OBSTACLE_COLORS
        owned_key = 'owned_trash_colors' if selected_category == "trash" else 'owned_obstacle_colors'
        selected_key = 'selected_trash_color' if selected_category == "trash" else 'selected_obstacle_color'

        card_y = 180 - scroll_offset
        card_width = 380
        card_height = 160
        cards_per_row = 2
        margin = 20

        item_index = 0
        for name, colors in current_items.items():
            if name == "Standaard":
                continue

            row = item_index // cards_per_row
            col = item_index % cards_per_row

            x = 50 + col * (card_width + margin)
            y = card_y + row * (card_height + margin)

            # Only draw visible cards
            if y > -card_height and y < WINDOW_HEIGHT:
                owned = name in game_data[owned_key]
                price = ITEM_PRICES.get(name, 0)
                can_afford = game_data['total_trash'] >= price
                selected = game_data[selected_key] == name

                item_data = {
                    'name': name,
                    'colors': colors,
                    'price': price,
                    'owned': owned,
                    'selected': selected,
                    'can_afford': can_afford
                }

                card_rect = pygame.Rect(x, y, card_width, card_height)
                hovered = card_rect.collidepoint(mouse_pos)

                draw_item_card(screen, x, y, card_width, card_height, item_data, hovered)

            item_index += 1

        screen.set_clip(None)

        # Scroll indicator
        if max_scroll > 0:
            scroll_bar_height = max(20, int((WINDOW_HEIGHT - 200) * (WINDOW_HEIGHT - 200) / (
                        max_scroll + WINDOW_HEIGHT - 200)))
            scroll_bar_y = 150 + int((scroll_offset / max_scroll) * (WINDOW_HEIGHT - 200 - scroll_bar_height))

            pygame.draw.rect(screen, BORDER_COLOR, (WINDOW_WIDTH - 10, 150, 8, WINDOW_HEIGHT - 200), border_radius=4)
            pygame.draw.rect(screen, ACCENT_COLOR, (WINDOW_WIDTH - 10, scroll_bar_y, 8, scroll_bar_height),
                             border_radius=4)

        # Footer
        footer_rect = pygame.Rect(0, WINDOW_HEIGHT - 50, WINDOW_WIDTH, 50)
        pygame.draw.rect(screen, CARD_BG, footer_rect)

        footer_text = "Gemaakt door team PattyDaddy  |  2025"
        footer_surf = small_font.render(footer_text, True, TEXT_SECONDARY)
        footer_text_rect = footer_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 25))
        screen.blit(footer_surf, footer_text_rect)

        pygame.display.flip()
        clock.tick(FPS)

def create_falling_trash(colors):
    x = random.randint(0, WINDOW_WIDTH - TRASH_SIZE)
    y = -TRASH_SIZE
    fall_speed = random.uniform(FALL_SPEED_MIN, FALL_SPEED_MAX)
    return FallingItem(x, y, TRASH_SIZE, TRASH_SIZE, fall_speed, 'trash', colors)

def create_falling_obstacle(colors):
    x = random.randint(0, WINDOW_WIDTH - OBSTACLE_WIDTH)
    y = -OBSTACLE_HEIGHT
    fall_speed = random.uniform(FALL_SPEED_MIN, FALL_SPEED_MAX)
    return FallingItem(x, y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT, fall_speed, 'obstacle', colors)

def schedule_next_spawn():
    return random.randint(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_MAX)

def play_game(screen, font, big_font, game_data):
    """Hoofdspel - eindloos overleven"""
    clock = pygame.time.Clock()
    
    # Create player using custom class
    player = Player(PLAYER_HEIGHT, PLAYER_WIDTH, (255, 0, 0), PLAYER_X_START, PLAYER_Y_BASE)
    
    # Game variabelen
    falling_items = []
    clouds = [pygame.Rect(random.randint(0, WINDOW_WIDTH), random.randint(20, 150), 100, 40) for _ in range(5)]
    
    score = 0
    game_start = pygame.time.get_ticks()
    last_spawn = pygame.time.get_ticks()
    next_spawn = schedule_next_spawn()
    
    running = True
    game_over = False
    keys_pressed = set()
    
    # Kleuren ophalen
    trash_colors = TRASH_COLORS[game_data['selected_trash_color']]
    obstacle_colors = OBSTACLE_COLORS[game_data['selected_obstacle_color']]
    
    # Printer animation variables
    class Printer:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.width = 120
            self.height = 100
            self.print_progress = 0  # 0 to 100 for burger print animation
            self.fade_out = 255  # Alpha for printer fade-out
            self.active = True
        
        def update(self, dt):
            if self.print_progress < 100:
                self.print_progress += 100 * (dt / 1000)  # Progress based on frame time (complete in ~1s)
            elif self.fade_out > 0:
                self.fade_out -= 255 * (dt / 500)  # Fade out in ~0.5s
                if self.fade_out <= 0:
                    self.active = False
        
        def draw(self, surface, player):
            if not self.active:
                return
            
            # Printer frame (dark gray with blue glow)
            printer_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            printer_surface.set_alpha(int(self.fade_out))
            pygame.draw.rect(printer_surface, (50, 50, 50), (0, 0, self.width, self.height), border_radius=10)
            pygame.draw.rect(printer_surface, (0, 0, 100, 100), (5, 5, self.width - 10, self.height - 10), border_radius=8)
            
            # Printing platform
            pygame.draw.rect(printer_surface, (150, 150, 150), (10, self.height - 20, self.width - 20, 10))
            
            # Burger printing animation (bottom-up reveal)
            if self.print_progress > 0:
                print_height = int(PLAYER_HEIGHT * (self.print_progress / 100))
                if print_height > 0:
                    burger_x = self.x + self.width // 2 - PLAYER_WIDTH // 2
                    burger_y = self.y + self.height - 10 - print_height
                    sub_rect = (0, PLAYER_HEIGHT - print_height, PLAYER_WIDTH, print_height)
                    subsurface = burger_image.subsurface(sub_rect)
                    surface.blit(subsurface, (burger_x, burger_y))
            
            surface.blit(printer_surface, (self.x, self.y))
    
    # Initialize printer above player
    printer = Printer(PLAYER_X_START - (120 - PLAYER_WIDTH) // 2, PLAYER_Y_BASE - 50)
    
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", score
            if event.type == pygame.KEYDOWN:
                keys_pressed.add(event.key)
                if event.key == pygame.K_ESCAPE and game_over:
                    return "menu", score
                if not game_over and not printer.active:  # Only allow jump if printer is done
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        player.Jump()
            if event.type == pygame.KEYUP:
                keys_pressed.discard(event.key)
        
        if not game_over:
            # Beweging using custom class methods, only if printer is done
            if not printer.active:
                if pygame.K_LEFT in keys_pressed or pygame.K_a in keys_pressed:
                    player.MoveLeft(PLAYER_MOVE_SPEED)
                if pygame.K_RIGHT in keys_pressed or pygame.K_d in keys_pressed:
                    player.MoveRight(PLAYER_MOVE_SPEED)
            
            # Update player physics
            player.Update()
            
            # Update printer
            printer.update(dt)
            for mountain in mountains:
                mountain.update()
            # Wolken
            for c in clouds:
                c.x -= 1
                if c.right < 0:
                    c.x = WINDOW_WIDTH + random.randint(50, 200)
                    c.y = random.randint(20, 150)
            
            # Spawn objecten, only after printer is done
            if not printer.active:
                now = pygame.time.get_ticks()
                if now - last_spawn >= next_spawn:
                    if random.random() < 0.25:
                        falling_items.append(create_falling_trash(trash_colors))
                    else:
                        falling_items.append(create_falling_obstacle(obstacle_colors))
                    last_spawn = now
                    next_spawn = schedule_next_spawn()
            
            # Update objecten using custom class method
            for item in falling_items[:]:
                item.Update()
                if item.is_off_screen():
                    falling_items.remove(item)
            
            # Collisions using custom class method
            for item in falling_items[:]:
                if player.collides_with(item):
                    if item.type == 'trash':
                        falling_items.remove(item)
                        score += 1
                    else:
                        game_over = True
                        # Update stats
                        game_data['total_trash'] += score
                        if score > game_data['high_score']:
                            game_data['high_score'] = score
                        save_game_data(game_data)
                        break
        
        # Tekenen
        draw_background(screen, clouds)
        
        # Draw falling items using custom draw methods
        for item in falling_items:
            if item.type == 'trash':
                item.DrawTrash(screen)
            else:
                item.DrawObstacle(screen)
        
        # Draw printer and player
        if printer.active:
            printer.draw(screen, player)
        else:
            player.DrawBurger(screen)
        
        # UI
        render_text(screen, f"Score: {score}", font, (15, 15), TEXT_COLOR, TEXT_SHADOW)
        render_text(screen, f"Hoogste: {game_data['high_score']}", font, (15, 45), TEXT_COLOR, TEXT_SHADOW)
        
        if not game_over:
            render_text(screen, "OVERLEEF ZO LANG MOGELIJK!", font, (15, WINDOW_HEIGHT - 60), TEXT_COLOR, TEXT_SHADOW)
            render_text(screen, "WASD/Pijltjes = bewegen, Spatie = springen", font, (15, WINDOW_HEIGHT - 30), TEXT_COLOR, TEXT_SHADOW)
        else:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            msg1 = f"GAME OVER! Score: {score}"
            msg2 = f"Afval verdiend: +{score}"
            msg3 = "Druk ESC voor menu"
            
            y_center = WINDOW_HEIGHT // 2
            surf1 = big_font.render(msg1, True, (255, 80, 80))
            surf2 = font.render(msg2, True, (80, 255, 80))
            surf3 = font.render(msg3, True, TEXT_COLOR)
            
            screen.blit(surf1, surf1.get_rect(center=(WINDOW_WIDTH//2, y_center - 40)))
            screen.blit(surf2, surf2.get_rect(center=(WINDOW_WIDTH//2, y_center + 20)))
            screen.blit(surf3, surf3.get_rect(center=(WINDOW_WIDTH//2, y_center + 60)))
        
        pygame.display.flip()

# Initialize game data
game_data = load_game_data()

#setup music
pygame.mixer.init()
MUSIC_FILE = "Patty Daddies.mp3"

# Start muziek alleen als geluid aan staat
if game_data.get("sound_enabled", True):
    try:
        pygame.mixer.music.load(MUSIC_FILE)
        pygame.mixer.music.play(-1)
    except:
        print("Muziekbestand niet gevonden of kan niet geladen worden")

# Main game loop
while running:
    # cap the framerate at 60 fps
    clock.tick(FPS)

    # handle global events (quit, esc, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            current_state = "quit"

    # state machine
    if current_state == "menu":
        current_state = show_start_menu(SCREEN, FONT, big_font, game_data)
    elif current_state == "shop":
        current_state = show_shop(SCREEN, FONT, big_font, game_data)
    elif current_state == "play":
        result, score = play_game(SCREEN, FONT, big_font, game_data)
        current_state = result
    # Als een state "quit" retourneert, sluit het spel
    if current_state == "quit":
        running = False
        pygame.quit()
        exit()