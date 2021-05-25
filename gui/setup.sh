#!/bin/bash

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

sudo apt-get install -y apache2
sudo apt-get install -y libapache2-mod-wsgi-py3
pip3 install flask

#####

FILE="wsgi.py"
echo "Writing $FILE"
/bin/cat <<EOM >$FILE
# Set MAVLink protocol to 2.
import os
os.environ["MAVLINK20"] = "1"
os.environ["MYCELIUM_ROOT"] = "$MYCELIUM_ROOT"
os.environ["MYCELIUM_CFG_ROOT"] = "$MYCELIUM_CFG_ROOT"
os.environ["MYCELIUM_GUI_ROOT"] = "$MYCELIUM_GUI_ROOT"

from app import app as application
EOM

FILE="mycelium-gui.conf"
echo "Writing $FILE"
/bin/cat <<EOM >$FILE
Listen 8080
<VirtualHost *:8080>
    ServerName 127.0.0.1

    WSGIDaemonProcess mycelium python-path=$PWD:$PYTHONPATH user=$USER
    WSGIScriptAlias / $PWD/wsgi.py

    <Directory $PWD>
        WSGIProcessGroup mycelium
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
</VirtualHost>
EOM


sudo cp $FILE /etc/apache2/sites-available
sudo a2ensite mycelium-gui.conf > /dev/null 2>&1
sudo a2enmod wsgi > /dev/null 2>&1
sudo systemctl reload apache2

echo "Setup complete!"