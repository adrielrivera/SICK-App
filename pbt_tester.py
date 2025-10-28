#!/usr/bin/env python3
"""
PBT Scoring System Tester
Allows testing different peak values without Arduino
Test the scoring system with fake peak inputs
"""
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Same scoring logic as app_combined.py
A_MIN, A_MAX = 24, 60
W_MIN_MS, W_MAX_MS = 10, 100
TRIGGER_THRESHOLD = 24

def clamp(x, lo, hi):
    """Clamp value between min and max."""
    return max(lo, min(hi, x))

def map_linear_inverse(x, x0, x1, y0, y1):
    """Map value from one range to another INVERSELY (high x → low y)."""
    if x1 <= x0:
        return y1
    t = (x - x0) / (x1 - x0)
    return y1 - t * (y1 - y0)  # Inverted: subtract instead of add

def calculate_pulse_width(peak):
    """Calculate pulse width from peak value using the same logic as app_combined.py."""
    a_clamped = clamp(peak, A_MIN, A_MAX)
    width_ms = clamp(
        map_linear_inverse(a_clamped, A_MIN, A_MAX, W_MIN_MS, W_MAX_MS),
        W_MIN_MS, W_MAX_MS
    )
    return width_ms

def get_score_level(pulse_width):
    """Determine score level based on pulse width."""
    if pulse_width < 20:
        return "HIGH SCORE (Short pulse - Quick hit)"
    elif pulse_width < 50:
        return "MEDIUM SCORE (Medium pulse)"
    else:
        return "LOW SCORE (Long pulse - Slow hit)"

# Web interface for testing
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pbt-tester-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    """PBT testing interface."""
    return render_template('pbt_tester.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('PBT Tester: Client connected')
    
    # Send initial configuration
    emit('config', {
        'trigger_threshold': TRIGGER_THRESHOLD,
        'peak_range': f"{A_MIN}-{A_MAX}",
        'pulse_range': f"{W_MIN_MS}-{W_MAX_MS}ms",
        'mapping': "INVERTED (High peak → Short pulse)"
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('PBT Tester: Client disconnected')

@socketio.on('test_peak')
def handle_test_peak(data):
    """Test a single peak value."""
    try:
        peak = float(data['peak'])
        
        # Calculate pulse width
        pulse_width = calculate_pulse_width(peak)
        
        # Determine if it would trigger
        triggered = peak >= TRIGGER_THRESHOLD
        
        # Get score level
        score_level = get_score_level(pulse_width) if triggered else "NO SCORE (Below threshold)"
        
        # Send results back
        emit('peak_result', {
            'peak': peak,
            'pulse_width': pulse_width,
            'triggered': triggered,
            'threshold': TRIGGER_THRESHOLD,
            'score_level': score_level,
            'range': f"{A_MIN}-{A_MAX} → {W_MIN_MS}-{W_MAX_MS}ms"
        })
        
        print(f"Test Peak: {peak:.1f} → Pulse: {pulse_width:.0f}ms {'(TRIGGERED)' if triggered else '(Below threshold)'}")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid peak value: {e}'})

@socketio.on('test_range')
def handle_test_range(data):
    """Test a range of peak values."""
    try:
        start = float(data.get('start', A_MIN))
        end = float(data.get('end', A_MAX))
        step = float(data.get('step', 2.0))
        
        results = []
        current = start
        while current <= end:
            pulse_width = calculate_pulse_width(current)
            triggered = current >= TRIGGER_THRESHOLD
            score_level = get_score_level(pulse_width) if triggered else "NO SCORE"
            
            results.append({
                'peak': current,
                'pulse_width': pulse_width,
                'triggered': triggered,
                'score_level': score_level
            })
            current += step
        
        emit('range_result', {
            'results': results,
            'start': start,
            'end': end,
            'step': step
        })
        
        print(f"Range test: {start}-{end} (step {step}) - {len(results)} values tested")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid range parameters: {e}'})

@socketio.on('test_specific')
def handle_test_specific(data):
    """Test specific peak values."""
    try:
        values = data.get('values', [20, 24, 30, 35, 40, 45, 50, 55, 60, 65, 70])
        
        results = []
        for peak in values:
            pulse_width = calculate_pulse_width(peak)
            triggered = peak >= TRIGGER_THRESHOLD
            score_level = get_score_level(pulse_width) if triggered else "NO SCORE"
            
            results.append({
                'peak': peak,
                'pulse_width': pulse_width,
                'triggered': triggered,
                'score_level': score_level
            })
        
        emit('specific_result', {
            'results': results,
            'values': values
        })
        
        print(f"Specific test: {len(values)} values tested")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid specific values: {e}'})

@socketio.on('simulate_hit')
def handle_simulate_hit(data):
    """Simulate a complete PBT hit sequence."""
    try:
        peak = float(data['peak'])
        
        if peak < TRIGGER_THRESHOLD:
            emit('simulation_result', {
                'success': False,
                'message': f'Peak {peak:.1f} below threshold {TRIGGER_THRESHOLD} - No hit detected'
            })
            return
        
        # Calculate pulse width
        pulse_width = calculate_pulse_width(peak)
        score_level = get_score_level(pulse_width)
        
        # Simulate the complete sequence
        emit('simulation_result', {
            'success': True,
            'peak': peak,
            'pulse_width': pulse_width,
            'score_level': score_level,
            'sequence': [
                f"1. Peak detected: {peak:.1f} ADC counts",
                f"2. Above threshold: {TRIGGER_THRESHOLD} ✓",
                f"3. Pulse width calculated: {pulse_width:.1f}ms",
                f"4. Arcade button press: {pulse_width:.1f}ms duration",
                f"5. Score level: {score_level}",
                f"6. PBT_HIT sent to Arduino",
                f"7. Credit tracking updated"
            ]
        })
        
        print(f"Simulation: Peak {peak:.1f} → {pulse_width:.1f}ms pulse → {score_level}")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid simulation parameters: {e}'})

if __name__ == '__main__':
    print("=" * 60)
    print("SICK7 PBT Scoring System Tester")
    print("=" * 60)
    print(f"Trigger Threshold: {TRIGGER_THRESHOLD} ADC counts")
    print(f"Peak Range: {A_MIN}-{A_MAX} ADC counts")
    print(f"Pulse Range: {W_MIN_MS}-{W_MAX_MS} ms")
    print(f"Mapping: INVERTED (High peak → Short pulse)")
    print(f"Web interface: http://localhost:5002")
    print("=" * 60)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nShutting down PBT Tester...")
    except Exception as e:
        print(f"Error starting PBT Tester: {e}")
