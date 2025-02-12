import pygame
import math
import time
from threading import Thread, Event
from queue import Queue, Full, Empty
import asyncio
import websockets
import json

# Pygame initialization
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
connected = set()
data = Queue()
mass1, mass2 = 1, 2  # Default masses

# Create the Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elastic Collision Simulator")

# Clock for controlling FPS
clock = pygame.time.Clock()

# Reset button constants
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50
BUTTON_COLOR = (0, 255, 0)
BUTTON_HOVER_COLOR = (0, 200, 0)
BUTTON_X = WIDTH - BUTTON_WIDTH - 20
BUTTON_Y = 20

class Ball:
    def __init__(self, x, y, radius, mass, color, velocity):
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.color = color
        self.velocity = velocity

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def move(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]

    def bounce(self):
        if self.x > WIDTH - self.radius:
            self.velocity[0] = -self.velocity[0]
            self.x = WIDTH - self.radius
        elif self.x < self.radius:
            self.velocity[0] = -self.velocity[0]
            self.x = self.radius
        
        if self.y > HEIGHT - self.radius:
            self.velocity[1] = -self.velocity[1]
            self.y = HEIGHT - self.radius
        elif self.y < self.radius:
            self.velocity[1] = -self.velocity[1]
            self.y = self.radius

    def check_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < self.radius + other.radius:
            # Elastic collision: calculate new velocities
            dvx = other.velocity[0] - self.velocity[0]
            dvy = other.velocity[1] - self.velocity[1]
            dvdotdr = dx * dvx + dy * dvy
            distance_square = dx**2 + dy**2
            
            # Update velocities based on elastic collision equations
            self.velocity[0] += (2 * other.mass / (self.mass + other.mass)) * (dvdotdr * dx / distance_square)
            self.velocity[1] += (2 * other.mass / (self.mass + other.mass)) * (dvdotdr * dy / distance_square)
            
            other.velocity[0] -= (2 * self.mass / (self.mass + other.mass)) * (dvdotdr * dx / distance_square)
            other.velocity[1] -= (2 * self.mass / (self.mass + other.mass)) * (dvdotdr * dy / distance_square)

# Initialize two balls
ball1 = Ball(100, 300, 20, mass1, (255, 0, 0), [2, 0])
ball2 = Ball(700, 300, 30, mass2, (0, 0, 255), [-2, 0])

async def handle_websocket(websocket, path):
    global ball1, ball2

    # Send initial settings
    await websocket.send(json.dumps({
        "type": "init",
        "name": "Physics Simulation",
        "default_settings": {
            "xAxisValue": "t",
            "yAxisValue": "y_{1}"
        }
    }))

    # Start sending data immediately, even if no message is received
    async def send_updates():
        while True:
            try:
                data_to_send = data.get_nowait()
            except Empty:
                await asyncio.sleep(0.1)
                continue

            message = {
                "type": "update",
                "values": data_to_send
            }
            await websocket.send(json.dumps(message))
            await asyncio.sleep(0.1)

    # Create a task to send updates
    send_task = asyncio.create_task(send_updates())

    async for message in websocket:
        data_received = json.loads(message)
        if data_received['type'] == 'update_mass':
            ball1.mass = data_received['mass1']
            ball2.mass = data_received['mass2']
            print(f"Updated masses: ball1 = {ball1.mass}, ball2 = {ball2.mass}")
        elif data_received['type'] == 'update_axis':
            # Handle axis update if needed
            pass

    send_task.cancel()

async def main():
    server = await websockets.serve(handle_websocket, "localhost", 8042) # changed port
    await server.wait_closed()

# Start the WebSocket server in a separate thread
asyncio_loop = asyncio.new_event_loop()  # Use new_event_loop instead of get_event_loop
asyncio_thread = Thread(target=lambda: asyncio_loop.run_until_complete(main()))
asyncio_thread.start()

shutdown_event = Event()

# Physics function
def physics(ball1, ball2):
    global data
    time_elapsed = 0
    dt = 0.1

    while not shutdown_event.is_set():
        # Compute physics values
        momentum1 = ball1.mass * ball1.velocity[0]
        momentum2 = ball2.mass * ball2.velocity[0]
        position1 = ball1.x
        position2 = ball2.x
        velocity1 = ball1.velocity[0]  # x-component of velocity for ball1
        velocity2 = ball2.velocity[0]  # x-component of velocity for ball2
        center_of_mass = (ball1.mass * ball1.x + ball2.mass * ball2.x) / (ball1.mass + ball2.mass)
        kinetic_energy1 = 0.5 * ball1.mass * (ball1.velocity[0] ** 2)
        kinetic_energy2 = 0.5 * ball2.mass * (ball2.velocity[0] ** 2)

        # Prepare data to send
        data_to_send = [
            ['time', time_elapsed, 't'],
            ['position1', position1, 'y_{1}'],  
            ['position2', position2, 'y_{2}'],
            ['velocity1', velocity1, 'v_{1}'],  # Adding velocity data
            ['velocity2', velocity2, 'v_{2}'],  # Adding velocity data
            ['Center of Mass', center_of_mass, 'c_{1}'],  
            ['Kinetic energy 1', kinetic_energy1, 'E_{1}'],
            ['Kinetic energy 2', kinetic_energy2, 'E_{2}'],
            ['momentum 1', momentum1, 'p_{1}'],
            ['momentum 2', momentum2, "p_{2}"]
        ]

        try:
            data.put_nowait(data_to_send)
        except Full:
            pass

        time_elapsed += dt
        time.sleep(dt)


# Start physics calculations in a separate thread
physics_thread = Thread(target=physics, args=(ball1, ball2))
physics_thread.start()

def draw_reset_button(hover=False):
    color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
    reset_button_rect = pygame.Rect(BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, color, reset_button_rect)
    font = pygame.font.Font(None, 36)
    text = font.render("Reset", True, BLACK)
    screen.blit(text, (BUTTON_X + (BUTTON_WIDTH - text.get_width()) // 2, BUTTON_Y + (BUTTON_HEIGHT - text.get_height()) // 2))
    return reset_button_rect

def reset_simulation():
    global ball1, ball2
    ball1 = Ball(100, 300, 20, mass1, (255, 0, 0), [2, 0])
    ball2 = Ball(700, 300, 30, mass2, (0, 0, 255), [-2, 0])

# Main simulation loop
running = True
while running:
    screen.fill(BLACK)  # Clear screen
    mouse_pos = pygame.mouse.get_pos()
    reset_button_rect = draw_reset_button(hover=reset_button_rect.collidepoint(mouse_pos) if 'reset_button_rect' in locals() else False)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if reset_button_rect.collidepoint(mouse_pos):
                reset_simulation()

    # Update balls
    ball1.move()
    ball1.bounce()
    ball2.move()
    ball2.bounce()

    # Check for collision between balls
    ball1.check_collision(ball2)

    # Draw balls
    ball1.draw()
    ball2.draw()

    pygame.display.flip()
    clock.tick(60)  # Limit FPS to 60

# Set the shutdown event to stop the physics thread
shutdown_event.set()
physics_thread.join()

# Shutdown WebSocket server
asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
asyncio_thread.join()

pygame.quit()
