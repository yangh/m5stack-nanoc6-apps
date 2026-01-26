sudo cp rfid-unlock.service /etc/systemd/system/rfid-unlock.service
sudo systemctl daemon-reload
sudo systemctl enable rfid-unlock.service
sudo systemctl stop rfid-unlock.service
sudo systemctl start rfid-unlock.service
sudo systemctl status -l rfid-unlock.service
