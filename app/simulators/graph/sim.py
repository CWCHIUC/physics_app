import pygame
import pymunk
import pymunk.pygame_util
import math
from threading import Thread, Event
from queue import Queue, Empty, Full
from json import dumps
from websockets.sync.server import serve
import time
import threading

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1000, 800
window = pygame.display.set_mode((WIDTH, HEIGHT))
all_data = []

# WebSocket server setup
connected = set()
data = Queue()
stop = Event()
b = True

def handler(websocket):
    connected.add(websocket)
    init_message = {
        'type': 'init',
        'name': 'pendulum',
        'default_settings': {'xAxisValue': 'Time', 'yAxisValue': 'Pos'}
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
            pass
    finally:
        connected.remove(websocket)

def start_server():
    server = serve(handler, '', 8043)
    Thread(target=server.serve_forever).start()
    return server

server = start_server()

def broadcaster():
    while not stop.is_set():
        for websocket in connected.copy():
            try:
                got = data.get_nowait()
                update_message = {
                    'type': 'update',
                    'values': got
                }
                websocket.send(dumps(update_message))
            except Empty:
                pass
        time.sleep(0.1)

Thread(target=broadcaster).start()

# Pygame functions and main loop
position1 = []  # x-coordinates
position2 = []  # y-coordinates
time_data = []
vel1 = []
velx = []
vely = []
position = []
initial_pos1 = (WIDTH/2, 200)
FIXED_DT = 1 / 60  # Fixed time step
time_elapsed = 0.0

def update_physics(ball):
    global position1, position2, time_data, vel1, time_elapsed

    if ball is None:
        return

    accumulator = 0.0
    last_time = time.time()

    while not stop.is_set():
        current_time = time.time()
        frame_time = current_time - last_time
        accumulator += frame_time

        while accumulator >= FIXED_DT:
            pos = ball.position
            velocity = ball.velocity
            speed = math.sqrt(velocity[0]**2 + velocity[1]**2)
            positionMag = math.sqrt(pos[0]**2 + pos[1]**2)
            #theta = math.atan2(pos.y - initial_pos1[1], pos.x - initial_pos1[0])

            # Append data to lists
            position1.append(pos.x)
            position2.append(pos.y)
            time_data.append(time_elapsed)
            velx.append(velocity.x)
            vely.append(velocity.y)
            vel1.append(speed)
            position.append(positionMag)

            # Print debug info
            # print(f"Time Elapsed: {time_elapsed:.2f}, Position X: {pos.x:.2f}, Position Y: {pos.y:.2f}, Delta Time: {frame_time:.3f}")

            # Prepare data to send
            data_to_send = [
                ['time', time_elapsed, 't'],
                ['x_pos1', position1[-1], 'x_{1}'],
                ['y_pos1', position2[-1], 'y_{2}'],
                ['position', positionMag, 'P_{3}'],
                ['velx', velx[-1], 'v_{1}'],
                ['vely', vely[-1], 'v_{2}'],
                ['vel1', speed, 'V_{3}']
            ]

            try:
                data.put_nowait(data_to_send)
            except Full:
                pass  # Handle queue full case if necessary

            # Update time and accumulator
            time_elapsed += FIXED_DT
            accumulator -= FIXED_DT

        # Sleep to prevent excessive CPU usage
        time.sleep(0.01)
        last_time = current_time

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

def create_ball1(space, radius, mass):
    body = pymunk.Body()
    body.position = (300, 300)  # Initial position of the ball
    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.color = (0, 255, 255, 100)
    shape.elasticity = 0.7
    space.add(body, shape)
    return body

def run(window, width, height):
    run = True
    clock = pygame.time.Clock()
    fps = 60
    dt = 1 / fps

    space = pymunk.Space()
    space.gravity = (0, 981)
    

    create_boundaries(space, width, height)
    create_structure(space, 100, 800)
    ball = create_ball1(space, 30, 10)

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
                    data_to_send = [[1, 2, 3]]
                    data.put_nowait(data_to_send)
                else:
                    #space.remove(ball, ball.body)
                    ball = None

        draw(space, window, draw_options, line)
        space.step(dt)
        clock.tick(fps)

    pygame.quit()

if __name__ == "__main__":
    run(window, WIDTH, HEIGHT)

    for websocket in connected.copy():
        websocket.close()
    server.shutdown()
    stop.set()
