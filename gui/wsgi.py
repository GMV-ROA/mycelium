from app import app as application

# Set MAVLink protocol to 2.
import os
os.environ["MAVLINK20"] = "1"