#!/bin/bash

sudo a2dissite mycelium-gui.conf > /dev/null 2>&1
sudo systemctl reload apache2
