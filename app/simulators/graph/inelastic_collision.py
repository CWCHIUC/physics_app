import pygame
import math

# Pygame initialization
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GROUND_HEIGHT = 100  # Height of the ground from the bottom

# Create the Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Inelastic Collision Simulator")

# Clock for controlling FPS
clock = pygame.time.Clock()

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
        
        if self.y > HEIGHT - GROUND_HEIGHT - self.radius:
            self.velocity[1] = -self.velocity[1]
            self.y = HEIGHT - GROUND_HEIGHT - self.radius
        elif self.y < self.radius:
            self.velocity[1] = -self.velocity[1]
            self.y = self.radius

    def apply_gravity(self):
        # Example: applying gravity (if needed)
        pass

# Initialize two balls
ball1 = Ball(100, HEIGHT - GROUND_HEIGHT - 20, 20, 1, (255, 0, 0), [2, 0])
ball2 = Ball(700, HEIGHT - GROUND_HEIGHT - 30, 30, 2, (0, 0, 255), [-1, 0])

# Main simulation loop
running = True
while running:
    screen.fill(BLACK)  # Clear screen

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update balls
    ball1.move()
    ball1.bounce()
    ball2.move()
    ball2.bounce()

    # Check for collision between balls
    distance = math.sqrt((ball1.x - ball2.x)**2 + (ball1.y - ball2.y)**2)
    if distance < ball1.radius + ball2.radius:
        # Inelastic collision example: combine masses and average velocities
        total_mass = ball1.mass + ball2.mass
        new_velocity_x = (ball1.velocity[0] * ball1.mass + ball2.velocity[0] * ball2.mass) / total_mass
        new_velocity_y = (ball1.velocity[1] * ball1.mass + ball2.velocity[1] * ball2.mass) / total_mass
        ball1.velocity = [new_velocity_x, new_velocity_y]
        ball2.velocity = [new_velocity_x, new_velocity_y]

    # Draw ground
    pygame.draw.rect(screen, WHITE, (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))

    # Draw balls
    ball1.draw()
    ball2.draw()

    pygame.display.flip()  # Update display
    clock.tick(60)  # Cap FPS

pygame.quit()  # Quit Pygame
