# Proportional PBT Scoring System

## Overview
The PBT scoring system has been updated to provide more proportional and fair scoring across the entire peak range.

## Changes Made

### 1. Expanded Peak Range
- **Old Range**: 24-60 ADC (very narrow)
- **New Range**: 30-100 ADC (much wider)
- **Result**: More granular scoring across peak values

### 2. Proportional Arcade Scoring
- **Peak 30 ADC** → **100 points** (minimum score)
- **Peak 50 ADC** → **300 points** (mid-range)
- **Peak 70 ADC** → **400 points** (good hit)
- **Peak 90 ADC** → **450 points** (excellent hit)
- **Peak 100 ADC** → **500 points** (maximum score)

### 3. Improved Threshold
- **Old Threshold**: 24 ADC
- **New Threshold**: 30 ADC
- **Result**: Better sensitivity and fewer false triggers

## Scoring Formula

### Arcade Score Calculation
```python
def calculate_arcade_score(peak):
    # Map peak (30-100 ADC) to score (100-500 points)
    # Higher peak = shorter pulse = higher score
    score = int(map_linear_inverse(peak, 30, 100, 100, 500))
    return max(100, min(500, score))  # Clamp to 100-500 range
```

### Pulse Width Calculation
```python
def calculate_pulse_width(peak):
    # Map peak (30-100 ADC) to pulse width (10-100ms)
    # Higher peak = shorter pulse = higher score
    width_ms = clamp(
        map_linear_inverse(peak, 30, 100, 10, 100),
        10, 100
    )
    return width_ms
```

## Expected Results

### Before (Old System)
- 30 ADC → 140 points
- 40 ADC → 140 points  
- 50 ADC → 140 points
- 60 ADC → 400 points (huge jump!)
- 70 ADC → 470 points
- 80 ADC → 475 points
- 90 ADC → 500 points

### After (New System)
- 30 ADC → 100 points
- 40 ADC → 200 points
- 50 ADC → 300 points
- 60 ADC → 350 points
- 70 ADC → 400 points
- 80 ADC → 450 points
- 90 ADC → 475 points
- 100 ADC → 500 points

## Benefits

1. **Proportional Scoring**: Each ADC increase gives a proportional score increase
2. **Fair Competition**: Players can see gradual improvement
3. **Better Sensitivity**: 30 ADC threshold catches more hits
4. **Wider Range**: 30-100 ADC covers more realistic peak values
5. **Smooth Progression**: No more sudden jumps in scoring

## Files Updated

- `pbt_tester.py` - Added proportional scoring functions
- `app_combined.py` - Updated peak range parameters
- `templates/pbt_tester.html` - Updated UI ranges and test values
- `config.py` - Updated trigger threshold

## Testing

Use the PBT tester to verify the new scoring:
1. Run `./start_tester.sh`
2. Open `http://localhost:5002`
3. Test different peak values (30-100 ADC)
4. Verify proportional scoring in results

The new system provides much more fair and proportional scoring across all peak values!
