const NAMESPACE = 'physiolab';
let REGISTERED = false;
let NAME = '';
const websocket = new WebSocket(`ws://localhost:8042`); //changed port
const calculatorElement = document.getElementById('calculator');
const calculator = Desmos.GraphingCalculator(calculatorElement);

/**
 * @param {number[]} arr
 */
function latexify(arr) {
    return '\\left[' + arr.map((n) => n.toPrecision(4)).join(',') + '\\right]';
}

/**
 * @type {Map.<string,number[]>}
 */
const storedValues = new Map();

/**
 * @type {Map.<string,string>}
 */
const latexNames = new Map();

websocket.onerror = console.error;

websocket.onmessage = function(event) {
    const contents = JSON.parse(event.data);

    if (REGISTERED) {
        console.assert(contents['type'] === 'update');
        if ('values' in contents) {
            for (const [name, value, latex] of contents['values']) {
                if (storedValues.has(name)) {
                    storedValues.get(name).push(value);
                } else {
                    storedValues.set(name, [value]);
                    latexNames.set(name, latex);
                }
            }
        }
    } else {
        console.assert(contents['type'] === 'init');
        REGISTERED = true;
        NAME = contents['name'];
        calculator.setExpression({
            type: 'table',
            columns: [
                { latex: contents['default_settings']['xAxisValue'] },
                { latex: contents['defaultSettings']['yAxisValue'] }
            ],
            id: `${NAMESPACE}__output`,
        });
    }
};

setInterval(function() {
    for (const [name, value] of storedValues) {
        const desmosName = `${NAMESPACE}__${name}`;
        calculator.setExpression({
            type: 'expression',
            latex: `${latexNames.get(name)}=${latexify(value)}`,
            id: desmosName,
        });
    }
}, 50);

function popout() {
    const child = window.open(' ', '_blank', 'popup=true');
}
document.getElementById('xAxisValue').addEventListener('change', updateDesmosGraph);
document.getElementById('yAxisValue').addEventListener('change', updateDesmosGraph);

function updateDesmosGraph() {
    const axisValueMap = {
        'time': 't',
        'Position 1': 'y_{1}',
        'Position  2': 'y_{2}',
        'Velocity 1': 'v_{1}',
        'Velocity 2': 'v_{2}',
        'Energy 1': 'E_{1}',
        'Energy 2': 'E_{2}',
        'Center of Mass': 'c_{1}',
        'velocity 1' : 'v_{1}',
        'velocity 2': 'v_{2}',
        'momentum 1' : 'p_{1}',
        'momentum 2': 'p_{2}'

    };
    
    const xAxisValue = axisValueMap[document.getElementById('xAxisValue').value];
    const yAxisValue = axisValueMap[document.getElementById('yAxisValue').value];
    
    console.log("Selected x-axis value:", xAxisValue);
    console.log("Selected y-axis value:", yAxisValue);
    
    // Debugging: Check if the values exist in the storedValues map
    console.log("Stored values for x-axis:", storedValues.get(xAxisValue));
    console.log("Stored values for y-axis:", storedValues.get(yAxisValue));
    
    calculator.setExpression({
        type: 'table',
        columns: [
            { latex: xAxisValue || 'undefined' },  // Use 'undefined' for debugging if value is missing
            { latex: yAxisValue || 'undefined' }
        ],
        id: `${NAMESPACE}__output`,
    });
}
// Get slider elements
// Get slider elements
const mass1Slider = document.getElementById('mass1_slider');
const mass2Slider = document.getElementById('mass2_slider');

// Get value display elements
const mass1Value = document.getElementById('mass1_value');
const mass2Value = document.getElementById('mass2_value');

// Function to update the displayed value and send the new mass values
// Ensure only one updateMass function is defined
function updateMass() {
    const mass1 = parseFloat(mass1Slider.value);
    const mass2 = parseFloat(mass2Slider.value);
    mass1Value.textContent = mass1.toFixed(1);
    mass2Value.textContent = mass2.toFixed(1);

    // Send updated masses to the WebSocket server
    websocket.send(JSON.stringify({ type: 'update_mass', mass1, mass2 }));
}

// Add event listeners for sliders
mass1Slider.addEventListener('input', updateMass);
mass2Slider.addEventListener('input', updateMass);


