#!/bin/bash
# Clean up Arduino files to prevent compilation conflicts

echo "=========================================="
echo "Cleaning up Arduino files"
echo "=========================================="

# Remove any old .ino files except our unified one
echo "Removing old Arduino files..."
rm -f SICK-App.ino
rm -f arduino_pbt_simulator.ino
rm -f signal_simulator.ino

# List remaining .ino files
echo "Remaining Arduino files:"
ls -la *.ino 2>/dev/null || echo "No .ino files found"

echo "=========================================="
echo "Cleanup complete!"
echo "Only unified_pbt_lidar.ino should remain"
echo "=========================================="
