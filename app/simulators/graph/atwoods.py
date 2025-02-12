from threading import Thread, Event
from queue import Queue, Empty
from json import dumps, loads
from websockets.sync.server import serve
import websockets
import pygame
import threading
import time
import math
import webbrowser

# WebSocket Server Setup
connected = set()
data = Queue()
b = False
all_data = []

def handler(websocket):
    connected.add(websocket)
    # Send init message
    init_message = {
        'type': 'init',
        'name': 'AtwoodMachine',
        'default_settings': {'xAxisValue': 't', 'yAxisValue': 't'}
    }
    websocket.send(dumps(init_message))
    global b
    global all_data
    if b:
        for entry in all_data:
            update_message = {
                'type': 'update',
                'values': entry
            }
            websocket.send(dumps(update_message))
    else:
        b = True

    try:
        for msg in websocket:
            data = loads(msg)
            if data['type'] == 'update_mass':
                global m1, m2
                m1 = data['mass1']
                m2 = data['mass2']
            elif data['type'] == 'update_axis':
                pass
    finally:
        connected.remove(websocket)

def start_server():
    server = serve(handler, '', 8045)
    Thread(target=server.serve_forever).start()
    return server

server = start_server()

def broadcaster():
    while True:
        for websocket in connected.copy():
            try:
                global all_data
                global b
                got = data.get_nowait()
                if b:
                    all_data.append(got)
                    update_message = {
                        'type': 'update',
                        'values': got
                    }
                    websocket.send(dumps(update_message))
                else:
                    b = True
            except Empty:
                pass
        time.sleep(.1)

Thread(target=broadcaster).start()

# Constants
g = 9.81  # gravitational acceleration
m1 = 1.0  # mass of block 1
m2 = 1.0  # mass of block 2
initial_pos1 = (150, 340)  # initial position of block 1
initial_pos2 = (210, 340)  # initial position of block 2

w1, l1 = 40, 40
w2, l2 = 40, 40

# Data lists for plotting
time_data = []
velocity_data1 = []
velocity_data2 = []
acceleration_data1 = []
acceleration_data2 = []
position_data1 = []
position_data2 = []

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Simulation variables
pos1 = list(initial_pos1)
pos2 = list(initial_pos2)
vel1 = 0.0
vel2 = 0.0
accel1 = 0.0
accel2 = 0.0
time_elapsed = 0.0
dt = .05  # simulation timestep

# Control flag for physics update
update_physics_running = Event()
update_physics_running.set()

def update_physics():
    global pos1, pos2, vel1, vel2, accel1, accel2, time_elapsed

    while update_physics_running.is_set():
        # Calculate forces and accelerations
        accel1 = (m2 - m1) * g / (m1 + m2)
        accel2 = (m1 - m2) * g / (m1 + m2)
        
        vel1 += accel1 * dt
        vel2 += accel2 * dt

        # Check and correct for collision with bottom boundary
        if pos1[1] >= 550 or pos2[1] >= 550:
            pos1[1] = min(pos1[1], 550)  # Ensure block 1 is within the boundary
            pos2[1] = min(pos2[1], 550)  # Ensure block 2 is within the boundary
            vel1 = 0
            vel2 = 0
        else:
            pos1[1] += vel1 * dt
            pos2[1] += vel2 * dt

        # Store data for plotting
        time_data.append(time_elapsed)
        velocity_data1.append(vel1)
        velocity_data2.append(vel2)
        acceleration_data1.append(accel1)
        acceleration_data2.append(accel2)
        position_data1.append(pos1[1])
        position_data2.append(pos2[1])

        # Send data to WebSocket server
        data.put_nowait([
            ['time', time_elapsed, 't'],
            ['pos1', pos1[1], 'y_{1}'],
            ['pos2', pos2[1], 'y_{2}'],
            ['vel1', vel1, 'v_{1}'],
            ['vel2', vel2, 'v_{2}'],
            ['accel1', accel1, 'a_{1}'],
            ['accel2', accel2, 'a_{2}']
        ])

        time_elapsed += dt
        time.sleep(dt)

        if pos1[1] >= 550 and pos2[1] >= 550:
            break  # Exit the loop when both blocks hit the boundary

# Function to reset simulation
def reset_simulation():
    global pos1, pos2, vel1, vel2, accel1, accel2, time_elapsed
    global update_physics_running

    # Stop the current simulation
    update_physics_running.clear()

    # Reset simulation variables
    pos1 = list(initial_pos1)
    pos2 = list(initial_pos2)
    vel1 = 0.0
    vel2 = 0.0
    accel1 = 0.0
    accel2 = 0.0
    time_elapsed = 0.0
    time_data.clear()
    velocity_data1.clear()
    velocity_data2.clear()
    acceleration_data1.clear()
    acceleration_data2.clear()
    position_data1.clear()
    position_data2.clear()
    all_data.clear()

    # Restart the physics thread
    update_physics_running.set()
    Thread(target=update_physics).start()

# Physics update thread
physics_thread = threading.Thread(target=update_physics)
physics_thread.daemon = True
physics_thread.start()

# Define the open_desmos function with locking
open_desmos_lock = threading.Lock()

def open_desmos():
    with open_desmos_lock:
        webbrowser.open('popout.html')  # Open the Desmos graph in the default web browser

class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('gray')
        self.text = text
        self.txt_surface = pygame.font.Font(None, 25).render(text, True, pygame.Color('white'))
        self.callback = callback

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.txt_surface, (self.rect.x + (self.rect.w - self.txt_surface.get_width()) // 2,
                                       self.rect.y + (self.rect.h - self.txt_surface.get_height()) // 2))

# Button and input field for reset
reset_button = Button(600, 150, 140, 30, 'Reset Simulation', reset_simulation)
button_desmos = Button(600, 300, 140, 30, 'Open Desmos', open_desmos)
button_end = Button(600, 450, 140, 30, 'End Sim', lambda: (pygame.quit(), stop.set(), server.shutdown()))

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        reset_button.handle_event(event)
        button_desmos.handle_event(event)
        button_end.handle_event(event)

    screen.fill((255, 255, 255))

    # Draw blocks
    pygame.draw.rect(screen, (0, 0, 255), (*pos1, w1, l1))
    pygame.draw.rect(screen, (255, 0, 0), (*pos2, w2, l2))
    pygame.draw.line(screen, (0, 0, 0), (200, 0), (200, 75))
    pygame.draw.circle(screen, (200, 0, 0), (200, 75), 30)
    pygame.draw.line(screen, (0, 0, 0), (170, pos1[1] + 40), (170, 75))
    pygame.draw.line(screen, (0, 0, 0), (230, pos2[1] + 40), (230, 75))
    pygame.draw.rect(screen, (200, 0, 0), (pos1[0], pos1[1], w2, w2))
    pygame.draw.rect(screen, (0, 0, 200), (pos2[0], pos2[1], w1, w1))

    # Draw buttons
    reset_button.draw(screen)
    button_desmos.draw(screen)
    button_end.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
stop.set()
server.shutdown()
