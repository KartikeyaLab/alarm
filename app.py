# app.py (Improved Stop Ring from Both Sides)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading
import time
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = 'devices.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            return data.get('registered_devices', {}), data.get('device_history', [])
    return {}, []

def save_data():
    with open(DATA_FILE, 'w') as file:
        json.dump({
            'registered_devices': registered_devices,
            'device_history': device_history
        }, file, indent=4)

registered_devices, device_history = load_data()
alarms = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_device():
    data = request.get_json()
    device_name = data.get('device_name', '').strip()

    if not device_name:
        return jsonify({'status': 'Invalid device name'}), 400

    if device_name not in registered_devices:
        registered_devices[device_name] = {'ringing': False, 'message': '', 'ring_id': 0}
        device_history.append({
            'device_name': device_name,
            'registered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data()
        return jsonify({'status': 'Device registered successfully'})

    return jsonify({'status': 'Device already registered'})

@app.route('/get_devices', methods=['GET'])
def get_devices():
    return jsonify({'devices': list(registered_devices.keys())})

@app.route('/ring', methods=['POST'])
def ring():
    data = request.json
    target_device = data.get('target_device', '').strip()
    message = data.get('message', 'Are you awake?')

    if target_device not in registered_devices:
        return jsonify({'status': 'Device not found'}), 404

    registered_devices[target_device]['ringing'] = True
    registered_devices[target_device]['message'] = message
    registered_devices[target_device]['ring_id'] += 1
    save_data()
    return jsonify({'status': f'Ringing {target_device}', 'ring_id': registered_devices[target_device]['ring_id']})

@app.route('/check_ring', methods=['GET'])
def check_ring():
    device_name = request.args.get('device_name', '').strip()

    if device_name not in registered_devices:
        return jsonify({'ringing': False})

    device = registered_devices[device_name]
    return jsonify({'ringing': device['ringing'], 'message': device['message'], 'ring_id': device['ring_id']})

@app.route('/acknowledge', methods=['POST'])
def acknowledge():
    data = request.json
    device_name = data.get('device_name', '').strip()

    if device_name in registered_devices:
        registered_devices[device_name]['ringing'] = False
        registered_devices[device_name]['message'] = ''
        save_data()
        return jsonify({'status': 'Acknowledged'})

    return jsonify({'status': 'Device not found'}), 404

@app.route('/stop_ring', methods=['POST'])
def stop_ring():
    data = request.json
    target_device = data.get('target_device', '').strip()

    if target_device in registered_devices:
        registered_devices[target_device]['ringing'] = False
        registered_devices[target_device]['message'] = ''
        save_data()
        return jsonify({'status': f'Ringing stopped for {target_device}'})

    return jsonify({'status': 'Device not found'}), 404

@app.route('/set_alarm', methods=['POST'])
def set_alarm():
    data = request.json
    target_device = data.get('target_device', '').strip()
    alarm_time = data.get('alarm_time', '').strip()
    message = data.get('message', 'Alarm Time! Are you awake?')

    if target_device not in registered_devices:
        return jsonify({'status': 'Device not found'}), 404

    if not alarm_time:
        return jsonify({'status': 'Invalid alarm time'}), 400

    alarms.append({'device': target_device, 'alarm_time': alarm_time, 'message': message})
    return jsonify({'status': f'Alarm set for {target_device} at {alarm_time}'})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

def alarm_checker():
    while True:
        current_time = time.strftime('%H:%M')
        for alarm in alarms[:]:
            if alarm['alarm_time'] == current_time:
                device = alarm['device']
                if device in registered_devices:
                    registered_devices[device]['ringing'] = True
                    registered_devices[device]['message'] = alarm['message']
                    registered_devices[device]['ring_id'] += 1
                    alarms.remove(alarm)
                    save_data()
        time.sleep(10)



if __name__ == '__main__':
    threading.Thread(target=alarm_checker, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)