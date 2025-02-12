import pygame
import pymunk
import pymunk.pygame_util
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()

# Pymunk space setup
space = pymunk.Space()
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Create a wheel
wheel_radius = 50
wheel_mass = 1
wheel_position = (300, 300)
wheel = None
angular_velocities = []
angular_accelerations = []
forces = []
times = []
positions = []

# Constants
angular_velocity = -2.0  # radians per second (clockwise)
elapsed_time = 0.0  # Initialize elapsed time

def create_wheel(space, position, radius, mass):
    global wheel
    if wheel is not None:
        space.remove(wheel, wheel.body)
    body = pymunk.Body()
    body.position = position
    inertia = pymunk.moment_for_circle(mass, 0, radius)  # Calculate moment of inertia
    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.friction = 0.5
    space.add(body, shape)
    body.angular_velocity = angular_velocity
    wheel = shape

# Function to update physics and track data
def update_physics_and_track_data():
    global elapsed_time

    # Update physics
    space.step(1/60.0)

    # Track elapsed time
    elapsed_time += 1/60.0

    # Calculate torque (tau) and force (f = MR^2)
    if wheel is not None:
        moment_of_inertia = wheel.mass * wheel.radius ** 2
        torque = moment_of_inertia * wheel.body.angular_velocity
        force = torque / wheel.radius

        # Update angular velocity, acceleration, and force
        angular_velocity = wheel.body.angular_velocity
        angular_acceleration = force / moment_of_inertia
        angular_velocities.append(angular_velocity)
        angular_accelerations.append(angular_acceleration)
        forces.append(force)

        # Track marker position
        center = wheel.body.position
        marker_position = center + pymunk.Vec2d(wheel_radius, 0).rotated(wheel.body.angle)
        positions.append(marker_position)

        # Track time
        times.append(elapsed_time)

# Create initial wheel
create_wheel(space, wheel_position, wheel_radius, wheel_mass)

# Function to create the plot window
def create_plot_window():
    root = tk.Tk()
    root.title("Graph")

    fig, ax1 = plt.subplots(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    data_options = ["Time", "Angular Velocity", "Position", "Angular Acceleration", "Force"]

    x_var = tk.StringVar(value=data_options[0])
    y_var = tk.StringVar(value=data_options[1])

    def update_plot_wrapper():
        x_label = x_var.get().lower()
        y_label = y_var.get().lower()

        # Select data based on user selection
        if x_label == "time":
            x_data = times
        elif x_label == "angular velocity":
            x_data = angular_velocities
        elif x_label == "position":
            x_data = [pos.x for pos in positions]
        elif x_label == "angular acceleration":
            x_data = angular_accelerations
        elif x_label == "force":
            x_data = forces

        if y_label == "time":
            y_data = times
        elif y_label == "angular velocity":
            y_data = angular_velocities
        elif y_label == "position":
            y_data = [pos.y for pos in positions]
        elif y_label == "angular acceleration":
            y_data = angular_accelerations
        elif y_label == "force":
            y_data = forces

        if len(x_data) != len(y_data):
            return  # Ensure x_data and y_data have the same length

        ax1.clear()
        ax1.plot(x_data, y_data)
        ax1.set_title(f"{y_var.get()} vs {x_var.get()}")
        ax1.set_xlabel(x_var.get())
        ax1.set_ylabel(y_var.get())
        ax1.grid(True)
        canvas.draw()

    # OptionMenus for selecting X-axis and Y-axis variables
    tk.Label(root, text="X-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, x_var, *data_options, command=lambda _: update_plot_wrapper()).pack(side=tk.LEFT)

    tk.Label(root, text="Y-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, y_var, *data_options, command=lambda _: update_plot_wrapper()).pack(side=tk.LEFT)

    # Function to update plot periodically
    def update_plot_periodically():
        while True:
            update_plot_wrapper()
            root.update()  # Update the Tkinter window
            pygame.time.wait(1000)  # Update every 1 second to reduce lag

    # Start thread to update plot periodically
    plot_thread = threading.Thread(target=update_plot_periodically)
    plot_thread.start()

    root.mainloop()

# Function to create the main control panel window
def create_main_window():
    main_root = tk.Tk()
    main_root.title("Control Panel")

    def update_radius(value):
        global wheel_radius
        wheel_radius = int(value)
        create_wheel(space, wheel_position, wheel_radius, wheel_mass)

    radius_slider = tk.Scale(main_root, label="Wheel Radius", orient=tk.HORIZONTAL, from_=10, to=100, length=200, command=lambda value: update_radius(value))
    radius_slider.pack()

    def update_mass(value):
        global wheel_mass
        wheel_mass = float(value)
        create_wheel(space, wheel_position, wheel_radius, wheel_mass)

    mass_slider = tk.Scale(main_root, label="Wheel Mass", orient=tk.HORIZONTAL, from_=0.1, to=5.0, resolution=0.1, length=200, command=lambda value: update_mass(value))
    mass_slider.pack()

    def on_button_click():
        plot_data_thread = threading.Thread(target=create_plot_window)
        plot_data_thread.start()

    button = tk.Button(main_root, text="Open Graph", command=on_button_click)
    button.pack(side=tk.TOP)

    main_root.mainloop()

# Start the control panel window in the main thread
if __name__ == "__main__":
    control_panel_thread = threading.Thread(target=create_main_window)
    control_panel_thread.start()

# Main Pygame loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill((255, 255, 255))

    # Update physics and track data
    update_physics_and_track_data()

    # Draw objects
    space.debug_draw(draw_options)

    # Draw a marker on the rotating wheel
    if wheel is not None:
        center = wheel.body.position
        marker_position = center + pymunk.Vec2d(wheel_radius, 0).rotated(wheel.body.angle)
        pygame.draw.line(screen, (255, 0, 0), center, marker_position, 2)
        pygame.draw.circle(screen, (255, 0, 0), (int(marker_position.x), int(marker_position.y)), 5)

    # Display elapsed time on the screen
    font = pygame.font.Font(None, 36)
    text_surface = font.render(f'Time: {elapsed_time:.2f} seconds', True, (0, 0, 0))
    screen.blit(text_surface, (10, 10))

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
