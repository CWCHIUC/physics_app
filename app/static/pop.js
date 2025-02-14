const NAMESPACE = 'physiolab';
let REGISTERED = false;
let NAME = '';
const websocket = new WebSocket(`ws://localhost:8041`);
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
        'Position Block 1': 'y_{1}',
        'Position Block 2': 'y_{2}',
        'Velocity Block 1': 'v_{1}',
        'Velocity Block 2': 'v_{2}',
        'Acceleration Block 1': 'a_{1}',
        'Acceleration Block 2': 'a_{2}'
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
document.getElementById('mass1').addEventListener('change', updateMass);
document.getElementById('mass2').addEventListener('change', updateMass);

function updateMass() {
    const mass1 = parseFloat(document.getElementById('mass1').value);
    const mass2 = parseFloat(document.getElementById('mass2').value);
    websocket.send(JSON.stringify({ type: 'update_mass', mass1, mass2 }));
}
