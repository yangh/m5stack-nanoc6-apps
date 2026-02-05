rfid-unlock
-----------

Lock or Unlock your Ubuntu Desktop by an NFC card.

Environment
-----------

Ubuntu 24.04
1x M5Stack NanoC6
1x Unit RFID2

Interface:
  LED blue: standby
  LED green flashing: card read successed
  NanoC6 UART: /dev/ttyACM0

rfid-unlock.py
--------------

This the main program to run as a system service to monitor NFC scanner.

./rfid-unlock.py --help
usage: rfid-unlock.py [-h] [--uid UID] [--port PORT] [--baud BAUD] [--dry-run] [--debug]

RFID Screen Lock/Unlock Toggle Tool

options:
  -h, --help   show this help message and exit
  --uid UID    The authorized Card UID (e.g., '20 2b 01 2b')
  --port PORT  Serial port (default: /dev/ttyACM0)
  --baud BAUD  Baud rate (default: 115200)
  --dry-run    Dry run
  --debug      Debug info

Usage
-----

0. Connect M5Stack NanoC6 and Unit RFID2 to your computer.

  PC <==USB-C== [NanoC6] <== Grov == [Unit RFID2]

  Load the unit-rfid2.ino into NanoC6 with Arduino IDE, then close the IDE.

1. Checkout you NFC ID:
  > ./rfid-unlock.py --dry-run
  [2026-01-26 15:09:02] Serial: New RFID/NFC card found...
  [2026-01-26 15:09:02] Serial: PICC type: MIFARE 1KB
  [2026-01-26 15:09:02] Serial: Card UID: 20 2B 01 2B

2. Write NFC ID to ~/.nfc_uid
  > echo "20 2B 01 2B" > ~/.nfc_uid

3. Set User name in the rfid-unlock.service [IMPORTANT]
  [Service]
  User=nio

4. Specify serial port of NanoC6 in the rfid-unlock.service
  Find correct serial port device and set it into the ExecStart command.

5. Install rfid-unlock.service
  > ./install-service.sh

Others
------

1. Stop rfid-unlock.service
  You cann't run the rdif-unlock service and Ardunio IDE at the same time, due
  the both access the serail port of the NanoC6. So you can stop the service if
  you want to using IDE for development, and vice visa.

  > ./stop-service.sh

2. Check rfid logs
  > journalctl -f -u rfid-unlock.service

3. Serial port
  > ls -l /dev/serial/by-id/
  lrwxrwxrwx 1 root root 13  1 26 14:05 usb-Espressif_USB_JTAG_serial_debug_unit_9C:13:9E:D3:45:58-if00 -> ../../ttyACM0

Reference
---------

https://docs.m5stack.com/zh_CN/core/M5NanoC6
https://docs.m5stack.com/zh_CN/unit/rfid2

https://docs.m5stack.com/zh_CN/arduino/m5nanoc6/program
https://docs.m5stack.com/zh_CN/arduino/projects/unit/unit_rfid

Author
------

Walter H. YANG
