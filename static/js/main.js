// WebSocket connection
const socket = io();

// Safety system variables
let safetyStatus = 'safe'; // 'safe' or 'danger'
let gameEnabled = true;

// Chart configuration
let chart;
let isPaused = false;
let totalSamples = 0;

// Data buffers
const MAX_POINTS = 4000; // 5 seconds at 800 Hz
let rawData = [];
let envelopeData = [];
let timeData = [];

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('waveformChart').getContext('2d');
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Raw Signal',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0.1
                },
                {
                    label: 'Envelope',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1
                },
                {
                    label: 'Threshold',
                    data: [],
                    borderColor: '#f39c12',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [10, 5],
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'ADC Counts (0-1023)'
                    },
                    min: 0,
                    max: 1023,
                    ticks: {
                        stepSize: 100
                    }
                }
            }
        }
    });
}

// Safety system functions
function updateSafetyStatus(status, areas = {}) {
    safetyStatus = status;
    const safetyDot = document.getElementById('safety-dot');
    const safetyText = document.getElementById('safety-text');
    const safetyMessage = document.getElementById('safety-message');
    
    // Update individual LiDAR status
    updateLidarStatus('rear', areas.rear || false);
    updateLidarStatus('left', areas.left || false);
    updateLidarStatus('right', areas.right || false);
    
    if (status === 'danger') {
        safetyDot.className = 'safety-dot danger';
        safetyText.textContent = 'DANGER - Person Detected';
        safetyText.className = 'safety-text danger';
        
        const areaList = areas.areas ? areas.areas.join(', ') : 'Unknown';
        safetyMessage.innerHTML = `<p><strong>⚠️ SAFETY ALERT:</strong> Person detected in: ${areaList}. Game is disabled for safety.</p>`;
        safetyMessage.className = 'safety-message danger';
        gameEnabled = false;
    } else {
        safetyDot.className = 'safety-dot';
        safetyText.textContent = 'SAFE - Game Ready';
        safetyText.className = 'safety-text safe';
        safetyMessage.innerHTML = '<p>System is ready for gameplay. Hit the PBT sensor to score points!</p>';
        safetyMessage.className = 'safety-message';
        gameEnabled = true;
    }
}

function updateLidarStatus(lidar, detected) {
    const lidarElement = document.querySelector(`.lidar-status.${lidar}`);
    const statusElement = document.getElementById(`${lidar}-status`);
    
    if (lidarElement && statusElement) {
        if (detected) {
            lidarElement.classList.add('detected');
            statusElement.textContent = 'DETECTED';
        } else {
            lidarElement.classList.remove('detected');
            statusElement.textContent = 'CLEAR';
        }
    }
}

// Update chart with new data
function updateChart(newRaw, newEnv, newTime, threshold) {
    if (isPaused) return;

    // Append new data
    rawData.push(...newRaw);
    envelopeData.push(...newEnv);
    timeData.push(...newTime);

    // Keep only last MAX_POINTS
    if (rawData.length > MAX_POINTS) {
        const excess = rawData.length - MAX_POINTS;
        rawData = rawData.slice(excess);
        envelopeData = envelopeData.slice(excess);
        timeData = timeData.slice(excess);
    }

    // Create threshold line
    const thresholdData = new Array(timeData.length).fill(threshold);

    // Update chart
    chart.data.labels = timeData;
    chart.data.datasets[0].data = rawData;
    chart.data.datasets[1].data = envelopeData;
    chart.data.datasets[2].data = thresholdData;
    
    chart.update('none'); // 'none' mode for best performance
}

// Update statistics display
function updateStats(baseline, envelope, threshold) {
    document.getElementById('baseline-value').textContent = baseline.toFixed(1);
    document.getElementById('envelope-value').textContent = envelope.toFixed(1);
    document.getElementById('threshold-value').textContent = threshold.toFixed(0);
}

// Update connection status
function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    if (connected) {
        statusDot.classList.add('connected');
        statusDot.classList.remove('disconnected');
        statusText.textContent = 'Connected';
        statusText.style.color = '#27ae60';
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
        statusText.style.color = '#e74c3c';
    }
}

// Socket.io event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
});

socket.on('initial_data', (data) => {
    console.log('Received initial data:', data.raw.length, 'samples');
    rawData = data.raw;
    envelopeData = data.envelope;
    timeData = data.time;
    totalSamples = rawData.length;
    
    updateChart([], [], [], data.threshold);
    updateStats(data.baseline, data.envelope[data.envelope.length - 1] || 0, data.threshold);
    
    document.getElementById('buffer-size').textContent = rawData.length;
    document.getElementById('sample-count').textContent = totalSamples;
    
    if (data.pulse_count !== undefined) {
        document.getElementById('pulse-count').textContent = data.pulse_count;
    }
});

socket.on('sensor_data', (data) => {
    if (data.raw && data.raw.length > 0) {
        totalSamples += data.raw.length;
        
        updateChart(data.raw, data.envelope, data.time, data.threshold);
        
        const lastEnvelope = data.envelope[data.envelope.length - 1] || 0;
        updateStats(data.baseline, lastEnvelope, data.threshold);
        
        document.getElementById('buffer-size').textContent = rawData.length;
        document.getElementById('sample-count').textContent = totalSamples;
        
        if (data.pulse_count !== undefined) {
            document.getElementById('pulse-count').textContent = data.pulse_count;
        }
    }
});

// Safety system WebSocket events
socket.on('safety_status', (data) => {
    updateSafetyStatus(data.status, data.areas || {});
    gameEnabled = data.game_enabled;
    console.log('Safety status updated:', data);
});

// Control buttons
document.getElementById('pause-btn').addEventListener('click', function() {
    isPaused = !isPaused;
    this.textContent = isPaused ? 'Resume' : 'Pause';
    this.classList.toggle('paused');
});

document.getElementById('clear-btn').addEventListener('click', function() {
    rawData = [];
    envelopeData = [];
    timeData = [];
    totalSamples = 0;
    
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.data.datasets[1].data = [];
    chart.data.datasets[2].data = [];
    chart.update();
    
    document.getElementById('buffer-size').textContent = '0';
    document.getElementById('sample-count').textContent = '0';
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    // Safety system test buttons
    const testPersonBtn = document.getElementById('test-person-btn');
    const testTim100Btn = document.getElementById('test-tim100-btn');
    const testTim150Btn = document.getElementById('test-tim150-btn');
    const testClearBtn = document.getElementById('test-clear-btn');
    
    testPersonBtn.addEventListener('click', function() {
        socket.emit('test_person_detected');
        console.log('Test: Rear detected - Game disabled');
    });
    
    testTim100Btn.addEventListener('click', function() {
        socket.emit('test_tim100_detected');
        console.log('Test: Left detected - Game disabled');
    });
    
    testTim150Btn.addEventListener('click', function() {
        socket.emit('test_tim150_detected');
        console.log('Test: Right detected - Game disabled');
    });
    
    testClearBtn.addEventListener('click', function() {
        socket.emit('test_area_clear');
        console.log('Test: All areas clear - Game enabled');
    });
    
    console.log('PBT Sensor Monitor initialized');
});

// Request stats periodically
setInterval(() => {
    socket.emit('request_stats');
}, 5000);

