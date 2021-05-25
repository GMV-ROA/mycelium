#!/bin/bash

if [[ $PYTHONPATH != *pyrealsense* ]]; then
    PYREALSENSE="/usr/lib/python3/dist-packages/pyrealsense2"
    echo "export PYTHONPATH=\$PYTHONPATH:$PYREALSENSE" >> ~/.bashrc
    source ~/.bashrc
fi

if [[ $PYTHONPATH != *$PWD* ]]; then
    echo "export PYTHONPATH=\$PYTHONPATH:$PWD" >> ~/.bashrc
    source ~/.bashrc
fi

if [ -z $MAVLINK20 ]; then
    echo "export MAVLINK20=1" >> ~/.bashrc
    source ~/.bashrc
fi

echo "Setting up mycelium vars"

if [[ -z $MYCELIUM_ROOT ]]; then
    echo "export MYCELIUM_ROOT=$PWD" >> ~/.bashrc
    source ~/.bashrc
fi

if [[ -z $MYCELIUM_CFG_ROOT ]]; then
    echo "export MYCELIUM_CFG_ROOT=$MYCELIUM_ROOT/cfg" >> ~/.bashrc
    source ~/.bashrc
fi

if [[ -z $MYCELIUM_GUI_ROOT ]]; then
    echo "export MYCELIUM_GUI_ROOT=$PWD" >> ~/.bashrc
    source ~/.bashrc
fi

#####

echo "Installing requirements"

sudo apt-get install -y python3-pip 
pip3 install pymavlink  
pip3 install PyYAML  
pip3 install transformations  
sudo apt-get install -y redis  
pip3 install redis  
pip3 install apscheduler
pip3 install dronekit

#####

ENV_FILE="env_file.conf"
echo "Writing $ENV_FILE"
/bin/cat <<EOM >$ENV_FILE
PYTHONPATH=$PYTHONPATH
MYCELIUM_ROOT=$MYCELIUM_ROOT
MYCELIUM_GUI_ROOT=$MYCELIUM_GUI_ROOT
MYCELIUM_CFG_ROOT=$MYCELIUM_CFG_ROOT
MAVLINK20=$MAVLINK20
EOM
sudo mkdir -p /etc/mycelium
sudo cp $ENV_FILE /etc/mycelium

sudo rm -r services
mkdir -p services
FILE="mycelium-t265.service"
echo "Writing $FILE"
/bin/cat <<EOM >services/$FILE
[Unit]
Description=Run t265 camera
After=redis.service
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$USER
EnvironmentFile=/etc/mycelium/$ENV_FILE
ExecStart=/usr/bin/env python3 $PWD/scripts/run_t265.py

[Install]
WantedBy = multi-user.target
EOM

FILE="mycelium-d435.service"
echo "Writing $FILE"
/bin/cat <<EOM >services/$FILE
[Unit]
Description=Run d435 camera
After=redis.service
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$USER
EnvironmentFile=/etc/mycelium/$ENV_FILE
ExecStart=/usr/bin/env python3 $PWD/scripts/run_d435.py

[Install]
WantedBy = multi-user.target
EOM

FILE="mycelium-redis-to-ap.service"
echo "Writing $FILE"
/bin/cat <<EOM >services/$FILE
[Unit]
Description=Send instrument data from redis to ArduPilot
Requires=redis.service
Requires=mavlink-router.service
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$USER
EnvironmentFile=/etc/mycelium/$ENV_FILE
ExecStart=/usr/bin/env python3 $PWD/redis_scripts/redis_to_ap.py

[Install]
WantedBy = multi-user.target
EOM

FILE="mycelium-ap-to-redis.service"
echo "Writing $FILE"
/bin/cat <<EOM >services/$FILE
[Unit]
Description=Get parameters from ArduPilot and save to redis
Requires=redis.service
Requires=mavlink-router.service
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$USER
EnvironmentFile=/etc/mycelium/$ENV_FILE
ExecStart=/usr/bin/env python3 $PWD/redis_scripts/ap_to_redis.py

[Install]
WantedBy = multi-user.target
EOM

SUDO_FILE="/etc/sudoers.d/mycelium"
sudo rm $SUDO_FILE 2> /dev/null
echo "Adding user sudo permissions"
R1="$USER ALL=NOPASSWD: /bin/systemctl * mavlink-router.service"
R2="$USER ALL=NOPASSWD: /bin/systemctl * redis.service"
R3="$USER ALL=NOPASSWD: /bin/systemctl * mycelium-*"
R4="$USER ALL=NOPASSWD: /bin/journalctl -u mavlink-router.service"
R5="$USER ALL=NOPASSWD: /bin/journalctl -u mavlink-router.service -n *"
R6="$USER ALL=NOPASSWD: /bin/journalctl -u redis.service"
R7="$USER ALL=NOPASSWD: /bin/journalctl -u redis.service -n *"
R8="$USER ALL=NOPASSWD: /bin/journalctl -u mycelium-*"
R9="$USER ALL=NOPASSWD: /bin/journalctl -u mycelium-* -n *"
for i in {1..9}; do
    rule=R${i}
    echo "${!rule}" | sudo EDITOR='tee -a' visudo -f "$SUDO_FILE"
done

echo "Installing services"
sudo rm /etc/systemd/system/mycelium-* 2> /dev/null
sudo cp services/* /etc/systemd/system/
sudo systemctl daemon-reload

echo "Enabling camera services"
sudo systemctl enable mycelium-t265.service
sudo systemctl enable mycelium-d435.service

#####

echo "Generating mavlink router config"
sudo mkdir -p /etc/mavlink-router
python3 scripts/generate_mavlink_conf.py
sudo cp main.conf /etc/mavlink-router/
sudo systemctl restart mavlink-router.service

echo "Setup complete!"