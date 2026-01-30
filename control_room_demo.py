import pygame
import threading
import time
# IMPORT ML-DRIVEN EVENT STREAM
from event_stream_with_models import run_scenario_with_models, EVENT_STREAM

# -------------------------------------------------
# PYGAME INIT
# -------------------------------------------------
pygame.init()
WIDTH, HEIGHT = 1150, 680
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disaster Monitoring Control Room (ML Live)")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("arial", 40, bold=True)
font_subtitle = pygame.font.SysFont("arial", 18)
font = pygame.font.SysFont("arial", 20)
font_small = pygame.font.SysFont("arial", 16)
font_tiny = pygame.font.SysFont("arial", 14)

# -------------------------------------------------
# COLORS
# -------------------------------------------------
BG = (10, 14, 25)
PANEL = (25, 30, 42)
PANEL_BORDER = (45, 52, 70)
HEADER_BG = (18, 22, 35)
WHITE = (240, 242, 248)
BLUE = (80, 150, 255)     # info
GREEN = (100, 210, 140)   # low
ORANGE = (255, 165, 0)    # medium
RED = (220, 20, 60)       # high
PURPLE = (150, 100, 255)  # ML accent
CYAN = (0, 220, 220)      # tech accent

SEVERITY_COLOR = {
    "info": BLUE,
    "low": GREEN,
    "medium": ORANGE,
    "high": RED
}

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def draw_rounded_rect(surface, color, rect, radius=10, border_color=None, border_width=0):
    """Draw a rounded rectangle with optional border"""
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x + radius, y, w - 2*radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2*radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)
    
    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)

def draw_ml_alert_card(surface, event, x, y, width, index):
    """Draw a styled ML alert card with animations"""
    color = SEVERITY_COLOR.get(event["severity"], WHITE)
    
    # Card background with subtle animation
    card_height = 70
    time_offset = (pygame.time.get_ticks() + index * 100) // 20
    pulse = abs((time_offset % 100) - 50) / 50.0
    bg_brightness = 25 + int(pulse * 5)
    card_bg = (bg_brightness, bg_brightness + 5, bg_brightness + 10)
    
    draw_rounded_rect(surface, card_bg, (x, y, width, card_height), 8, PANEL_BORDER, 1)
    
    # Severity indicator stripe
    pygame.draw.rect(surface, color, (x, y, 4, card_height), 
                    border_top_left_radius=8, border_bottom_left_radius=8)
    
    # Event type badge with glow
    badge_text = font_tiny.render(event['type'].upper(), True, WHITE)
    badge_width = badge_text.get_width() + 16
    badge_rect = (x + 12, y + 8, badge_width, 20)
    
    # Glow effect
    glow_surface = pygame.Surface((badge_width + 10, 30), pygame.SRCALPHA)
    pygame.draw.rect(glow_surface, (*color, 30), (0, 5, badge_width + 10, 30), border_radius=6)
    surface.blit(glow_surface, (x + 7, y + 3))
    
    draw_rounded_rect(surface, color, badge_rect, 4)
    surface.blit(badge_text, (x + 20, y + 11))
    
    # Severity level indicator
    severity_text = font_tiny.render(event['severity'].upper(), True, color)
    surface.blit(severity_text, (x + badge_width + 20, y + 11))
    
    # Message with word wrap
    message = event['message']
    max_width = width - 25
    words = message.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + word + " "
        if font_small.render(test_line, True, WHITE).get_width() < max_width - 20:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word + " "
    if current_line:
        lines.append(current_line)
    
    # Draw message lines
    msg_y = y + 35
    for line in lines[:2]:  # Max 2 lines
        rendered = font_small.render(line.strip(), True, (220, 220, 230))
        surface.blit(rendered, (x + 12, msg_y))
        msg_y += 18

def draw_animated_marker(surface, x, y, color, size, shape="circle"):
    """Draw animated markers with pulse effect"""
    t = pygame.time.get_ticks()
    pulse = (t // 10) % 80
    pulse_alpha = max(0, 120 - pulse * 2)
    
    # Outer pulse rings
    for i in range(3):
        ring_size = size + pulse + (i * 15)
        ring_alpha = max(0, pulse_alpha - (i * 40))
        s = pygame.Surface((int(ring_size * 3), int(ring_size * 3)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, ring_alpha), 
                          (int(ring_size * 1.5), int(ring_size * 1.5)), 
                          int(ring_size))
        surface.blit(s, (x - ring_size * 1.5, y - ring_size * 1.5))
    
    # Main marker
    if shape == "circle":
        pygame.draw.circle(surface, color, (x, y), size)
        pygame.draw.circle(surface, WHITE, (x, y), size, 2)
        pygame.draw.circle(surface, color, (x, y), size // 2)
    elif shape == "triangle":
        points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)
    elif shape == "square":
        pygame.draw.rect(surface, color, (x - size, y - size, size * 2, size * 2))
        pygame.draw.rect(surface, WHITE, (x - size, y - size, size * 2, size * 2), 2)

def draw_ml_badge(surface, x, y):
    """Draw animated ML processing badge"""
    t = pygame.time.get_ticks()
    pulse = abs((t // 20) % 100 - 50) / 50.0
    
    # Background
    badge_width = 160
    badge_height = 28
    draw_rounded_rect(surface, HEADER_BG, (x, y, badge_width, badge_height), 6, PURPLE, 2)
    
    # Animated processing dots
    dot_y = y + badge_height // 2
    for i in range(3):
        dot_phase = (t // 200 + i * 333) % 1000 / 1000.0
        dot_alpha = int(100 + 155 * abs(dot_phase - 0.5) * 2)
        pygame.draw.circle(surface, (*PURPLE, dot_alpha), (x + 12 + i * 10, dot_y), 3)
    
    # Text
    ml_text = font_tiny.render("ML PROCESSING", True, PURPLE)
    surface.blit(ml_text, (x + 42, y + 7))

def draw_data_stream_effect(surface, x, y, width, height):
    """Draw animated data stream in background"""
    t = pygame.time.get_ticks()
    for i in range(15):
        offset = (t // 5 + i * 50) % height
        alpha = int(30 * (1 - offset / height))
        line_length = 20 + (i % 5) * 10
        pygame.draw.line(surface, (*CYAN, alpha), 
                        (x + (i * width // 15), y + offset), 
                        (x + (i * width // 15), y + offset - line_length), 2)

# -------------------------------------------------
# RUN ML SIMULATION IN BACKGROUND
# -------------------------------------------------
def start_ml_simulation():
    run_scenario_with_models()

sim_thread = threading.Thread(
    target=start_ml_simulation,
    daemon=True
)
sim_thread.start()

# -------------------------------------------------
# MAIN UI LOOP
# -------------------------------------------------
running = True

while running:
    screen.fill(BG)
    
    # -----------------------------
    # HEADER WITH GRADIENT
    # -----------------------------
    header_height = 85
    for i in range(header_height):
        alpha = int(255 * (1 - i / header_height) * 0.3)
        pygame.draw.line(screen, (18 + i//4, 22 + i//4, 35 + i//3), 
                        (0, i), (WIDTH, i))
    
    draw_rounded_rect(screen, HEADER_BG, (0, 0, WIDTH, header_height), 0)
    
    # Title
    title = font_title.render("National Disaster Monitoring Center", True, WHITE)
    screen.blit(title, (40, 15))
    
    # ML Live indicator with animation
    t = pygame.time.get_ticks()
    live_pulse = (t // 500) % 2
    live_color = PURPLE if live_pulse else (100, 50, 180)
    pygame.draw.circle(screen, live_color, (40 + title.get_width() + 25, 32), 7)
    pygame.draw.circle(screen, PURPLE, (40 + title.get_width() + 25, 32), 7, 2)
    
    live_text = font_subtitle.render("ML LIVE", True, PURPLE)
    screen.blit(live_text, (40 + title.get_width() + 42, 24))
    
    # Subtitle
    subtitle = font_subtitle.render(
        "Autonomous AI-Driven Monitoring System • Real-time Analysis",
        True,
        (140, 150, 170)
    )
    screen.blit(subtitle, (40, 52))
    
    # ML Processing badge
    draw_ml_badge(screen, WIDTH - 180, 28)
    
    # Event counter
    event_count = len(EVENT_STREAM)
    counter_bg = (WIDTH - 180, 62, 160, 22)
    draw_rounded_rect(screen, PANEL, counter_bg, 4)
    counter_text = font_small.render(f"Events Processed: {event_count}", True, CYAN)
    screen.blit(counter_text, (WIDTH - 172, 65))
    
    # -----------------------------
    # MAP PANEL WITH EFFECTS
    # -----------------------------
    map_rect = (30, 105, 730, 500)
    
    # Data stream background effect
    draw_data_stream_effect(screen, 35, 110, 720, 490)
    
    draw_rounded_rect(screen, PANEL, map_rect, 12, PANEL_BORDER, 2)
    
    # Map header
    map_header_rect = (40, 110, 710, 38)
    draw_rounded_rect(screen, HEADER_BG, map_header_rect, 8)
    
    # Map icon
    pygame.draw.circle(screen, CYAN, (58, 129), 5)
    pygame.draw.circle(screen, CYAN, (58, 129), 8, 1)
    
    map_label = font.render("Geographic Overview - Indian Ocean Region", True, WHITE)
    screen.blit(map_label, (75, 119))
    
    # Grid coordinates
    coord_text = font_tiny.render("LAT: 8.5°N | LON: 76.9°E", True, (100, 110, 130))
    screen.blit(coord_text, (580, 122))
    
    # Enhanced grid system
    grid_color = (35, 42, 55)
    for i in range(8):
        x_pos = 50 + i * 90
        pygame.draw.line(screen, grid_color, (x_pos, 160), (x_pos, 590), 1)
    for i in range(6):
        y_pos = 160 + i * 72
        pygame.draw.line(screen, grid_color, (50, y_pos), (740, y_pos), 1)
    
    # Center reference point
    center_x, center_y = 410, 370
    pygame.draw.circle(screen, (70, 80, 100), (center_x, center_y), 4)
    pygame.draw.circle(screen, CYAN, (center_x, center_y), 8, 1)
    
    # Region label
    region_text = font_small.render("MONITORING ZONE", True, (80, 90, 110))
    screen.blit(region_text, (center_x - 70, center_y + 15))
    
    # -----------------------------
    # ALERT PANEL
    # -----------------------------
    alert_rect = (780, 105, 340, 500)
    draw_rounded_rect(screen, PANEL, alert_rect, 12, PANEL_BORDER, 2)
    
    # Alert header
    alert_header_rect = (790, 110, 320, 38)
    draw_rounded_rect(screen, HEADER_BG, alert_header_rect, 8)
    
    # Alert icon
    pygame.draw.rect(screen, RED, (808, 123, 12, 12), border_radius=2)
    pygame.draw.rect(screen, WHITE, (808, 123, 12, 12), 2, border_radius=2)
    
    alert_title = font.render("Live Alert Feed", True, WHITE)
    screen.blit(alert_title, (830, 119))
    
    # Active alerts count
    active_count = min(len(EVENT_STREAM), 6)
    count_bg = (1050, 115, 45, 26)
    count_color = RED if active_count > 3 else ORANGE if active_count > 0 else GREEN
    draw_rounded_rect(screen, count_color, count_bg, 6)
    count_text = font.render(str(active_count), True, WHITE)
    count_rect = count_text.get_rect(center=(1072, 128))
    screen.blit(count_text, count_rect)
    
    # -----------------------------
    # DRAW EVENT FEED
    # -----------------------------
    y_offset = 160
    last_events = EVENT_STREAM[-6:][::-1]  # Last 6, reversed
    
    if len(last_events) > 0:
        for idx, event in enumerate(last_events):
            draw_ml_alert_card(screen, event, 795, y_offset, 310, idx)
            y_offset += 78
            
            # MAP ICONS with different positions
            base_x = center_x
            base_y = center_y
            offset_x = (idx % 3 - 1) * 40
            offset_y = (idx // 3) * 40 - 40
            
            if event["type"] == "earthquake":
                draw_animated_marker(screen, base_x + offset_x, base_y + offset_y, 
                                   ORANGE, 9, "circle")
            elif event["type"] == "tsunami":
                draw_animated_marker(screen, base_x + offset_x + 20, base_y + offset_y + 30, 
                                   RED, 13, "triangle")
            elif event["type"] == "cyclone":
                draw_animated_marker(screen, base_x + offset_x - 20, base_y + offset_y - 20, 
                                   BLUE, 10, "square")
    else:
        # Empty state
        empty_y = 330
        empty_icon = font_title.render("✓", True, (60, 70, 90))
        screen.blit(empty_icon, (930, empty_y - 30))
        empty_text = font.render("All Clear", True, (100, 110, 130))
        screen.blit(empty_text, (910, empty_y + 20))
        empty_sub = font_small.render("Monitoring active", True, (70, 80, 100))
        screen.blit(empty_sub, (890, empty_y + 48))
    
    # -----------------------------
    # STATUS BAR WITH STATS
    # -----------------------------
    status_height = 45
    status_y = HEIGHT - status_height
    
    draw_rounded_rect(screen, HEADER_BG, (0, status_y, WIDTH, status_height), 0)
    
    # Status indicator
    status_active = (t // 1000) % 2
    status_color = GREEN if status_active else (60, 150, 80)
    pygame.draw.circle(screen, status_color, (30, status_y + 22), 6)
    pygame.draw.circle(screen, GREEN, (30, status_y + 22), 9, 1)
    
    status = font.render("SYSTEM OPERATIONAL", True, WHITE)
    screen.blit(status, (48, status_y + 13))
    
    # Divider
    pygame.draw.line(screen, PANEL_BORDER, (250, status_y + 10), (250, status_y + 35), 1)
    
    # ML status
    ml_icon_x = 270
    for i in range(3):
        dot_phase = (t // 150 + i * 333) % 1000 / 1000.0
        dot_brightness = int(100 + 100 * dot_phase)
        dot_color = (min(255, int(dot_brightness)), min(255, int(dot_brightness // 2)), min(255, int(dot_brightness + 100)))
        pygame.draw.circle(screen, dot_color, (ml_icon_x + i * 12, status_y + 22), 4)
    
    ml_status = font_small.render("ML Models Active • Autonomous Processing", True, PURPLE)
    screen.blit(ml_status, (ml_icon_x + 40, status_y + 14))
    
    # System time
    time_text = font_small.render(f"SYSTEM TIME: {time.strftime('%H:%M:%S')}", True, (130, 140, 160))
    screen.blit(time_text, (WIDTH - 200, status_y + 14))
    
    # -----------------------------
    # EXIT
    # -----------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()