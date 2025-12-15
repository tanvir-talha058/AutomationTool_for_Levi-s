"""
Web Automation Tool - Modern Web UI Version
A Flask-based web application for automating data entry using Selenium.
"""

import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'automation-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global state
automation_state = {
    'is_running': False,
    'is_paused': False,
    'should_stop': False,
    'driver': None,
    'data': None,
    'file_info': None,
    'config': {
        'url': 'https://www.google.com',
        'delay': 2.0,
        'browser': 'chrome',
        'start_row': 0,
        'end_row': -1
    },
    'stats': {
        'success': 0,
        'failed': 0,
        'total': 0,
        'current': 0,
        'start_time': None
    }
}


def log_message(message, level='info'):
    """Send log message to frontend via WebSocket."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    socketio.emit('log', {
        'timestamp': timestamp,
        'message': message,
        'level': level
    })


def update_progress(current, total, success, failed):
    """Send progress update to frontend."""
    elapsed = 0
    speed = 0
    if automation_state['stats']['start_time']:
        elapsed = time.time() - automation_state['stats']['start_time']
        if elapsed > 0:
            speed = (success + failed) / (elapsed / 60)
    
    socketio.emit('progress', {
        'current': current,
        'total': total,
        'percent': int((current / total) * 100) if total > 0 else 0,
        'success': success,
        'failed': failed,
        'elapsed': int(elapsed),
        'speed': round(speed, 1)
    })


def get_driver(browser='chrome'):
    """Initialize and return WebDriver."""
    if browser == 'chrome':
        options = Options()
        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return webdriver.Chrome(options=options)
    elif browser == 'firefox':
        return webdriver.Firefox()
    elif browser == 'edge':
        return webdriver.Edge()
    return webdriver.Chrome()


def run_automation(column_name):
    """Main automation loop - runs in background thread."""
    state = automation_state
    config = state['config']
    
    try:
        state['stats']['start_time'] = time.time()
        state['stats']['success'] = 0
        state['stats']['failed'] = 0
        
        log_message('Initializing browser...', 'info')
        state['driver'] = get_driver(config['browser'])
        
        log_message(f'Navigating to: {config["url"]}', 'info')
        state['driver'].get(config['url'])
        time.sleep(2)
        
        log_message('⚠️ Click on the INPUT FIELD in the browser, then click "Confirm Input"', 'warning')
        socketio.emit('wait_for_element', {'type': 'input'})
        
        # Wait for element selection
        while not state.get('input_selected') and not state['should_stop']:
            time.sleep(0.5)
        
        if state['should_stop']:
            raise Exception('Automation stopped by user')
        
        log_message('✅ Input field confirmed', 'success')
        log_message('⚠️ Now click on the SUBMIT BUTTON, then click "Confirm Submit"', 'warning')
        socketio.emit('wait_for_element', {'type': 'submit'})
        
        while not state.get('submit_selected') and not state['should_stop']:
            time.sleep(0.5)
        
        if state['should_stop']:
            raise Exception('Automation stopped by user')
        
        log_message('✅ Submit button confirmed', 'success')
        log_message('Starting data processing...', 'info')
        
        # Get data range
        data = state['data']
        start = config['start_row']
        end = config['end_row'] if config['end_row'] != -1 else len(data)
        data_subset = data.iloc[start:end]
        total = len(data_subset)
        
        state['stats']['total'] = total
        
        for idx, (index, row) in enumerate(data_subset.iterrows()):
            if state['should_stop']:
                log_message('Automation stopped by user', 'warning')
                break
            
            while state['is_paused'] and not state['should_stop']:
                time.sleep(0.5)
            
            try:
                value = str(row[column_name])
                state['stats']['current'] = idx + 1
                
                # Get active element and interact
                input_elem = state['driver'].switch_to.active_element
                input_elem.clear()
                input_elem.send_keys(value)
                
                time.sleep(0.3)
                input_elem.submit()
                
                state['stats']['success'] += 1
                log_message(f'Row {index + 1}: {value[:50]}', 'success')
                
            except Exception as e:
                state['stats']['failed'] += 1
                log_message(f'Row {index + 1} failed: {str(e)}', 'error')
            
            update_progress(
                idx + 1, total,
                state['stats']['success'],
                state['stats']['failed']
            )
            
            time.sleep(config['delay'])
        
        log_message('═' * 40, 'info')
        log_message(f'✅ Completed! Success: {state["stats"]["success"]}, Failed: {state["stats"]["failed"]}', 'success')
        socketio.emit('automation_complete', state['stats'])
        
    except Exception as e:
        log_message(f'Error: {str(e)}', 'error')
        socketio.emit('automation_error', {'error': str(e)})
    
    finally:
        if state['driver']:
            try:
                state['driver'].quit()
            except:
                pass
            state['driver'] = None
        
        state['is_running'] = False
        state['is_paused'] = False
        state['should_stop'] = False
        state['input_selected'] = False
        state['submit_selected'] = False
        socketio.emit('automation_stopped')


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle Excel file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type. Please upload an Excel file.'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        df = pd.read_excel(filepath)
        automation_state['data'] = df
        automation_state['file_info'] = {
            'name': filename,
            'rows': len(df),
            'columns': list(df.columns),
            'size': os.path.getsize(filepath)
        }
        
        return jsonify({
            'success': True,
            'file': automation_state['file_info']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration."""
    if request.method == 'GET':
        return jsonify(automation_state['config'])
    
    data = request.json
    automation_state['config'].update(data)
    return jsonify({'success': True, 'config': automation_state['config']})


@app.route('/api/start', methods=['POST'])
def start_automation():
    """Start the automation process."""
    if automation_state['is_running']:
        return jsonify({'error': 'Automation already running'}), 400
    
    if automation_state['data'] is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    data = request.json
    column = data.get('column')
    
    if not column:
        return jsonify({'error': 'No column selected'}), 400
    
    automation_state['is_running'] = True
    automation_state['should_stop'] = False
    automation_state['input_selected'] = False
    automation_state['submit_selected'] = False
    
    thread = threading.Thread(target=run_automation, args=(column,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})


@app.route('/api/stop', methods=['POST'])
def stop_automation():
    """Stop the automation process."""
    automation_state['should_stop'] = True
    return jsonify({'success': True})


@app.route('/api/pause', methods=['POST'])
def toggle_pause():
    """Toggle pause state."""
    automation_state['is_paused'] = not automation_state['is_paused']
    return jsonify({'paused': automation_state['is_paused']})


@app.route('/api/confirm-element', methods=['POST'])
def confirm_element():
    """Confirm element selection from browser."""
    data = request.json
    elem_type = data.get('type')
    
    if elem_type == 'input':
        automation_state['input_selected'] = True
    elif elem_type == 'submit':
        automation_state['submit_selected'] = True
    
    return jsonify({'success': True})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current automation status."""
    return jsonify({
        'is_running': automation_state['is_running'],
        'is_paused': automation_state['is_paused'],
        'stats': automation_state['stats'],
        'file_info': automation_state['file_info']
    })


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    emit('connected', {'status': 'Connected to server'})


if __name__ == '__main__':
    print('\n' + '=' * 50)
    print('🤖 Web Automation Tool - Modern UI')
    print('=' * 50)
    print('Open your browser and go to: http://localhost:5000')
    print('=' * 50 + '\n')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
