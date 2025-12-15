"""
Web Automation Tool - Modern Web UI Version
A Flask-based web application for automating data entry using Selenium.
"""

import os
import json
import time
import threading
import secrets
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['CONFIG_FILE'] = 'config.json'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Thread lock for state access
state_lock = threading.Lock()

# Global state
automation_state = {
    'is_running': False,
    'is_paused': False,
    'should_stop': False,
    'driver': None,
    'data': None,
    'file_info': None,
    'file_path': None,
    'config': {
        'url': 'https://www.google.com',
        'delay': 2.0,
        'browser': 'chrome',
        'start_row': 0,
        'end_row': -1,
        'headless': False,
        'retry_failed': True,
        'max_retries': 3
    },
    'stats': {
        'success': 0,
        'failed': 0,
        'total': 0,
        'current': 0,
        'start_time': None
    },
    'failed_rows': [],
    'logs': [],
    'selected_element': None,
    'element_xpath': None,
    'submit_xpath': None
}

# JavaScript for element selection
ELEMENT_SELECTOR_JS = """
(function() {
    if (window.__automationSelectorActive) return;
    window.__automationSelectorActive = true;
    
    var overlay = document.createElement('div');
    overlay.id = '__automation_overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:999999;pointer-events:none;';
    document.body.appendChild(overlay);
    
    var highlight = document.createElement('div');
    highlight.id = '__automation_highlight';
    highlight.style.cssText = 'position:absolute;border:3px solid #3b82f6;background:rgba(59,130,246,0.1);pointer-events:none;z-index:999998;transition:all 0.1s;';
    document.body.appendChild(highlight);
    
    var info = document.createElement('div');
    info.id = '__automation_info';
    info.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#1e293b;color:#f1f5f9;padding:12px 24px;border-radius:8px;font-family:system-ui;font-size:14px;z-index:1000000;box-shadow:0 4px 20px rgba(0,0,0,0.3);';
    info.innerHTML = '👆 Click on the <strong>%ELEMENT_TYPE%</strong> you want to select';
    document.body.appendChild(info);
    
    window.__lastHovered = null;
    
    function getXPath(element) {
        if (element.id) return '//*[@id="' + element.id + '"]';
        if (element === document.body) return '/html/body';
        
        var ix = 0;
        var siblings = element.parentNode ? element.parentNode.childNodes : [];
        for (var i = 0; i < siblings.length; i++) {
            var sibling = siblings[i];
            if (sibling === element) {
                var parentPath = element.parentNode ? getXPath(element.parentNode) : '';
                return parentPath + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            }
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
        }
    }
    
    document.addEventListener('mousemove', function(e) {
        var elem = document.elementFromPoint(e.clientX, e.clientY);
        if (!elem || elem.id && elem.id.startsWith('__automation')) return;
        
        window.__lastHovered = elem;
        var rect = elem.getBoundingClientRect();
        highlight.style.top = rect.top + 'px';
        highlight.style.left = rect.left + 'px';
        highlight.style.width = rect.width + 'px';
        highlight.style.height = rect.height + 'px';
    }, true);
    
    document.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        var elem = window.__lastHovered || document.elementFromPoint(e.clientX, e.clientY);
        if (!elem || elem.id && elem.id.startsWith('__automation')) return;
        
        var xpath = getXPath(elem);
        var tagName = elem.tagName.toLowerCase();
        var className = elem.className || '';
        var id = elem.id || '';
        
        window.__selectedElementInfo = {
            xpath: xpath,
            tag: tagName,
            id: id,
            className: className.toString().substring(0, 50)
        };
        
        // Visual feedback
        highlight.style.borderColor = '#22c55e';
        highlight.style.background = 'rgba(34,197,94,0.2)';
        info.innerHTML = '✅ Selected: <strong>' + tagName + '</strong>' + (id ? ' #' + id : '');
        info.style.background = '#166534';
        
        setTimeout(function() {
            overlay.remove();
            highlight.remove();
            info.remove();
            window.__automationSelectorActive = false;
        }, 1000);
    }, true);
})();
"""


def load_config():
    """Load configuration from file."""
    try:
        if os.path.exists(app.config['CONFIG_FILE']):
            with open(app.config['CONFIG_FILE'], 'r') as f:
                saved = json.load(f)
                automation_state['config'].update(saved)
    except Exception:
        pass


def save_config():
    """Save configuration to file."""
    try:
        with open(app.config['CONFIG_FILE'], 'w') as f:
            json.dump(automation_state['config'], f, indent=2)
    except Exception:
        pass


def log_message(message, level='info'):
    """Send log message to frontend via WebSocket."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    with state_lock:
        automation_state['logs'].append(log_entry)
        # Keep only last 1000 logs
        if len(automation_state['logs']) > 1000:
            automation_state['logs'] = automation_state['logs'][-1000:]
    socketio.emit('log', log_entry)


def update_progress(current, total, success, failed):
    """Send progress update to frontend."""
    elapsed = 0
    speed = 0
    eta = 0
    if automation_state['stats']['start_time']:
        elapsed = time.time() - automation_state['stats']['start_time']
        if elapsed > 0 and (success + failed) > 0:
            speed = (success + failed) / (elapsed / 60)
            remaining = total - current
            if speed > 0:
                eta = int((remaining / speed) * 60)
    
    socketio.emit('progress', {
        'current': current,
        'total': total,
        'percent': int((current / total) * 100) if total > 0 else 0,
        'success': success,
        'failed': failed,
        'elapsed': int(elapsed),
        'speed': round(speed, 1),
        'eta': eta
    })


def get_driver(browser='chrome', headless=False):
    """Initialize and return WebDriver with error handling."""
    try:
        if browser == 'chrome':
            options = ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            if headless:
                options.add_argument('--headless=new')
            return webdriver.Chrome(options=options)
        elif browser == 'firefox':
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            return webdriver.Firefox(options=options)
        elif browser == 'edge':
            options = EdgeOptions()
            if headless:
                options.add_argument('--headless')
            return webdriver.Edge(options=options)
        return webdriver.Chrome()
    except WebDriverException as e:
        raise Exception(f"Failed to initialize {browser} browser. Make sure it's installed. Error: {str(e)}")


def inject_element_selector(driver, element_type='INPUT FIELD'):
    """Inject JavaScript for element selection."""
    js = ELEMENT_SELECTOR_JS.replace('%ELEMENT_TYPE%', element_type)
    driver.execute_script(js)


def get_selected_element(driver):
    """Get the selected element info from browser."""
    try:
        result = driver.execute_script("return window.__selectedElementInfo;")
        return result
    except:
        return None


def process_row(driver, value, input_xpath, submit_xpath, retry_count=0, max_retries=3):
    """Process a single row with retry logic."""
    try:
        # Find input element
        input_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, input_xpath))
        )
        input_elem.clear()
        input_elem.send_keys(str(value))
        
        time.sleep(0.3)
        
        # Find and click submit
        submit_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, submit_xpath))
        )
        submit_elem.click()
        
        return True, None
    except Exception as e:
        if retry_count < max_retries:
            time.sleep(1)
            return process_row(driver, value, input_xpath, submit_xpath, retry_count + 1, max_retries)
        return False, str(e)


def run_automation(column_name):
    """Main automation loop - runs in background thread."""
    state = automation_state
    config = state['config']
    
    try:
        with state_lock:
            state['stats']['start_time'] = time.time()
            state['stats']['success'] = 0
            state['stats']['failed'] = 0
            state['failed_rows'] = []
        
        log_message('Initializing browser...', 'info')
        state['driver'] = get_driver(config['browser'], config.get('headless', False))
        
        log_message(f'Navigating to: {config["url"]}', 'info')
        state['driver'].get(config['url'])
        time.sleep(2)
        
        # Element selection phase - Input field
        log_message('⚠️ Click on the INPUT FIELD in the browser window', 'warning')
        inject_element_selector(state['driver'], 'INPUT FIELD')
        socketio.emit('wait_for_element', {'type': 'input'})
        
        # Wait for element selection
        while not state.get('input_selected') and not state['should_stop']:
            elem_info = get_selected_element(state['driver'])
            if elem_info:
                state['element_xpath'] = elem_info['xpath']
                state['input_selected'] = True
                log_message(f"✅ Input field selected: {elem_info['tag']}" + 
                           (f" #{elem_info['id']}" if elem_info.get('id') else ''), 'success')
            time.sleep(0.5)
        
        if state['should_stop']:
            raise Exception('Automation stopped by user')
        
        time.sleep(1)
        
        # Element selection phase - Submit button
        log_message('⚠️ Now click on the SUBMIT BUTTON in the browser window', 'warning')
        inject_element_selector(state['driver'], 'SUBMIT BUTTON')
        socketio.emit('wait_for_element', {'type': 'submit'})
        
        while not state.get('submit_selected') and not state['should_stop']:
            elem_info = get_selected_element(state['driver'])
            if elem_info:
                state['submit_xpath'] = elem_info['xpath']
                state['submit_selected'] = True
                log_message(f"✅ Submit button selected: {elem_info['tag']}" + 
                           (f" #{elem_info['id']}" if elem_info.get('id') else ''), 'success')
            time.sleep(0.5)
        
        if state['should_stop']:
            raise Exception('Automation stopped by user')
        
        socketio.emit('elements_confirmed')
        log_message('Starting data processing...', 'info')
        
        # Get data range
        data = state['data']
        start = config['start_row']
        end = config['end_row'] if config['end_row'] != -1 else len(data)
        data_subset = data.iloc[start:end]
        total = len(data_subset)
        
        with state_lock:
            state['stats']['total'] = total
        
        for idx, (index, row) in enumerate(data_subset.iterrows()):
            if state['should_stop']:
                log_message('Automation stopped by user', 'warning')
                break
            
            while state['is_paused'] and not state['should_stop']:
                time.sleep(0.5)
            
            value = str(row[column_name])
            state['stats']['current'] = idx + 1
            
            success, error = process_row(
                state['driver'], 
                value, 
                state['element_xpath'], 
                state['submit_xpath'],
                max_retries=config.get('max_retries', 3) if config.get('retry_failed', True) else 0
            )
            
            if success:
                with state_lock:
                    state['stats']['success'] += 1
                log_message(f'Row {index + 1}: {value[:50]}{"..." if len(value) > 50 else ""}', 'success')
            else:
                with state_lock:
                    state['stats']['failed'] += 1
                    state['failed_rows'].append({'index': index, 'value': value, 'error': error})
                log_message(f'Row {index + 1} failed: {error}', 'error')
            
            update_progress(
                idx + 1, total,
                state['stats']['success'],
                state['stats']['failed']
            )
            
            time.sleep(config['delay'])
        
        # Summary
        log_message('═' * 40, 'info')
        log_message(f'✅ Completed! Success: {state["stats"]["success"]}, Failed: {state["stats"]["failed"]}', 'success')
        
        if state['failed_rows']:
            log_message(f'⚠️ {len(state["failed_rows"])} rows failed. Check failed rows for details.', 'warning')
        
        socketio.emit('automation_complete', {
            **state['stats'],
            'failed_rows': state['failed_rows']
        })
        socketio.emit('play_sound', {'type': 'complete'})
        
    except Exception as e:
        log_message(f'Error: {str(e)}', 'error')
        socketio.emit('automation_error', {'error': str(e)})
        socketio.emit('play_sound', {'type': 'error'})
    
    finally:
        if state['driver']:
            try:
                state['driver'].quit()
            except:
                pass
            state['driver'] = None
        
        with state_lock:
            state['is_running'] = False
            state['is_paused'] = False
            state['should_stop'] = False
            state['input_selected'] = False
            state['submit_selected'] = False
        socketio.emit('automation_stopped')


def cleanup_uploads():
    """Clean up old uploaded files."""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            # Remove files older than 1 hour
            if os.path.isfile(filepath):
                if time.time() - os.path.getmtime(filepath) > 3600:
                    os.remove(filepath)
    except Exception:
        pass


@app.route('/')
def index():
    """Serve the main page."""
    load_config()
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle Excel file upload."""
    cleanup_uploads()  # Clean old files
    
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
        
        # Get preview data (first 5 rows)
        preview = df.head(5).to_dict('records')
        
        with state_lock:
            automation_state['data'] = df
            automation_state['file_path'] = filepath
            automation_state['file_info'] = {
                'name': filename,
                'rows': len(df),
                'columns': list(df.columns),
                'size': os.path.getsize(filepath),
                'preview': preview
            }
        
        return jsonify({
            'success': True,
            'file': automation_state['file_info']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-file', methods=['POST'])
def clear_file():
    """Clear the uploaded file."""
    with state_lock:
        if automation_state.get('file_path') and os.path.exists(automation_state['file_path']):
            try:
                os.remove(automation_state['file_path'])
            except:
                pass
        automation_state['data'] = None
        automation_state['file_info'] = None
        automation_state['file_path'] = None
    return jsonify({'success': True})


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration."""
    if request.method == 'GET':
        return jsonify(automation_state['config'])
    
    data = request.json
    with state_lock:
        automation_state['config'].update(data)
    save_config()
    return jsonify({'success': True, 'config': automation_state['config']})


@app.route('/api/start', methods=['POST'])
def start_automation():
    """Start the automation process."""
    if automation_state['is_running']:
        return jsonify({'error': 'Automation already running'}), 400
    
    if automation_state['data'] is None:
        return jsonify({'error': 'No data loaded. Please upload an Excel file first.'}), 400
    
    data = request.json
    column = data.get('column')
    
    if not column:
        return jsonify({'error': 'No column selected'}), 400
    
    if column not in automation_state['data'].columns:
        return jsonify({'error': f'Column "{column}" not found in data'}), 400
    
    # Validate URL
    url = automation_state['config'].get('url', '')
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        return jsonify({'error': 'Invalid URL. Must start with http:// or https://'}), 400
    
    with state_lock:
        automation_state['is_running'] = True
        automation_state['should_stop'] = False
        automation_state['input_selected'] = False
        automation_state['submit_selected'] = False
        automation_state['element_xpath'] = None
        automation_state['submit_xpath'] = None
        automation_state['logs'] = []
    
    thread = threading.Thread(target=run_automation, args=(column,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})


@app.route('/api/stop', methods=['POST'])
def stop_automation():
    """Stop the automation process."""
    with state_lock:
        automation_state['should_stop'] = True
    return jsonify({'success': True})


@app.route('/api/pause', methods=['POST'])
def toggle_pause():
    """Toggle pause state."""
    with state_lock:
        automation_state['is_paused'] = not automation_state['is_paused']
    return jsonify({'paused': automation_state['is_paused']})


@app.route('/api/confirm-element', methods=['POST'])
def confirm_element():
    """Confirm element selection from browser."""
    data = request.json
    elem_type = data.get('type')
    
    with state_lock:
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
        'file_info': automation_state['file_info'],
        'config': automation_state['config']
    })


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get all logs."""
    return jsonify({'logs': automation_state['logs']})


@app.route('/api/export-logs', methods=['GET'])
def export_logs():
    """Export logs as a text file."""
    logs = automation_state['logs']
    content = '\n'.join([f"[{l['timestamp']}] [{l['level'].upper()}] {l['message']}" for l in logs])
    
    filename = f"automation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Web Automation Tool - Log Export\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write('=' * 50 + '\n\n')
        f.write(content)
    
    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route('/api/failed-rows', methods=['GET'])
def get_failed_rows():
    """Get list of failed rows."""
    return jsonify({'failed_rows': automation_state['failed_rows']})


@app.route('/api/retry-failed', methods=['POST'])
def retry_failed():
    """Retry failed rows."""
    if automation_state['is_running']:
        return jsonify({'error': 'Automation already running'}), 400
    
    if not automation_state['failed_rows']:
        return jsonify({'error': 'No failed rows to retry'}), 400
    
    return jsonify({'success': True, 'message': 'Use the main automation with retry enabled'})


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    emit('connected', {
        'status': 'Connected to server',
        'config': automation_state['config']
    })


if __name__ == '__main__':
    load_config()
    print('\n' + '=' * 50)
    print('🤖 Web Automation Tool - Modern UI')
    print('=' * 50)
    print('Open your browser and go to: http://localhost:5000')
    print('=' * 50 + '\n')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
