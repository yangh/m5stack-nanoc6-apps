#!/usr/bin/env python3

import serial
import subprocess
import os
import pwd
import argparse
from datetime import datetime
import time

args = None

# --- Functions ---

def auto_set_display():
    if 'DISPLAY' not in os.environ:
        try:
            # Try to find the X socket
            displays = os.listdir('/tmp/.X11-unix/')
            if displays:
                # Take the last one (e.g., 'X1' -> ':1')
                display_num = displays[-1].replace('X', ':')
                os.environ['DISPLAY'] = display_num
                return display_num
        except Exception:
            os.environ['DISPLAY'] = ":0" # Fallback

    return os.environ.get('DISPLAY')

def get_active_graphical_session():
    """Finds the Session ID that is both graphical and active."""
    try:
        # Get list of all sessions
        output = subprocess.check_output(['loginctl', 'list-sessions', '--no-legend']).decode()
        for line in output.splitlines():
            parts = line.split()
            if not parts: continue
            sid = parts[0]

            # Check properties of each session
            info = subprocess.check_output(['loginctl', 'show-session', sid]).decode()
            is_graphical = "Type=wayland" in info or "Type=x11" in info
            is_active = "Active=yes" in info

            if is_graphical and is_active:
                return sid
    except Exception as e:
        log_event(f"Failed to probe sessions: {e}")
    return "auto" # Fallback to auto if discovery fails

def setup_env():
    # Get current user's UID and username
    uid = os.getuid()
    username = pwd.getpwuid(uid).pw_name

    # Dynamically set environment variables if they are missing
    if 'XDG_RUNTIME_DIR' not in os.environ:
        os.environ['XDG_RUNTIME_DIR'] = f"/run/user/{uid}"

    if 'DBUS_SESSION_BUS_ADDRESS' not in os.environ:
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = f"unix:path=/run/user/{uid}/bus"

    auto_set_display()

    important_envs = ['USER', 'DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS']
    log_debug(f"Dump environment")
    for key in sorted(os.environ.keys()):
        if key in important_envs:
            log_debug(f"{key}= {os.environ[key]}")

def log_debug(message, debug = False):
    """
    Log events with a human-readable timestamp.
    """
    if debug or args.debug:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if args.debug:
            print(f"[{timestamp}] {message}")
        else:
            print(f"{message}")

def log_event(message):
    """
    Log events with a human-readable timestamp.
    """
    log_debug(message, True)

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
    subprocess.run([
        'gdbus', 'call', '--session',
        '--dest', 'org.gnome.ScreenSaver',
        '--object-path', '/org/gnome/ScreenSaver',
        '--method', 'org.gnome.ScreenSaver.SetActive', 'true'
    ])

    # Step 2: Unlock the session
    # Get the specific session ID for the user
    session_id = get_active_graphical_session()
    log_event(f"Unlock session: {session_id}")
    subprocess.run(['loginctl', 'unlock-session', session_id])

    # 3. CRITICAL: Reset the idle timer to prevent immediate re-blanking
    # This simulates user activity via D-Bus
    subprocess.run([
        'gdbus', 'call', '--session',
        '--dest', 'org.gnome.Mutter.IdleMonitor',
        '--object-path', '/org/gnome/Mutter/IdleMonitor/Core',
        '--method', 'org.gnome.Mutter.IdleMonitor.ResetIdletime'
    ])

def get_uid_from_file():
    """
    Reads the authorized UID from ~/.nfc_uid.
    Returns the cleaned UID string or None if failed.
    """
    # Expand ~ to the full home directory path
    file_path = os.path.expanduser("~/.nfc_uid")

    if not os.path.exists(file_path):
        log_event(f"Error: Config file {file_path} not found.")
        return None

    try:
        with open(file_path, 'r') as f:
            # Read, remove whitespace/newlines, and convert to lowercase
            uid = f.read().strip().replace(" ", "").lower()
            if not uid:
                log_event("Error: ~/.nfc_uid is empty.")
                return None
            return uid
    except Exception as e:
        log_event(f"Error reading ~/.nfc_uid: {e}")
        return None

def main():
    global args

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="RFID Screen Lock/Unlock Toggle Tool")
    parser.add_argument('--uid', type=str, default='', help="The authorized Card UID (e.g., '20 2b 01 2b')")
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument('--baud', type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument('--dry-run', action='store_true', default=False, help="Dry run")
    parser.add_argument('--debug', action='store_true', default=False, help="Debug")

    args = parser.parse_args()

    setup_env()

    uid = args.uid
    if not uid or len(uid) == 0:
        uid = os.getenv("NFC_UID")

    if not uid or len(uid) == 0:
        uid = get_uid_from_file()

    if not uid or len(uid) == 0:
        log_event(f"NFC UID not speicified")

    # Normalize the provided UID (remove spaces and lowercase)
    authorized_uid = uid.replace(" ", "").lower()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        log_event(f"Service started. Listening on {args.port}")
        log_debug(f"Authorized UID (hex): {authorized_uid}")

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                log_debug(f"Serial: {line}")

                if args.dry_run:
                    continue

                if "Card UID:" in line:
                    # Extract and normalize scanned UID
                    scanned_uid_raw = line.split("Card UID:")[1].strip()
                    scanned_uid = scanned_uid_raw.replace(" ", "").lower()
                    log_debug(f"Scanned: {scanned_uid_raw}")

                    if scanned_uid == authorized_uid:
                        if is_screen_locked():
                            unlock_screen()
                        else:
                            lock_screen()
                    else:
                        log_event("Access Denied: Unauthorized card.")
            else:
                # Prevent busy-waiting when no data available
                time.sleep(0.1)

    except KeyboardInterrupt:
        log_event("Service stopped.")
    except Exception as e:
        log_event(f"Critical error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    main()
