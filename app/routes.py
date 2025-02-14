import subprocess
from flask import current_app as app
from flask import render_template, request
from . import socketio

@app.route('/')
def start():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/simulator_with_graphs', methods=['GET', 'POST'])
def simulator_with_graphs():
    return render_template('simgraphs.html')

@app.route('/simulator_without_graphs', methods=['GET', 'POST'])
def simulator_without_graphs():
    return render_template('simnographs.html')

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    simulation_type = request.form.get('simulation_type')
    # Simulations With Graph
    if simulation_type == 'single_object':
        subprocess.Popen(["python3", "app/simulators/graph/sim.py"])
        return render_template('simgraphs.html')
    if simulation_type == 'atwoods':
        subprocess.Popen(["python3", "app/simulators/graph/atwoods.py"])
        return render_template('simgraphs.html')
    if simulation_type == 'pendulum':
        subprocess.Popen(["python3", "app/simulators/graph/pendulum.py"])
        return render_template('simgraphs.html')
    if simulation_type == 'planetary_motion':
        subprocess.Popen(["python3", "app/simulators/graph/planetary_motion.py"])
        return render_template('simgraphs.html')
    if simulation_type == 'elastic_collision':
        subprocess.Popen(["python3", "app/simulators/graph/elastic_collision.py"])
        return render_template('simgraphs.html')
    if simulation_type == 'inelastic_collision':
        subprocess.Popen(["python3", "app/simulators/graph/inelastic_collision.py"])
        return render_template('simgraphs.html')
    if simulation_type == 'rotational_motion':
        subprocess.Popen(["python3", "app/simulators/graph/rotational_motion.py"])
        return render_template('simgraphs.html')
    # Simulations Without Graph
    if simulation_type == 'shapes':
        subprocess.Popen(["python3", "app/simulators/nograph/shapes.py"])
        return render_template('simnographs.html')
    if simulation_type == 'camera':
        subprocess.Popen(["python3", "app/simulators/nograph/camera.py"])
        return render_template('simnographs.html')

@app.route('/desmos')
def desmos():
    return render_template('desmos.html')

@app.route('/ellastic')
def ellastic():
    return render_template('ellastic.html')

@app.route('/basicsim')
def sim():
    return render_template('sim.html')

@app.route('/atwoods')
def atwoods():
    return render_template('atwoods.html')

# Example of emitting WebSocket data
@socketio.on('connect')
def handle_connect():
    print('Client connected')

def send_simulation_data(data):
    socketio.emit('update', data)
