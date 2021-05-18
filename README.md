# mycelium
mycelium is a fast light weight in-memory data exchange for sensor information on-board a robot or between robots in large distributed and scalable swarms or systems.

mycelium is aimed at mobile robotics and embodied intelligence. You can think of mycelium as the robot's memory, both short term and long term. 
The goal of mycelium is to enable robots to learn from experiences during operation and improve over time, as well as allowing them to quickly simulate expected outcomes of actions on-board. 
Conceptually this is achived by creating a complete model (sensor, data, processed data, inputs and outputs) of the robot in-memory in a redis data-base allowing many subroutines to access this data-base and periodically saving snapshot of part or whole of the database on the hard drive (long term storage).
Long term storage can be analyised at any point to change subroutines effecting current in-memory storage.<br>

Currently mycleium enable easy interfacing between sensors and software components enabling a large number of different programming language to easily interact with the system data.
At this point it uses a ardupilot baed flight controller for guidance navigation and control. Overall the system has 2 key function: 1) Waypoint based navigation 2) Obstacle avoidance.
WP based navigation combines absolute localisation using GPS and relative localisation using Visual Odometry. Robustness and tolerance to failure (hardware, network, power) are important design considerations.
<br>

Camera scripts are based on scripts found on Ardupilto documentation:<br>
https://ardupilot.org/copter/docs/common-realsense-depth-camera.html<br>
https://ardupilot.org/copter/docs/common-vio-tracking-camera.html<br>

Cameras use the Intel REalsense SDK<br>

# Hardware

Tested on the following: 
"Flight Controller" Running Ardurover 4.0.0
Tested on the following computers: Ultra96-V2 (Zynq UltraScale+), NanoPi Neo3 2GB (FriendlyElec RK3328), NanoPi R4S (FriendlyElec RK3399), Raspberry Pi4 8GB, Raspberry Pi Zero, Beaglebone Blue, multiple x86 computers

<br>

# Installation

Clone the repository and install the following requirements:

#### To install pip3  
```
sudo apt-get install -y python3-pip 
```

#### Main requirements (automatically installed by Setup) 
```
pip3 install pymavlink  
pip3 install PyYAML  
pip3 install transformations  
sudo apt-get install -y redis  
pip3 install redis  
pip3 install apscheduler
pip3 install dronekit
```  
 
#### Setup

The ```setup.sh``` script will add the python mycelium module to path and install services for running scripts with systemd (note: pyrealsense2 must be added to the python path). It will also generate a mavlink router config file for connection endpoints. Before running the script, you should update the config file ```mycelium/cfg/default.yaml``` with the correct ArduPilot device port and connection baudrate.
<br>
Once updated, run:
```
chmod +x setup.sh
source setup.sh
```

<br>
<br>

# How to run

### Run automatically with services

Services generated with ```setup.sh``` script:
- mycelium-t265.service: starts the t265 camera (calls ```run_t265.py``` script)
- mycelium-d435.service: starts the d435 camera (calls ```run_d435.py``` script)
- mycelium-instrument-redis.service: sends instrument data from redis to ArduPilot (calls ```redis_to_ap.py``` script)
- mycelium-ap-redis.service: fetches ArduPilot parameters and saves to redis (calls ```ap_to_redis.py``` script)

<br>

These services will restart automatically upon failure and run continuously until stopped.<br>
You can start all services at once with script ```start_services.sh```<br>
You can also start services automatically on booting by enabling each service:<br>
```sudo systemctl enable [service]```

### Run manually with scripts

Start t265 camera<br>
```scripts/run_t265.py``` 
<br>
<br>

Start d435 camera<br>
```scripts/run_d435.py```
<br>
<br>

Send instrument data from redis to ArduPilot<br>
```redis_scripts/redis_to_ap.py```
<br>
<br>

Fetch ArduPilot parameters and save to redis<br>
```redis_scripts/ap_to_redis.py```
<br>
<br>

### Additional scripts

Sets the ekf source ([1] GPS only, [2] Visual odom only, [3] Fuse sources)<br>
```set_ekf_source.py --source [source]```
<br>
This option requires the following ArduPilot parameter setup (require version 4.1 or later, tested on Rover):
<br>
AHRS_EKF_TYPE = 3 (EKF3)
EK2_ENABLE = 0 (disabled)
EK3_ENABLE = 1 (enabled)
EK3_SRC1_POSXY = 6 (ExternalNav)
EK3_SRC1_VELXY = 6 (ExternalNav)
EK3_SRC1_POSZ = 1 (Baro which is safer because of the camera’s weakness to high vibrations)
EK3_SRC1_VELZ = 6 (ExternalNav)
GPS_TYPE = 0 to disable the GPS
VISO_TYPE = 2 (IntelT265)
RC7_OPTION = 80 (Viso Align) to allow the pilot to re-align the camera’s yaw with the AHRS/EKF yaw before flight with auxiliary switch 7. Re-aligning yaw before takeoff is a good idea or loss of position control (aka “toilet bowling”) may occur.

<br>
<br>
  
Switch LED lights on/off (State [0/1])<br>
```set_ekf_source.py --pin [relay pin] --state [state]```
<br>
This option requires the following ArduPilot parameter setup:
<br>
TODO
<br>
<br>  

### Configuration

Configuration can be set in the ```default.yaml``` config file.

<br>

# Running the gui

```
pip3 install flask
```
Add /home/robot/.local/bin to PATH
You can serve the app with run.sh script
Or serve with apache2:

sudo apt-get install apache2
and run setup.sh

