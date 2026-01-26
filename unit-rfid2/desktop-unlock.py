#!/usr/bin/env python3

import serial
import subprocess
import os
import argparse
from datetime import datetime

# --- Functions ---

def log_event(message):
    """
    Log events with a human-readable timestamp.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def execute_cmd(cmd):
    subprocess.run(cmd,
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

def is_screen_locked():
    """
    Check if the GNOME screensaver is currently active via D-Bus.
    """
    try:
        output = subprocess.check_output([
            'gdbus', 'call', '--session',
            '--dest', 'org.gnome.ScreenSaver',
            '--object-path', '/org/gnome/ScreenSaver',
            '--method', 'org.gnome.ScreenSaver.GetActive'
        ]).decode('utf-8')
        return 'true' in output.lower()
    except Exception as e:
        log_event(f"Error checking screen status: {e}")
        return False

def lock_screen():
    log_event("Action: Locking screen.")
    subprocess.run(['xdg-screensaver', 'lock'])

def unlock_screen():
    log_event("Action: Waking up and unlocking screen.")
    # Step 1: Wake up the display
    execute_cmd([
        'gdbus', 'call', '--session',
        '--dest', 'org.gnome.ScreenSaver',
        '--object-path', '/org/gnome/ScreenSaver',
        '--method', 'org.gnome.ScreenSaver.SetActive', 'true'
    ])
    # Step 2: Unlock the session
    subprocess.run(['loginctl', 'unlock-session'])

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="RFID Screen Lock/Unlock Toggle Tool")
    parser.add_argument('--uid', type=str, default='', help="The authorized Card UID (e.g., '04 ab 12 cd')")
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument('--baud', type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument('--dry-run', action='store_true', default=False, help="Dry run")

    args = parser.parse_args()

    uid = args.uid
    if not uid or len(uid) == 0:
        uid = os.getenv("NFC_UID")

    if not uid or len(uid) == 0:
        log_event(f"NFC UID not speicified")

    # Normalize the provided UID (remove spaces and lowercase)
    authorized_uid = uid.replace(" ", "").lower()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        log_event(f"Service started. Listening on {args.port}")
        log_event(f"Authorized UID (hex): {authorized_uid}")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                log_event(f"Serial: {line}")

                if args.dry_run:
                    continue

                if "Card UID:" in line:
                    # Extract and normalize scanned UID
                    scanned_uid_raw = line.split("Card UID:")[1].strip()
                    scanned_uid = scanned_uid_raw.replace(" ", "").lower()

                    log_event(f"Scanned: {scanned_uid_raw}")

                    if scanned_uid == authorized_uid:
                        if is_screen_locked():
                            unlock_screen()
                        else:
                            lock_screen()
                    else:
                        log_event("Access Denied: Unauthorized card.")

    except KeyboardInterrupt:
        log_event("Service stopped.")
    except Exception as e:
        log_event(f"Critical error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    main()
