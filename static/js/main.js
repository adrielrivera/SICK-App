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

// Safety banner updater (single ANY-person state)
function updateSafetyBanner(enabled) {
    const banner = document.getElementById('safetyBanner');
    const text = document.getElementById('safetyText');
    if (enabled) {
        banner.classList.remove('danger');
        banner.classList.add('safe');
        text.textContent = 'AREA CLEAR';
    } else {
        banner.classList.remove('safe');
        banner.classList.add('danger');
        text.textContent = 'PERSON DETECTED – SCORING DISABLED';
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
    console.log('🔔 Received safety_status:', data);
    gameEnabled = !!data.game_enabled;
    updateSafetyBanner(gameEnabled);
});

// PBT hit event handler - display ADC value for each hit
socket.on('pbt_hit', (data) => {
    console.log(`PBT Hit #${data.hit_number}: ADC=${data.adc_value}, Pulse=${data.pulse_width_ms}ms`);
    addHitToDisplay(data);
});

// Store recent hits (last 10)
let recentHits = [];
const MAX_HITS_DISPLAY = 10;

function addHitToDisplay(hitData) {
    recentHits.unshift(hitData);
    if (recentHits.length > MAX_HITS_DISPLAY) {
        recentHits.pop();
    }
    updateHitDisplay();
}

function updateHitDisplay() {
    const container = document.getElementById('hit-history');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (recentHits.length === 0) {
        container.innerHTML = '<div class="no-hits">No hits yet</div>';
        return;
    }
    
    recentHits.forEach((hit, index) => {
        const hitElement = document.createElement('div');
        hitElement.className = 'hit-item';
        hitElement.innerHTML = `
            <span class="hit-number">#${hit.hit_number}</span>
            <span class="hit-adc">ADC: ${hit.adc_value}</span>
            <span class="hit-pulse">${hit.pulse_width_ms}ms</span>
        `;
        container.appendChild(hitElement);
    });
}

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
    
    console.log('PBT Sensor Monitor initialized');
});

// Request stats periodically
setInterval(() => {
    socket.emit('request_stats');
}, 5000);

