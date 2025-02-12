import pygame
import pymunk
import pymunk.pygame_util
import math
from threading import Thread, Event
from queue import Queue, Empty, Full
from json import dumps
import time
import asyncio
import websockets
import threading

b = False
pygame.init()

WIDTH, HEIGHT = 1000, 800
window = pygame.display.set_mode((WIDTH, HEIGHT))
all_data = []

# WebSocket server setup
connected = set()
data = Queue()
stop = Event()

async def handler(websocket, path):
    connected.add(websocket)
    init_message = {
        'type': 'init',
        'name': 'pendulum',
        'default_settings': {'xAxisValue': 'Time', 'yAxisValue': 'Pos'}
    }
    await websocket.send(dumps(init_message))
    global b
    global all_data
    if b:
        for entry in all_data:
            update_message = {
                'type': 'update',
                'values': entry
            }
            await websocket.send(dumps(update_message))
    else:
        b = True

    try:
        async for msg in websocket:
            pass
    finally:
        connected.remove(websocket)

async def start_server():
    async with websockets.serve(handler, '', 8041):  # Change 8032 to an available port like 8040
        await asyncio.Future()  # Run forever

async def broadcaster():
    while not stop.is_set():
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
                    await websocket.send(dumps(update_message))
                else:
                    b = True
            except Empty:
                pass
        await asyncio.sleep(.1)

# Start the server and broadcaster in the event loop
async def main():
    await asyncio.gather(start_server(), broadcaster())

# Pygame functions and main loop
time_data = []
position1 = []
vel1 = []
initial_pos1 = (WIDTH/2, 200)
dt = .05
pos1 = list(initial_pos1)
time_elapsed = 0.0

def update_physics(ball):
    global pos1, time_data, vel1, time_elapsed

    if ball is None:
        return

    while not stop.is_set():
        # Get current time
        current_time = time.time()

        # Update position and velocity
        pos = ball.position
        velocity = ball.velocity
        speed = math.sqrt(velocity[0]**2 + velocity[1]**2)

        # Calculate angle (theta)
        theta = math.atan2(pos[1] - initial_pos1[1], pos[0] - initial_pos1[0])

        # Store data for WebSocket
        pos1.append((pos[0], pos[1]))
        time_data.append(current_time)
        vel1.append(speed)

        # Prepare data to send
        if len(pos1) > 0:
            last_pos1 = pos1[-1]
            last_x_pos, last_y_pos = last_pos1
        else:
            last_x_pos = last_y_pos = 0

        data_to_send = [
            ['time', time_elapsed, 't'],
            ['x_pos1', last_x_pos, 'x_{1}'],
            ['y_pos1', last_y_pos, 'y_{1}'],
            ['vel1', vel1[-1] if vel1 else 0, 'v_{1}'],
            ['theta', theta, 'a_{1}']
        ]

        # Send data to WebSocket
        try:
            data.put_nowait(data_to_send)
        except Full:
            # Handle case where queue is full
            pass

        time_elapsed += dt
        time.sleep(dt)

def calculate_distance(p1, p2):
    return math.sqrt((p2[1] - p1[1])**2 + (p2[0] - p1[0])**2)

def calculate_angle(p1, p2):
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])

def create_boundaries(space, width, height):
    rects = [
        [(width/2, height - 10), (width, 20)],
        [(width/2, 10), (width, 20)],
        [(10, height/2), (20, height)],
        [(width - 10, height/2), (20, height)]
    ]

    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos
        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.4
        shape.friction = 0.5
        space.add(body, shape)

def create_structure(space, width, height):
    BROWN = (139, 69, 19, 100)
    rects = [
        [(600, height - 120), (40, 200), BROWN, 100],
        [(900, height - 120), (40, 200), BROWN, 100],
        [(750, height - 240), (340, 40), BROWN, 150]
    ]

    for pos, size, color, mass in rects:
        body = pymunk.Body()
        body.position = pos
        shape = pymunk.Poly.create_box(body, size, radius=2)
        shape.color = color
        shape.mass = mass
        shape.elasticity = 0.4
        shape.friction = 0.4
        space.add(body, shape)

def create_swinging_ball(space, length):
    # Create the rotation center (static body)
    rotation_center_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    rotation_center_body.position = (WIDTH/2, 200)

    # Create the swinging ball body
    ball_body = pymunk.Body()
    ball_body.position = (rotation_center_body.position.x + length, 200)
    ball_shape = pymunk.Circle(ball_body, radius=20)
    ball_shape.mass = 30
    ball_shape.elasticity = 1.0
    ball_shape.friction = 0.0

    # Pin joint to connect the ball and the arm to the rotation center
    ball_joint = pymunk.PinJoint(ball_body, rotation_center_body, (0, 0), (0, 0))

    # Add everything to the space
    space.add(ball_body, ball_shape, ball_joint)

    return ball_body

def create_ball(space, radius, mass, pos):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = pos
    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.elasticity = 0.9
    shape.friction = 0.4
    shape.color = (255, 0, 0, 100)
    space.add(body, shape)
    # Set up a timer to despawn the ball after 6 seconds
    def despawn_ball():
        if shape in space.shapes:
            space.remove(body, shape)  # Remove both body and shape from space

    timer = threading.Timer(6, despawn_ball)  # Start the timer for 6 seconds
    timer.start()

    return shape

def draw(space, window, draw_options, line):
    window.fill("white")

    if line:
        pygame.draw.line(window, "black", line[0], line[1], 3)

    space.debug_draw(draw_options)

    pygame.display.update()

def run(window, width, height):
    run = True
    clock = pygame.time.Clock()
    fps = 60
    dt = 1 / fps

    space = pymunk.Space()
    space.gravity = (0, 981)
    
    create_boundaries(space, width, height)
    ball = create_swinging_ball(space, 400)

    draw_options = pymunk.pygame_util.DrawOptions(window)

    pressed_pos = None
    
    physics_thread = threading.Thread(target=update_physics, args=(ball,))
    physics_thread.start()

    while run:
        line = None
        if ball and pressed_pos:
            line = [pressed_pos, pygame.mouse.get_pos()]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not ball:
                    pressed_pos = pygame.mouse.get_pos()
                    ball = create_ball(space, 30, 10, pressed_pos)
                elif pressed_pos:
                    ball.body.body_type = pymunk.Body.DYNAMIC
                    angle = calculate_angle(*line)
                    force = calculate_distance(*line) * 50
                    fx = math.cos(angle) * force
                    fy = math.sin(angle) * force
                    ball.body.apply_impulse_at_local_point((fx, fy), (0, 0))
                    pressed_pos = None
                    # Send data to WebSocket clients
                    data_to_send = [[1, 2, 3]]  # Example data
                    data.put_nowait(data_to_send)

                else:
                    # space.remove(ball, ball.body)
                    ball = None

        draw(space, window, draw_options, line)
        space.step(dt)
        clock.tick(fps)

    pygame.quit()

if __name__ == "__main__":
    # Start the main game loop and the WebSocket server
    game_thread = threading.Thread(target=run, args=(window, WIDTH, HEIGHT))
    game_thread.start()

    asyncio.run(main())

    # Cleanup on exit
    for websocket in connected.copy():
        asyncio.run(websocket.close())
    stop.set()
