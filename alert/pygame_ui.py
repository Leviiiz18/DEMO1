import pygame
import json
import threading
from websocket import WebSocketApp

WIDTH, HEIGHT = 900, 550
WS_AUTH = "ws://127.0.0.1:8000/ws/authority"
WS_CIV = "ws://127.0.0.1:8000/ws/civilian"

auth_alert = None
civ_alert = None
status = "Waiting for data source..."

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disaster Alert Module – Simulation UI")
font = pygame.font.SysFont("consolas", 16)
clock = pygame.time.Clock()

def auth_msg(ws, msg):
    global auth_alert, status
    auth_alert = json.loads(msg)
    status = "Authority alert issued"

def civ_msg(ws, msg):
    global civ_alert, status
    civ_alert = json.loads(msg)
    status = "Civilian alert issued"

def start_ws(url, handler):
    ws = WebSocketApp(url, on_message=handler)
    ws.run_forever()

threading.Thread(target=start_ws, args=(WS_AUTH, auth_msg), daemon=True).start()
threading.Thread(target=start_ws, args=(WS_CIV, civ_msg), daemon=True).start()

def draw(t, x, y, c=(220,220,220)):
    screen.blit(font.render(t, True, c), (x, y))

running = True
while running:
    screen.fill((12, 16, 30))
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    draw("DISASTER ALERT MODULE (PLUG-IN READY)", 20, 20, (80,200,255))
    draw(f"STATUS: {status}", 20, 50, (150,255,150))

    if auth_alert:
        draw("AUTHORITY ALERT", 20, 100, (255,100,100))
        draw(f"Location: {auth_alert['location']}", 20, 130)
        draw(f"ETA: {auth_alert['eta_hours']} hrs", 20, 160)
        draw("States: " + ", ".join(auth_alert["predicted_impact_states"]), 20, 190)

    if civ_alert:
        draw("CIVILIAN ALERT", 20, 240, (255,200,80))
        draw(civ_alert["message"], 20, 270)
        draw("Risk: " + civ_alert["risk_level"], 20, 300)

    if not auth_alert and not civ_alert:
        draw("Listening on /ingest → /ws/*", 20, 120)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
