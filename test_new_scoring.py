#!/usr/bin/env python3
"""
Test script to verify the new 30-100 ADC → 40-10ms scoring system
"""

def clamp(x, lo, hi):
    """Clamp value between min and max."""
    return max(lo, min(hi, x))

def calculate_pulse_width(peak):
    """Calculate pulse width from peak value - map 30-100 ADC to 40-10ms."""
    A_MIN, A_MAX = 30, 100
    W_MIN_MS, W_MAX_MS = 10, 100
    
    a_clamped = clamp(peak, A_MIN, A_MAX)
    
    # Map 30-100 ADC to 40-10ms pulse width for better distribution
    # 30 ADC -> 40ms (good score)
    # 100 ADC -> 10ms (maximum score)
    # Linear mapping across the full range
    
    width_ms = 40 - (a_clamped - 30) * (30 / 70)  # 30->40ms, 100->10ms
    
    return clamp(width_ms, W_MIN_MS, W_MAX_MS)

def calculate_arcade_score_from_pulse_width(pulse_width_ms):
    """Calculate arcade score based on actual pulse width duration."""
    # Based on your observations with better distribution:
    # 100ms -> 140 score
    # 80ms  -> 200 score  
    # 60ms  -> 280 score
    # 40ms  -> 380 score
    # 20ms  -> 450 score
    # 10ms  -> 500 score
    
    if pulse_width_ms >= 100:
        return 140
    elif pulse_width_ms >= 80:
        # Linear interpolation: 100ms->140, 80ms->200
        return int(140 + (100 - pulse_width_ms) * (60 / 20))
    elif pulse_width_ms >= 60:
        # Linear interpolation: 80ms->200, 60ms->280
        return int(200 + (80 - pulse_width_ms) * (80 / 20))
    elif pulse_width_ms >= 40:
        # Linear interpolation: 60ms->280, 40ms->380
        return int(280 + (60 - pulse_width_ms) * (100 / 20))
    elif pulse_width_ms >= 20:
        # Linear interpolation: 40ms->380, 20ms->450
        return int(380 + (40 - pulse_width_ms) * (70 / 20))
    elif pulse_width_ms >= 10:
        # Linear interpolation: 20ms->450, 10ms->500
        return int(450 + (20 - pulse_width_ms) * (50 / 10))
    else:
        return 500  # Very short pulses get max score

def test_scoring():
    """Test the new scoring system with various peak values."""
    print("=" * 60)
    print("NEW SCORING SYSTEM TEST")
    print("30-100 ADC → 40-10ms → Arcade Score")
    print("=" * 60)
    
    test_values = [30, 40, 50, 60, 70, 80, 90, 100]
    
    for peak in test_values:
        pulse_width = calculate_pulse_width(peak)
        arcade_score = calculate_arcade_score_from_pulse_width(pulse_width)
        
        print(f"Peak: {peak:3d} ADC → {pulse_width:5.1f}ms → {arcade_score:3d} pts")
    
    print("=" * 60)
    print("Expected distribution:")
    print("- 30-50 ADC: Should give good scores (140-280 pts)")
    print("- 60-80 ADC: Should give medium scores (280-380 pts)")  
    print("- 90-100 ADC: Should give high scores (380-500 pts)")
    print("=" * 60)

if __name__ == "__main__":
    test_scoring()
