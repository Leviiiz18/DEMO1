import pygame
import json
import threading
import time
import math
import random
from websocket import WebSocketApp
from datetime import datetime

# ============================================================================
# CONFIG
# ============================================================================
WIDTH, HEIGHT = 1280, 800
FPS = 60

WS_MONITOR = "ws://127.0.0.1:8000/ws/monitor"
WS_AUTH = "ws://127.0.0.1:8000/ws/authority"
WS_CIV = "ws://127.0.0.1:8000/ws/civilian"

# ============================================================================
# COLORS - Premium Dark Theme
# ============================================================================
BG_DARK = (8, 10, 18)
BG_DARKER = (12, 14, 22)
CARD_BG = (18, 22, 33)
CARD_HOVER = (22, 28, 42)

# Accent colors
CYAN = (0, 229, 255)
CYAN_DIM = (0, 180, 220)
RED = (255, 50, 85)
RED_DIM = (200, 40, 70)
YELLOW = (255, 193, 7)
GREEN = (46, 213, 115)
ORANGE = (255, 121, 63)
PURPLE = (138, 43, 226)

# Text colors
TEXT_WHITE = (255, 255, 255)
TEXT_LIGHT = (220, 225, 235)
TEXT_GRAY = (140, 150, 170)
TEXT_DIM = (90, 100, 120)

# ============================================================================
# STATE
# ============================================================================
monitor = None
auth_alert = None
civ_alert = None
last_update = None
connection_status = {"monitor": False, "auth": False, "civ": False}

# Animation states
particles = []
scan_lines = []
alert_flash_time = 0
card_animations = {}

# ============================================================================
# PYGAME INIT
# ============================================================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DISASTER MONITORING SYSTEM • LIVE")
clock = pygame.time.Clock()

# Load custom fonts - fallback to system if not available
try:
    font_title = pygame.font.Font(None, 52)
    font_heading = pygame.font.Font(None, 36)
    font_subhead = pygame.font.Font(None, 28)
    font_body = pygame.font.Font(None, 22)
    font_small = pygame.font.Font(None, 18)
    font_tiny = pygame.font.Font(None, 14)
except:
    font_title = pygame.font.SysFont('arial', 48, bold=True)
    font_heading = pygame.font.SysFont('arial', 32, bold=True)
    font_subhead = pygame.font.SysFont('arial', 24, bold=True)
    font_body = pygame.font.SysFont('arial', 20)
    font_small = pygame.font.SysFont('arial', 16)
    font_tiny = pygame.font.SysFont('arial', 12)

# ============================================================================
# PARTICLE SYSTEM
# ============================================================================
class Particle:
    def __init__(self):
        self.pos = pygame.Vector2(random.random() * WIDTH, random.random() * HEIGHT)
        self.vel = pygame.Vector2((random.random() - 0.5) * 0.3, (random.random() - 0.5) * 0.3)
        self.size = random.uniform(1, 2.5)
        self.alpha = random.randint(80, 180)
        self.base_alpha = self.alpha
    
    def update(self):
        self.pos += self.vel
        
        # Wrap around screen
        if self.pos.x < 0: self.pos.x = WIDTH
        if self.pos.x > WIDTH: self.pos.x = 0
        if self.pos.y < 0: self.pos.y = HEIGHT
        if self.pos.y > HEIGHT: self.pos.y = 0
        
        # Subtle pulse
        self.alpha = self.base_alpha + math.sin(time.time() * 2 + self.pos.x) * 30
    
    def draw(self, surf):
        color = (*CYAN, int(max(0, min(255, self.alpha))))
        pygame.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), self.size)

# Initialize particles
for _ in range(100):
    particles.append(Particle())

# ============================================================================
# SCAN LINE EFFECTS
# ============================================================================
class ScanLine:
    def __init__(self, y):
        self.y = y
        self.speed = random.uniform(0.3, 0.8)
        self.alpha = random.randint(10, 30)
    
    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = -10
    
    def draw(self, surf):
        color = (*CYAN, self.alpha)
        pygame.draw.line(surf, color, (0, int(self.y)), (WIDTH, int(self.y)), 1)

# Initialize scan lines
for _ in range(5):
    scan_lines.append(ScanLine(random.randint(0, HEIGHT)))

# ============================================================================
# WEBSOCKET HANDLERS
# ============================================================================
def on_monitor(ws, msg):
    global monitor, last_update
    monitor = json.loads(msg)
    last_update = time.time()
    connection_status["monitor"] = True

def on_auth(ws, msg):
    global auth_alert, alert_flash_time
    auth_alert = json.loads(msg)
    connection_status["auth"] = True
    alert_flash_time = time.time()

def on_civ(ws, msg):
    global civ_alert
    civ_alert = json.loads(msg)
    connection_status["civ"] = True

def start_ws(url, handler, conn_key):
    def run():
        while True:
            try:
                ws = WebSocketApp(url, on_message=handler)
                ws.run_forever()
            except:
                connection_status[conn_key] = False
                time.sleep(2)
    threading.Thread(target=run, daemon=True).start()

start_ws(WS_MONITOR, on_monitor, "monitor")
start_ws(WS_AUTH, on_auth, "auth")
start_ws(WS_CIV, on_civ, "civ")

# ============================================================================
# DRAWING UTILITIES
# ============================================================================
def ease_out_cubic(t):
    """Smooth easing function"""
    return 1 - pow(1 - t, 3)

def draw_glow(surf, pos, radius, color, intensity=0.5):
    """Draw a glowing circle with gradient falloff"""
    glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    for i in range(5):
        r = radius + i * (radius // 2)
        a = int(intensity * 255 / (i + 1))
        pygame.draw.circle(glow_surf, (*color, a), (radius * 2, radius * 2), r)
    pygame.draw.circle(glow_surf, color, (radius * 2, radius * 2), radius)
    surf.blit(glow_surf, (pos[0] - radius * 2, pos[1] - radius * 2))

def draw_text_with_shadow(surf, text, pos, font, color, shadow_offset=2):
    """Draw text with subtle shadow"""
    # Shadow
    shadow_surf = font.render(text, True, (0, 0, 0))
    shadow_surf.set_alpha(100)
    surf.blit(shadow_surf, (pos[0] + shadow_offset, pos[1] + shadow_offset))
    # Text
    text_surf = font.render(text, True, color)
    surf.blit(text_surf, pos)
    return text_surf.get_size()

def draw_rounded_rect(surf, rect, color, radius=12, border=0, border_color=None):
    """Draw a rounded rectangle with optional border"""
    if border > 0 and border_color:
        pygame.draw.rect(surf, border_color, rect, border_radius=radius)
        inner_rect = pygame.Rect(rect.x + border, rect.y + border, 
                                 rect.width - border * 2, rect.height - border * 2)
        pygame.draw.rect(surf, color, inner_rect, border_radius=radius - border)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_card(surf, rect, title=None, glow_color=None):
    """Draw a premium card with optional glow"""
    # Glow effect
    if glow_color:
        glow_rect = pygame.Rect(rect.x - 2, rect.y - 2, rect.width + 4, rect.height + 4)
        glow_surf = pygame.Surface((rect.width + 4, rect.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*glow_color, 30), glow_surf.get_rect(), border_radius=14)
        surf.blit(glow_surf, (rect.x - 2, rect.y - 2))
    
    # Card background
    draw_rounded_rect(surf, rect, CARD_BG, radius=12, border=1, border_color=(*CYAN, 40))
    
    # Subtle gradient overlay
    gradient_surf = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
    for i in range(rect.height // 2):
        alpha = int(20 * (1 - i / (rect.height // 2)))
        pygame.draw.line(gradient_surf, (*TEXT_WHITE, alpha), (0, i), (rect.width, i))
    surf.blit(gradient_surf, (rect.x, rect.y))
    
    # Title bar
    if title:
        title_rect = pygame.Rect(rect.x, rect.y, rect.width, 50)
        pygame.draw.line(surf, (*CYAN, 60), (rect.x + 20, rect.y + 50), 
                        (rect.x + rect.width - 20, rect.y + 50), 1)
        draw_text_with_shadow(surf, title, (rect.x + 20, rect.y + 14), font_subhead, CYAN)

def draw_badge(surf, pos, text, badge_type="default"):
    """Draw a status badge"""
    colors = {
        "default": CYAN,
        "success": GREEN,
        "warning": YELLOW,
        "danger": RED,
        "info": PURPLE
    }
    color = colors.get(badge_type, CYAN)
    
    # Measure text
    text_surf = font_small.render(text, True, TEXT_WHITE)
    padding = (12, 6)
    badge_rect = pygame.Rect(pos[0], pos[1], text_surf.get_width() + padding[0] * 2, 
                             text_surf.get_height() + padding[1] * 2)
    
    # Background with glow
    glow_surf = pygame.Surface((badge_rect.width + 4, badge_rect.height + 4), pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, (*color, 60), glow_surf.get_rect(), border_radius=6)
    surf.blit(glow_surf, (badge_rect.x - 2, badge_rect.y - 2))
    
    pygame.draw.rect(surf, (*color, 40), badge_rect, border_radius=6)
    pygame.draw.rect(surf, color, badge_rect, 1, border_radius=6)
    
    # Text
    surf.blit(text_surf, (pos[0] + padding[0], pos[1] + padding[1]))
    
    return badge_rect.width + 10

def draw_progress_bar(surf, rect, progress, color, bg_color=(30, 35, 45)):
    """Draw an animated progress bar"""
    # Background
    pygame.draw.rect(surf, bg_color, rect, border_radius=8)
    
    # Progress fill
    if progress > 0:
        fill_width = int(rect.width * progress)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        
        # Gradient fill
        for x in range(fill_width):
            gradient_progress = x / fill_width
            r = int(color[0] * (0.6 + 0.4 * gradient_progress))
            g = int(color[1] * (0.6 + 0.4 * gradient_progress))
            b = int(color[2] * (0.6 + 0.4 * gradient_progress))
            pygame.draw.line(surf, (r, g, b), (rect.x + x, rect.y), 
                           (rect.x + x, rect.y + rect.height))
        
        # Shimmer effect
        shimmer_pos = (time.time() * 200) % (fill_width + 100)
        if shimmer_pos < fill_width:
            shimmer_alpha = 100
            pygame.draw.line(surf, (*TEXT_WHITE, shimmer_alpha), 
                           (rect.x + int(shimmer_pos), rect.y), 
                           (rect.x + int(shimmer_pos), rect.y + rect.height), 2)
    
    # Border
    pygame.draw.rect(surf, (*color, 100), rect, 2, border_radius=8)

def draw_metric_card(surf, pos, label, value, icon_color=CYAN, width=220, height=100):
    """Draw a metric display card"""
    rect = pygame.Rect(pos[0], pos[1], width, height)
    
    # Hover effect
    mouse_pos = pygame.mouse.get_pos()
    is_hover = rect.collidepoint(mouse_pos)
    
    # Background
    bg_color = CARD_HOVER if is_hover else CARD_BG
    draw_rounded_rect(surf, rect, bg_color, radius=10, border=1, 
                     border_color=(*icon_color, 80 if is_hover else 40))
    
    # Accent line
    pygame.draw.rect(surf, icon_color, (rect.x, rect.y, 4, rect.height), 
                    border_top_left_radius=10, border_bottom_left_radius=10)
    
    # Label
    draw_text_with_shadow(surf, label, (rect.x + 20, rect.y + 15), 
                         font_tiny, TEXT_GRAY, shadow_offset=1)
    
    # Value
    draw_text_with_shadow(surf, str(value), (rect.x + 20, rect.y + 40), 
                         font_heading, icon_color)

def draw_status_indicator(surf, pos, is_active, label):
    """Draw connection status indicator"""
    # Pulsing animation
    pulse = abs(math.sin(time.time() * 3)) if is_active else 0
    color = GREEN if is_active else RED
    
    # Glow
    glow_size = 8 + int(pulse * 4)
    draw_glow(surf, pos, glow_size, color, intensity=0.3 + pulse * 0.2)
    
    # Label
    draw_text_with_shadow(surf, label, (pos[0] + 20, pos[1] - 7), 
                         font_small, TEXT_LIGHT if is_active else TEXT_DIM)

def draw_wave_marker(surf, pos, color=RED, size=20):
    """Draw animated wave/ping marker"""
    t = time.time() * 2
    
    # Multiple expanding circles
    for i in range(3):
        phase = (t + i * 0.3) % 2
        if phase < 1:
            radius = int(size + phase * size * 2)
            alpha = int(180 * (1 - phase))
            circle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (*color, alpha), (radius, radius), radius, 2)
            surf.blit(circle_surf, (pos[0] - radius, pos[1] - radius))
    
    # Center dot
    draw_glow(surf, pos, 8, color, intensity=0.6)

def draw_spinner(surf, pos, radius=30, color=CYAN):
    """Draw animated loading spinner"""
    t = time.time() * 4
    
    # Outer ring
    pygame.draw.circle(surf, (*color, 30), pos, radius, 3)
    
    # Animated arc
    for i in range(20):
        angle = math.radians((t * 60 + i * 18) % 360)
        alpha = int(255 * (i / 20))
        end_x = pos[0] + int(math.cos(angle) * radius)
        end_y = pos[1] + int(math.sin(angle) * radius)
        pygame.draw.circle(surf, (*color, alpha), (end_x, end_y), 3)

# ============================================================================
# RENDER PANELS
# ============================================================================
def render_header():
    """Render top header bar"""
    header_rect = pygame.Rect(15, 15, WIDTH - 30, 70)
    draw_card(screen, header_rect)
    
    # Logo/Title with glow
    title_pos = (header_rect.x + 25, header_rect.y + 15)
    draw_glow(screen, (title_pos[0] + 140, title_pos[1] + 20), 40, CYAN, intensity=0.2)
    draw_text_with_shadow(screen, "DISASTER MONITORING", title_pos, 
                         font_title, CYAN, shadow_offset=3)
    
    # Live indicator
    live_x = title_pos[0] + 480
    if int(time.time() * 2) % 2:
        pygame.draw.circle(screen, RED, (live_x, title_pos[1] + 20), 6)
    draw_text_with_shadow(screen, "LIVE", (live_x + 15, title_pos[1] + 10), 
                         font_body, RED)
    
    # Timestamp
    timestamp = datetime.now().strftime("%H:%M:%S • %d %b %Y")
    draw_text_with_shadow(screen, timestamp, (header_rect.x + header_rect.width - 240, 
                         title_pos[1] + 12), font_body, TEXT_GRAY)
    
    # Connection status
    status_y = header_rect.y + 50
    status_x = header_rect.x + header_rect.width - 380
    for i, (name, active) in enumerate(connection_status.items()):
        draw_status_indicator(screen, (status_x + i * 115, status_y), active, name.upper())

def render_main_monitor():
    """Render main monitoring panel"""
    panel_rect = pygame.Rect(15, 100, 770, HEIGHT - 115)
    
    # Check for critical alert flash
    is_critical = monitor and monitor.get('severity') in ['HIGH', 'CRITICAL']
    glow = RED if (is_critical and int(time.time() * 3) % 2) else None
    
    draw_card(screen, panel_rect, "LIVE MONITORING", glow_color=glow)
    
    content_y = panel_rect.y + 65
    
    if monitor:
        # Disaster type - BIG and prominent
        disaster = monitor.get('disaster_type', 'UNKNOWN').upper()
        disaster_pos = (panel_rect.x + 25, content_y)
        
        # Glowing disaster type
        draw_glow(screen, (disaster_pos[0] + 150, disaster_pos[1] + 25), 40, RED, intensity=0.3)
        draw_text_with_shadow(screen, disaster, disaster_pos, font_title, RED, shadow_offset=3)
        
        content_y += 70
        
        # Severity bar
        severity = monitor.get('severity', 'Unknown')
        severity_map = {
            'LOW': (0.25, GREEN),
            'MODERATE': (0.5, YELLOW),
            'HIGH': (0.75, ORANGE),
            'CRITICAL': (1.0, RED)
        }
        progress, sev_color = severity_map.get(severity, (0.5, YELLOW))
        
        draw_text_with_shadow(screen, "THREAT LEVEL", (panel_rect.x + 25, content_y), 
                             font_small, TEXT_GRAY)
        content_y += 25
        
        bar_rect = pygame.Rect(panel_rect.x + 25, content_y, panel_rect.width - 50, 35)
        draw_progress_bar(screen, bar_rect, progress, sev_color)
        
        # Severity label on bar
        draw_text_with_shadow(screen, severity.upper(), 
                             (bar_rect.x + bar_rect.width - 120, bar_rect.y + 6), 
                             font_body, TEXT_WHITE)
        
        content_y += 60
        
        # Map visualization area
        map_rect = pygame.Rect(panel_rect.x + 25, content_y, panel_rect.width - 50, 160)
        pygame.draw.rect(screen, BG_DARKER, map_rect, border_radius=10)
        pygame.draw.rect(screen, (*CYAN, 30), map_rect, 2, border_radius=10)
        
        # Grid overlay on map
        grid_color = (*CYAN, 10)
        for i in range(0, map_rect.width, 40):
            pygame.draw.line(screen, grid_color, 
                           (map_rect.x + i, map_rect.y), 
                           (map_rect.x + i, map_rect.y + map_rect.height))
        for i in range(0, map_rect.height, 40):
            pygame.draw.line(screen, grid_color, 
                           (map_rect.x, map_rect.y + i), 
                           (map_rect.x + map_rect.width, map_rect.y + i))
        
        # Animated marker
        marker_pos = (map_rect.centerx, map_rect.centery)
        draw_wave_marker(screen, marker_pos, RED, 15)
        
        # Coordinates on map
        lat = monitor.get('latitude', 0)
        lon = monitor.get('longitude', 0)
        coord_text = f"LAT: {lat:.4f}  LON: {lon:.4f}"
        draw_text_with_shadow(screen, coord_text, 
                             (map_rect.x + 12, map_rect.y + map_rect.height - 25), 
                             font_small, CYAN)
        
        content_y += 180
        
        # Metrics grid
        metrics = [
            ("LATITUDE", f"{lat:.4f}", CYAN),
            ("LONGITUDE", f"{lon:.4f}", CYAN),
            ("DENSITY", f"{monitor.get('density', 0):.1f}", PURPLE),
            ("STATUS", monitor.get('status', 'N/A'), GREEN)
        ]
        
        metric_width = (panel_rect.width - 65) // 2
        for i, (label, value, color) in enumerate(metrics):
            col = i % 2
            row = i // 2
            x = panel_rect.x + 25 + col * (metric_width + 15)
            y = content_y + row * 95
            draw_metric_card(screen, (x, y), label, value, color, 
                           width=metric_width, height=80)
        
        content_y += 200
        
        # Affected states
        states = monitor.get('affected_states', [])
        if states:
            draw_text_with_shadow(screen, "AFFECTED REGIONS", 
                                 (panel_rect.x + 25, content_y), 
                                 font_small, TEXT_GRAY)
            content_y += 30
            
            chip_x = panel_rect.x + 25
            chip_y = content_y
            for state in states:
                badge_width = draw_badge(screen, (chip_x, chip_y), state, "warning")
                chip_x += badge_width
                if chip_x + 100 > panel_rect.x + panel_rect.width - 25:
                    chip_x = panel_rect.x + 25
                    chip_y += 38
        
        # Last update
        if last_update:
            elapsed = int(time.time() - last_update)
            update_text = f"Updated {elapsed}s ago"
            draw_text_with_shadow(screen, update_text, 
                                 (panel_rect.x + 25, panel_rect.y + panel_rect.height - 30), 
                                 font_tiny, TEXT_DIM)
    else:
        # Loading state
        center = panel_rect.center
        draw_spinner(screen, center, 35, CYAN)
        draw_text_with_shadow(screen, "ESTABLISHING CONNECTION", 
                             (center[0] - 130, center[1] + 60), 
                             font_body, TEXT_GRAY)

def render_authority_alert():
    """Render authority alert panel"""
    panel_rect = pygame.Rect(800, 100, WIDTH - 815, 340)
    
    is_critical = auth_alert and auth_alert.get('severity') in ['HIGH', 'CRITICAL']
    glow = ORANGE if (is_critical and int(time.time() * 3) % 2) else None
    
    draw_card(screen, panel_rect, "AUTHORITY ALERT", glow_color=glow)
    
    if auth_alert:
        content_y = panel_rect.y + 65
        
        # Status badge
        draw_badge(screen, (panel_rect.x + panel_rect.width - 95, panel_rect.y + 10), 
                  "ACTIVE", "danger")
        
        # ETA - large and prominent
        eta = auth_alert.get('eta_hours', 'N/A')
        eta_text = f"{eta}"
        draw_text_with_shadow(screen, eta_text, (panel_rect.x + 25, content_y), 
                             font_heading, ORANGE, shadow_offset=2)
        draw_text_with_shadow(screen, "HOURS ETA", (panel_rect.x + 120, content_y + 28), 
                             font_small, TEXT_GRAY)
        
        content_y += 70
        
        # Severity metric
        severity = auth_alert.get('severity', 'N/A')
        draw_metric_card(screen, (panel_rect.x + 25, content_y), 
                        "SEVERITY", severity, RED, 
                        width=panel_rect.width - 50, height=65)
        
        content_y += 80
        
        # Recommended forces section
        forces = auth_alert.get('recommended_forces', [])
        if forces:
            draw_text_with_shadow(screen, "DEPLOY FORCES", 
                                 (panel_rect.x + 25, content_y), 
                                 font_small, TEXT_GRAY)
            content_y += 25
            
            # Draw forces as badges
            chip_x = panel_rect.x + 25
            chip_y = content_y
            for force in forces[:5]:  # Limit to 5 forces
                badge_width = draw_badge(screen, (chip_x, chip_y), force, "success")
                chip_y += 35
        else:
            # Affected areas if no forces
            states = auth_alert.get('affected_states', [])
            if states:
                draw_text_with_shadow(screen, "AFFECTED AREAS", 
                                     (panel_rect.x + 25, content_y), 
                                     font_small, TEXT_GRAY)
                content_y += 25
                
                chip_x = panel_rect.x + 25
                chip_y = content_y
                for state in states[:3]:
                    badge_width = draw_badge(screen, (chip_x, chip_y), state, "warning")
                    chip_x += badge_width
                    if chip_x + 90 > panel_rect.x + panel_rect.width - 25:
                        chip_x = panel_rect.x + 25
                        chip_y += 35
    else:
        center_y = panel_rect.y + panel_rect.height // 2
        draw_text_with_shadow(screen, "NO ACTIVE ALERTS", 
                             (panel_rect.x + panel_rect.width // 2 - 85, center_y), 
                             font_body, TEXT_DIM)

def render_civilian_alert():
    """Render civilian alert panel"""
    panel_rect = pygame.Rect(800, 455, WIDTH - 815, HEIGHT - 470)
    draw_card(screen, panel_rect, "CIVILIAN ALERT")
    
    if civ_alert:
        content_y = panel_rect.y + 65
        
        # Status badge
        draw_badge(screen, (panel_rect.x + panel_rect.width - 95, panel_rect.y + 10), 
                  "ACTIVE", "warning")
        
        # Message box
        message = civ_alert.get('message', 'No message')
        msg_rect = pygame.Rect(panel_rect.x + 25, content_y, 
                              panel_rect.width - 50, 110)
        
        pygame.draw.rect(screen, (*YELLOW, 20), msg_rect, border_radius=8)
        pygame.draw.rect(screen, YELLOW, (msg_rect.x, msg_rect.y, 4, msg_rect.height), 
                        border_top_left_radius=8, border_bottom_left_radius=8)
        
        # Word wrap message
        words = message.split()
        lines = []
        current_line = []
        max_width = msg_rect.width - 35
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font_body.size(test_line)[0] > max_width:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw lines
        for i, line in enumerate(lines[:3]):
            draw_text_with_shadow(screen, line, 
                                 (msg_rect.x + 18, msg_rect.y + 18 + i * 28), 
                                 font_body, TEXT_LIGHT)
        
        content_y += 125
        
        # Severity and ETA metrics
        severity = civ_alert.get('severity', 'N/A')
        eta = civ_alert.get('eta', 'N/A')
        
        # Two smaller metric cards side by side
        draw_metric_card(screen, (panel_rect.x + 25, content_y), 
                        "SEVERITY", severity, YELLOW, 
                        width=(panel_rect.width - 60) // 2, height=65)
        
        draw_metric_card(screen, (panel_rect.x + 35 + (panel_rect.width - 60) // 2, content_y), 
                        "ETA", eta, ORANGE, 
                        width=(panel_rect.width - 60) // 2, height=65)
    else:
        center_y = panel_rect.y + panel_rect.height // 2
        draw_text_with_shadow(screen, "NO ACTIVE ALERTS", 
                             (panel_rect.x + panel_rect.width // 2 - 85, center_y), 
                             font_body, TEXT_DIM)

# ============================================================================
# MAIN LOOP
# ============================================================================
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Clear screen
    screen.fill(BG_DARK)
    
    # Draw background effects
    for particle in particles:
        particle.update()
        particle.draw(screen)
    
    # Draw connections between nearby particles
    for i, p1 in enumerate(particles):
        for p2 in particles[i+1:i+6]:  # Limit connections for performance
            dist = p1.pos.distance_to(p2.pos)
            if dist < 120:
                alpha = int(30 * (1 - dist / 120))
                pygame.draw.line(screen, (*CYAN, alpha), 
                               (int(p1.pos.x), int(p1.pos.y)), 
                               (int(p2.pos.x), int(p2.pos.y)), 1)
    
    # Scan lines
    for scan in scan_lines:
        scan.update()
        scan.draw(screen)
    
    # Render UI
    render_header()
    render_main_monitor()
    render_authority_alert()
    render_civilian_alert()
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()