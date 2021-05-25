from flask import Flask, request, render_template, redirect
import os
import json
import glob
import base64
from datetime import datetime

from mycelium import EKFSwitch, RelaySwitch, CameraD435
from mycelium.components import RedisBridge
from mycelium_utils import RedisConfig, DefaultConfig, utils

app = Flask(__name__, static_url_path='', static_folder='static')

services = {
    'mav_router': 1,
    'redis': 2,
    'ap_to_redis': 3,
    'redis_to_ap': 4,
    't265': 5,
    'd435': 6
}

service_file = {
    'mav_router': 'mavlink-router.service',
    'redis': 'redis.service',
    'ap_to_redis': 'mycelium-ap-to-redis.service',
    'redis_to_ap': 'mycelium-redis-to-ap.service',
    't265': 'mycelium-t265.service',
    'd435': 'mycelium-d435.service'
}

@app.route('/')
def index():
    return redirect('/service')

@app.route('/service')
def service_tab():
    stats = get_service_status(False)
    if len(stats) == 6:
        service_statuses = {
            'mav_router': stats[0],
            'redis': stats[1],
            'ap_to_redis': stats[2],
            'redis_to_ap': stats[3],
            't265': stats[4],
            'd435': stats[5]
        }
    else:
        service_statuses = {
            'mav_router': 'n/a',
            'redis': 'n/a',
            'ap_to_redis': 'n/a',
            'redis_to_ap': 'n/a',
            't265': 'n/a',
            'd435': 'n/a'
        }
        
    return render_template('main.html', 
        tab="service",
        tab_html="service_tab.html",
        service_statuses=service_statuses, 
        services=services
    )

@app.route('/service/set-state/<service>/<state>')
def set_service_state(service, state):
    call = service_file[service]
    
    if int(state) == 0:
        msg = 'Stopping ' + service
        call = 'sudo systemctl stop ' + call
    else:               
        msg = 'Starting ' + service
        call = 'sudo systemctl restart ' + call

    utils.progress(msg)
    os.system(call)
    return '', 204

@app.route('/service/start-all')
def start_all_services():
    for k, v in service_file.items():
        os.system('sudo systemctl start '+v)
    return '', 204

@app.route('/service/stop-all')
def stop_all_services():
    for k, v in service_file.items():
        os.system('sudo systemctl stop '+v)
    return '', 204

@app.route('/service/status')
def get_service_status(to_json=True):
    status = []
    for k, v in service_file.items():
        status.append(os.popen('sudo systemctl is-active '+v).read())
    if to_json:
        return json.dumps(status)
    return status

@app.route('/service/log/<service>', defaults={'lines': 1})
@app.route('/service/log/<service>/<lines>')
def get_service_log(service, lines, to_json=True):
    if service not in service_file.keys():
        return None

    service = service_file[service]
    output = os.popen('sudo journalctl -u '+service+' -n '+str(lines)).read()
    status = output.splitlines()
    if to_json:
        return json.dumps(status)
    return status

@app.route('/service/log-all', defaults={'lines': 1})
@app.route('/service/log-all/<lines>')
def get_service_logs_all(lines):
    logs = []
    for k, v in service_file.items():
        log = get_service_log(k, lines, False)
        logs.append(log)
    return json.dumps(logs)


#########################################################

controls = {
    'ekf_source': 1,
    'led_relay': 2,
    'rgb_capture': 3,
    'depth_capture': 4,
    'infrared_capture': 5
}

@app.route('/controls')
def controls_tab():
    rgb_status = get_switch_status(controls['rgb_capture'], False)
    depth_status = get_switch_status(controls['depth_capture'], False)
    infrared_status = get_switch_status(controls['infrared_capture'], False)

    return render_template('main.html', 
        tab="controls",
        tab_html="controls_tab.html",
        controls=controls,
        rgb_status=rgb_status,
        depth_status=depth_status,
        infrared_status=infrared_status
    )

rd_cfg = RedisConfig()
rb = RedisBridge(db=rd_cfg.databases['instruments'])

@app.route('/controls/set/<switch>/<value>')
def set_switch(switch, value):
    msg = "Setting switch "
    switch = int(switch)
    value = int(value)
    if switch == controls['ekf_source']:
        msg += "EKF source to "
        try:
            switch = EKFSwitch()
            switch.set_ekf_source(value)
        except:
            pass
    
    elif switch == controls['led_relay']:
        msg += "LED relay to "
        try:            
            rs = RelaySwitch(relay_pin=pin)
            if value == 1:
                rs.on()
            else:
                rs.off()
        except:
            pass

    elif switch == controls['rgb_capture']:
        msg += "RGB capture to "
        rb.add_key(value, 'd435', 'save_rgb_frames', to_json=False)
        
    elif switch == controls['depth_capture']:
        msg += "depth capture to "
        rb.add_key(value, 'd435', 'save_depth_frames', to_json=False)

    elif switch == controls['infrared_capture']:
        msg += "infrared capture to "
        rb.add_key(value, 'd435', 'save_infrared_frames', to_json=False)

    else:
        print("Invalid switch")
        return redirect('/controls')

    msg += str(value)
    print(msg)
    return redirect('/controls')

@app.route('/controls/status/<switch>')
def get_switch_status(switch, to_json=True):    
    if switch == controls['rgb_capture']:
        key = 'save_rgb_frames'        
    elif switch == controls['depth_capture']:
        key = 'save_depth_frames'
    elif switch == controls['infrared_capture']:
        key = 'save_infrared_frames'
    
    return rb.get_key('d435', key, parse_json=(not to_json))

@app.route('/controls/status-all')
def get_all_switch_status():    
    status = [
        get_switch_status(controls['rgb_capture'], False),
        get_switch_status(controls['depth_capture'], False),
        get_switch_status(controls['infrared_capture'], False)
    ]
    return json.dumps(status)


#########################################################

cfg = DefaultConfig()
dir_path = os.environ['MYCELIUM_GUI_ROOT']

stream_options = {
    CameraD435.CFG_MODE_1: 'RGB & Depth',
    CameraD435.CFG_MODE_2: 'RGB & Infrared',
    CameraD435.CFG_MODE_3: 'Infrared only'
}

save_frame_options = {
    'rgb': 'save_rgb_frames', 
    'depth': 'save_depth_frames', 
    'infrared': 'save_infrared_frames'
}

@app.route('/camera')
def camera_tab():
    try:
        devices = []#list_rs_devices()
    except:
        devices = None

    return render_template('main.html', 
        tab="camera",
        tab_html="camera_tab.html",
        devices=devices,
        stream_options=stream_options,
        save_frame_options=save_frame_options
    )

@app.route('/camera/set-mode/<mode>')
def set_camera_mode(mode):
    try:
        mode = int(mode)
        cfg.write_key(mode, ['d435', 'configuration_mode'])
        return set_service_state('d435', 1)
    except:
        return '', 500

@app.route('/camera/toggle-frame-save/<frame>')
def toggle_frame_save(frame):
    try:
        val = rb.get_key('d435', save_frame_options[frame])
        if val is None:
            val = 1
        else:
            val = (int(val)+1)%2
        rb.add_key(val, 'd435', save_frame_options[frame])
        return '', 200
    except:
        return '', 500

@app.route('/camera/get-latest-image/<image_type>')
def get_latest_image(image_type):
    try:
        data_dir = dir_path + "/../" + cfg.save_data_dir
        now = datetime.today().strftime('%Y_%m_%d')
        date_dir = os.path.join(data_dir, now)
        
        if not os.path.exists(date_dir):
            return "Date directory not found", 204

        if image_type == "rgb":
            images = glob.glob(date_dir+"/*.rgb.png")
        else:
            images = glob.glob(date_dir+"/*.depth.png")
        
        if len(images) > 0:
            return generate_response(images[-1])

    except Exception as e:
        return str(e), 500

def generate_response(filename):
    with open(filename, "rb") as f:
        encoded_string = base64.b64encode(f.read())
    return encoded_string


#########################################################

databases = rd_cfg.databases

@app.route('/redis')
def redis_tab():
    return render_template('main.html', 
        tab="redis",
        tab_html="redis_tab.html",
        databases=databases
    )

@app.route('/redis/get-data/<database>/<paginate>', defaults={'paginate_it': 1})
@app.route('/redis/get-data/<database>/<paginate>/<paginate_it>')
def get_redis_data(database, paginate, paginate_it):
    database = int(database)
    paginate = int(paginate)
    paginate_it = int(paginate_it)

    rb = RedisBridge(db=int(database))
    keys = rd_cfg.generate_flat_keys(database)
    if isinstance(keys, dict):
        keys = list(keys.keys())

    start = (paginate_it-1)*paginate
    end = start+paginate
    keys = keys[start:end]
    
    data = {}
    for key in keys:
        data[key] = rb.get_key_by_string(key)

    return json.dumps(data)

#########################################################

services_by_val = dict((v,k) for k,v in services.items())

@app.route('/logs')
def logs_tab():
    lines = [20, 50, 100]
    return render_template('main.html', 
        tab="logs",
        tab_html="logs_tab.html",
        services=services,
        lines=lines
    )
    