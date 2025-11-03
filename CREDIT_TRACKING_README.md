# Credit Tracking System Documentation

## Overview

The credit tracking system adds a pay-to-play mechanism to the SICK7 PBT arcade system. Credits are deducted based on PBT hits, and LiDAR safety monitoring is disabled when no credits are available.

## Key Features

- **Credit Deduction**: 2 PBT hits = 1 credit deducted
- **LiDAR Override**: When `credits == 0`, LiDAR detections do NOT disable the game or trigger alarms
- **Credit Management**: Admin controls via webapp to set/add credits
- **Real-time Updates**: Credit status updates in real-time via WebSocket

## System Architecture

### Components

1. **Arduino (`pbt_with_credits.ino`)**: Tracks credits and PBT hits
   - Located: `/SICK-Capstone/SICK-Capstone/arduino_stuff/pbt_with_credits/`
   - Port: `/dev/ttyUSB0` (PBT Arduino)
   - Commands: `PBT_HIT`, `GET_CREDITS`, `SET_CREDITS:<n>`, `ADD_CREDITS:<n>`

2. **Raspberry Pi (`app_with_credits.py`)**: Webapp and game logic
   - Located: `/SICK7/SICK-App/app_with_credits.py`
   - Port: `5000` (default)
   - WebSocket events: `credit_status`, `set_credits`, `add_credits`

3. **Web Interface (`index_with_credits.html`)**: Credit display and controls
   - Located: `/SICK7/SICK-App/templates/index_with_credits.html`
   - Features: Credit display, admin controls, visual feedback

### Credit Flow

```
Player hits PBT → Pi detects peak → Pi sends PBT_HIT to Arduino
↓
Arduino counts hit (2 hits needed)
↓
Arduino deducts 1 credit → Arduino sends CREDITS:<n> to Pi
↓
Pi updates credits → Pi emits credit_status to webapp
↓
Webapp displays updated credit count
```

## Installation

### 1. Upload Arduino Code

```bash
cd /path/to/SICK-Capstone/SICK-Capstone/arduino_stuff/pbt_with_credits
./upload.sh
```

This uploads the credit tracking Arduino code to the PBT Arduino at `/dev/ttyUSB0`.

### 2. Start Pi Application

```bash
cd /path/to/SICK7/SICK-App
./start_with_credits.sh
```

The webapp will be available at `http://raspberry-pi-ip:5000`

## Usage

### Adding Credits (Admin)

1. Open the webapp in a browser
2. In the credit card section, enter a number in "Set" or "Add" field
3. Click "Set Credits" or "Add Credits"
4. Credits update immediately on all connected clients

### Credit Deduction

- Every **2 PBT hits** automatically deducts **1 credit**
- Credits cannot go negative (minimum is 0)
- When credits reach 0, LiDAR safety is disabled

### LiDAR Safety Behavior

- **Credits > 0**: Normal LiDAR safety (person detection disables game)
- **Credits == 0**: LiDAR safety **DISABLED** (allows play without credits)

This design allows testing and play when no credits are available, while maintaining safety during actual gameplay.

## Arduino Commands

### From Pi to Arduino

- `PBT_HIT`: Notify Arduino of a PBT hit (auto-sent by Pi)
- `GET_CREDITS`: Request current credit count
- `SET_CREDITS:<n>`: Set credits directly (e.g., `SET_CREDITS:10`)
- `ADD_CREDITS:<n>`: Add credits (e.g., `ADD_CREDITS:5`)

### From Arduino to Pi

- `CREDITS:<n>`: Current credit count (e.g., `CREDITS:5`)
- `CREDIT_PROGRESS:<n>/2`: Progress toward next deduction (e.g., `CREDIT_PROGRESS:1/2`)

## WebSocket Events

### Client → Server

- `set_credits`: `{ credits: <number> }` - Set credits directly
- `add_credits`: `{ credits: <number> }` - Add credits
- `request_credits`: Request current credit status

### Server → Client

- `credit_status`: `{ credits: <number>, changed: <boolean> }` - Credit update

## Code Files

### Arduino
- `/SICK-Capstone/SICK-Capstone/arduino_stuff/pbt_with_credits/pbt_with_credits.ino`
- `/SICK-Capstone/SICK-Capstone/arduino_stuff/pbt_with_credits/upload.sh`

### Raspberry Pi
- `/SICK7/SICK-App/app_with_credits.py`
- `/SICK7/SICK-App/templates/index_with_credits.html`
- `/SICK7/SICK-App/start_with_credits.sh`

## Differences from Base System

### Key Changes

1. **Credit Tracking Variables**
   - Added `credits` and `credits_lock` for thread-safe credit access
   - Credits tracked from Arduino via `CREDITS:` messages

2. **Modified `get_combined_lidar_status()`**
   - Returns `SAFE` when `credits == 0` (overrides LiDAR detection)
   - Normal LiDAR logic when `credits > 0`

3. **Modified Pulse Generation**
   - Checks `credits > 0` before generating pulses
   - No pulses generated when credits == 0

4. **WebSocket Handlers**
   - `set_credits`: Admin command to set credits
   - `add_credits`: Admin command to add credits
   - `request_credits`: Client request for credit status

5. **Credit Display UI**
   - Large credit counter with visual feedback
   - Admin input controls for setting/adding credits
   - Color changes when credits reach 0

## Troubleshooting

### Credits Not Updating

1. Check Arduino connection: `ls /dev/ttyUSB0`
2. Check Arduino is running `pbt_with_credits.ino`
3. Monitor serial output: `screen /dev/ttyUSB0 115200`
4. Look for `CREDITS:` messages in Pi console

### Credits Don't Deduct

1. Verify Pi is sending `PBT_HIT` after each pulse
2. Check Arduino is counting hits (should see `PBT_HIT received` messages)
3. Verify `HITS_PER_CREDIT = 2` in Arduino code

### LiDAR Still Disabling Game at 0 Credits

1. Verify `get_combined_lidar_status()` checks `credits == 0`
2. Check credit variable is updating correctly
3. Monitor console for "Credits updated" messages

## Testing

### Manual Credit Test

1. Start system: `./start_with_credits.sh`
2. Open webapp
3. Set credits to 5 via web interface
4. Make 10 PBT hits (should deduct 5 credits, leaving 0)
5. Verify credits reach 0
6. Verify LiDAR safety is disabled (try triggering LiDAR detection)

### Automated Test Sequence

1. Set credits: 5
2. Make 2 hits → Should deduct 1 credit (now 4)
3. Make 2 more hits → Should deduct 1 credit (now 3)
4. Make 10 more hits → Should deduct 5 credits (now 0)
5. Verify game continues even with LiDAR detection (when credits == 0)

## Notes

- Credits start at 0 by default
- Credits cannot go negative
- Credit count is not persisted (resets on restart)
- Admin controls are accessible to anyone on the webapp (no authentication)

For production, consider adding:
- Authentication for credit management
- Credit persistence (database/file)
- Credit purchase system (coin acceptor, payment gateway, etc.)

