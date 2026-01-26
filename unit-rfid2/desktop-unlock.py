#!/usr/bin/env python3

import serial
import subprocess
import os

# Configuration
# Replace with your NanoC6 port (check with ls /dev/ttyACM*)
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200
# Replace with your actual Card UID (lowercase)
AUTHORIZED_UID = 'EC A6 0D 48' 

def unlock_screen():
    """
    Attempts to unlock the GNOME screen saver for the current user.
    """
    print("Authorized UID detected. Unlocking...")
    # For GNOME on Ubuntu 24.04
    subprocess.run(['loginctl', 'unlock-session'])

def main():
    try:
        # Open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Listening for RFID cards on {SERIAL_PORT}...")

        while True:
            if ser.in_waiting > 0:
                # Read line and strip whitespace
                line = ser.readline().decode('utf-8').strip()
                print(line);
                
                if "Card UID:" in line:
                    # Extract the hex UID part
                    scanned_uid = line.split(":")[1].strip()
                    print(f"Scanned: {scanned_uid}")

                    if scanned_uid == AUTHORIZED_UID:
                        unlock_screen()
                    else:
                        print("Access Denied: Unknown UID")
                        
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    main()
