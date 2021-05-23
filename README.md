![MiniB-farm](https://user-images.githubusercontent.com/84319584/119270749-12ff4400-bbf6-11eb-84be-ac4ebf1a8db9.png)


# mycelium
mycelium is a fast light weight in-memory data exchange for sensor information on-board a robot or between robots in large distributed and scalable swarms or systems.

mycelium is aimed at mobile robotics and embodied intelligence. You can think of mycelium as the robot's memory, both short term and long term. 
The goal of mycelium is to enable robots to learn from experiences during operation and improve over time, as well as allowing them to quickly simulate expected outcomes of actions on-board. 
Conceptually this is achived by creating a complete model (sensor, data, processed data, inputs and outputs) of the robot in-memory in a redis data-base allowing many subroutines to access this data-base and periodically saving snapshot of part or whole of the database on the hard drive (long term storage).
Long term storage can be analyised at any point to change subroutines effecting current in-memory storage.<br>

## status

Currently mycleium enable easy interfacing between sensors and software components enabling a large number of different programming language to easily interact with the system data.
At this point it uses a ardupilot baed flight controller for guidance navigation and control. Overall the system has 2 key function: 1) Waypoint based navigation 2) Obstacle avoidance.
WP based navigation combines absolute localisation using GPS and relative localisation using Visual Odometry. Robustness and tolerance to failure (hardware, network, power) are important design considerations.
<br>

## References and 3rd party projects

The software draws concepts from GSoC 2020 Ardupilot: 
Camera scripts are based on scripts found on Ardupilto documentation:<br>
https://ardupilot.org/copter/docs/common-realsense-depth-camera.html<br>
https://ardupilot.org/copter/docs/common-vio-tracking-camera.html<br>

Cameras use the Intel Realsense SDK<br>

# Hardware

Tested on the following: 
"Flight Controller" Running Ardurover 4.0.0 henceforth refered to as "Robot Controller" or RC
Tested on the following computers: Ultra96-V2 (Zynq UltraScale+), NanoPi Neo3 2GB (FriendlyElec RK3328), NanoPi R4S (FriendlyElec RK3399), Raspberry Pi4 8GB, Raspberry Pi Zero, Beaglebone Blue, multiple x86 computers

●	Intel RealSense T265 tracking camera
●	Intel RealSense D435 stereo camera
●	GPS modules
●	Camera stream over UDP
●	Livox Horizon Lidar (optional) for mapping

Tested on GMV's MiniB rover (version 3.5).

<br>

# Installation

Clone the repository:
```
git clone https://spass-git-ext.gmv.com/BEAST/mycelium.git
```
The ```setup.sh``` script will add the python mycelium module to path and install services for running scripts with systemd (note: pyrealsense2 must be added to the python path). It will also generate a mavlink router config file for connection endpoints. Before running the script, you should update the config file ```mycelium/cfg/default.yaml``` with the correct ArduPilot device port and connection baudrate.


```
chmod +x setup.sh
source setup.sh
```
<br>

### Main requirements (automatically installed by Setup) 
```
●	pymavlink  
●	PyYAML  
●	transformations  
●	redis  
●	apscheduler
●	dronekit

```  
 
## MGUI Installation (optional)

The web GUI runs on a web application framework called Flask and can be set up to run continuously in the background on an Apache server. Alternatively, the GUI can be served on the cuff (see below).

### Web server

In the mycelium/gui directory run:

```
chmod +x setup.sh
source setup.sh
```

After a successful installation, the GUI will be running on Apache by default on booting. To enable or disable this, the scripts to be run are run_gui_server.sh and stop_gui_server.sh.  The GUI will be served on localhost:8080.

#### Ad-hoc

To serve the GUI on the cuff, run the run.sh script. This will serve the GUI on localhost:5000.

## UDP Camera Installation (optional)

This add-on is aimed at receiving high-res camera data from a stand-alone board over network. By defualt it is configured to capture raw bayer data. It can be run as a standalone camera or in sync with an ArduPilot mission on a robot.  

In the picamera directory run:

```
chmod +x setup.sh
source setup.sh
```

If running in sync with an ArduPilot mission on a robot, UDP endpoints to the robot will need to be generated on the robot (see below in Advanced Mavlink Port Setup). The picamera IP address will also need to be set in the network.yaml config file in the cfg directory.

### Hardware

Tested on Arducam 12MP IMX477 Mini High Quality Camera Module using CSI on Raspberry Pi zero

## Advanced Mavlink Port Setup (optional)

This allows for communication via the Mavlink router to other robots and devices on the network.
In network.yaml, make sure the robot/device IP is set there and add a port number for the UDP endpoint. The port number must not already be in use. By default, the following ports are used for mycelium software endpoints: 14575, 14560, 14570, 14578, 14579 (see cfg/default.yaml).

Example of IP/port number entry:

```
external_connection_to_robot: 192.x.x.x
_external_connection_to_robot: 14580
```

The first entry is the IP address of the robot to connect to and the second entry is the port number. These entries should be added before the mavlink router config file is generated (whether through the setup.sh script or manually with scripts/generate_mavlink_conf.py).

# How to run

## Services

### Service paradigm

To create an efficent fast and scalable system each service should be single purpose, as small as possible and expose as much information as possible to the Redis server data exchange.

### List of current services

| Name of service  | Description | Run script |
| ------------- | ------------- | ------------- |
| mycelium-t265.service  | Connects to the T265 realsense camera and stores pose data in the Redis database.  | scripts/run_t265.py |
| mycelium-d435.service  | Connects to the D435 realsense camera and stores obstacle distance data in the Redis database. Can also be set to save RGB/depth/IR images captured from frames.  | scripts/run_d435.py |
| mycelium-redis-to-ap.service  | Sends valid parameters stored in Redis to ArduPilot. The parameters to be sent are specified in cfg/redis_dict.yaml under key: instruments.  | redis_scripts/redis_to_ap.service |
| mycelium-ap-to-redis.service  | Retrieves parameters from ArduPilot and stores in Redis. The parameters to be retrieved are specified in cfg/redis_dict.yaml under key: robot.  | redis_scripts/ap_to_redis.service |
| mavlink-router.service  | Router service for connecting to the flight controller and re-routing Mavlink messages sent to specified TCP/UDP ports.  | N/A |
| redis  | System-wide database (in-memory) for exchange of mycelium parameters and data accessible by subprocess in any language  | N/A |

The last two services are external to the mycelium code-base and thus have no run script. The services are implemented with systemd, a service manager for Linux. To see the status of a service, run:

```
sudo systemctl status [name of service]
```

These services will restart automatically upon failure and run continuously until stopped.<br>

Other commands are start, stop, restart, enable.
These services will restart automatically upon failure and run continuously until stopped. You can start all services at once with the start_services.sh script. The T265 and D435 camera services are automatically enabled with the setup.sh script.

### Services planned:

-MavROS integration
-Past -periodick backup for redis database
-Future -forward simulator of states of redis database

### Additional scripts

#### scripts/generate_mavlink_conf.py	
Generates Mavlink router configuration with IP and ports set in cfg/default.yaml and cfg/network.yaml.

#### scripts/send_to_waypoint.py	
Sets the next waypoint in an ArduPilot mission.

#### scripts/set_ekf_source.py

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

#### scripts/set_initial_mode.py	
Sets the startup mode for robot when first powered on.
 
#### scripts/set_relay.py

Sets relay state on/off for specified pin. This relay pin must first be configured correctly in ArduPilot.
 

# Advanced Settings

## Camera D435

There are four configuration modes available:
1	Enables RGB and depth streams and does not save frame images
2	Enables RGB and infrared streams and does not save frames images
3	Enables infrared stream and does not save frames
4	Custom mode: this mode allows streams and frame saving options to be set in cfg/default.yaml

The configuration mode is set in cfg/default.yaml with parameter d435:configuration_mode. The mode always overrides the separate parameters such as d435:enable_rgb_stream. Frame saving can be toggled on and off manually to override the configuration mode setting (see below). However, note that the relevant stream must first be enabled in order for the associated frame to be saved. The camera service must always be restarted for changes in configuration to take place (with the exception of frame saving, see below).
<br>

### Saving frames

The Redis database stores keys to toggle frame saving:
<br>
d435:save_rgb_frames
d435:save_depth_frames
d435:save_infrared_frames
<br>
Set to 0 to toggle off and 1 to toggle on.
<br>

### ArduPilot parameters

The D435 camera saves the following ArduPilot parameters to the Redis database:
d435:obstacle_distance

## Camera T265

### ArduPilot parameters

The T265 camera saves the following ArduPilot parameters to the Redis database:
t265:vision_position_estimate

# Ongoing work

-	Camera T265 : add ArduPilot messages
o	Position delta
o	Vision speed estimate
-	Fix the message frequency to AP in redis_to_ap.py
-	Create snapshot backups for Redis database
-	Add tests
-	Replace Connector class (mycelium/components/ardu_mavlink.py) with Dronekit library methods
-	GUI:
o	Detect and list available sensors
o	Log data for runtime and usage of mycelium services in the Redis database – this data can be used for system analysis and to create a visual display for the user of the system state over time



