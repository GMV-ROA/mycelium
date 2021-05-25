#!/bin/bash

PARENTDIR="$(dirname `pwd`)"
if [[ $PYTHONPATH != *$PARENTDIR* ]]; then
    echo "export PYTHONPATH=\$PYTHONPATH:$PARENTDIR" >> ~/.bashrc
    source ~/.bashrc
fi

if [[ $PYTHONPATH != *$PWD* ]]; then
    echo "export PYTHONPATH=\$PYTHONPATH:$PWD" >> ~/.bashrc
    source ~/.bashrc
fi

if [[ -z $PICAMERA_ROOT ]]; then
    echo "export PICAMERA_ROOT=$PWD" >> ~/.bashrc
    source ~/.bashrc
fi

echo "Installing python modules"
pip3 install picamera
pip3 install dronekit
pip3 install gpiozero
pip3 install bh1745
pip3 install pyyaml
pip3 install cv
pip3 install pigpio
echo "Installation complete"

#####

FILE="picamera.service"
echo "Writing $FILE"
/bin/cat <<EOM >$FILE
[Unit]
Description=Run picamera
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$USER
ExecStart=/usr/bin/env python3 $PWD/scripts/mission_capture.py

[Install]
WantedBy = multi-user.target
EOM

sudo cp $FILE /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

echo "Setup complete!"