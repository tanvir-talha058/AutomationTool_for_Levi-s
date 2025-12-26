"""
Web Automation Tool - Modern Web UI Version.

A Flask-based web application for automating data entry using Selenium.
Provides a modern web interface for uploading Excel files and automating
browser interactions with configurable selectors.

Author: Automation Team
Version: 2.0.0
"""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from flask import Flask, Response, jsonify, render_template, request, send_file
from flask_socketio import SocketIO, emit
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.utils import secure_filename

# =============================================================================
# Constants
# =============================================================================

# File handling constants
MAX_FILE_SIZE_MB: int = 16
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({'.xlsx', '.xls'})
UPLOAD_FOLDER: str = 'uploads'
CONFIG_FILE: str = 'config.json'

# Automation constants
DEFAULT_URL: str = 'https://www.google.com'
DEFAULT_DELAY: float = 2.0
DEFAULT_BROWSER: str = 'chrome'
DEFAULT_MAX_RETRIES: int = 3
ELEMENT_WAIT_TIMEOUT: int = 10
MAX_LOG_ENTRIES: int = 1000
FILE_CLEANUP_AGE_SECONDS: int = 3600  # 1 hour

# Preview limits
PREVIEW_ROW_COUNT: int = 5
VALUE_TRUNCATE_LENGTH: int = 50

# Supported browsers
SUPPORTED_BROWSERS: frozenset[str] = frozenset({'chrome', 'firefox', 'edge'})

# =============================================================================
# Flask App Configuration
# =============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_BYTES
app.config['CONFIG_FILE'] = CONFIG_FILE

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Ensure upload folder exists
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Thread lock for state access
state_lock = threading.Lock()


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AutomationConfig:
    """Configuration settings for automation."""
    
    url: str = DEFAULT_URL
    delay: float = DEFAULT_DELAY
    browser: str = DEFAULT_BROWSER
    start_row: int = 0
    end_row: int = -1
    headless: bool = False
    retry_failed: bool = True
    max_retries: int = DEFAULT_MAX_RETRIES
    
    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'url': self.url,
            'delay': self.delay,
            'browser': self.browser,
            'start_row': self.start_row,
            'end_row': self.end_row,
            'headless': self.headless,
            'retry_failed': self.retry_failed,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutomationConfig:
        """Create config from dictionary."""
        return cls(
            url=data.get('url', DEFAULT_URL),
            delay=float(data.get('delay', DEFAULT_DELAY)),
            browser=data.get('browser', DEFAULT_BROWSER),
            start_row=int(data.get('start_row', 0)),
            end_row=int(data.get('end_row', -1)),
            headless=bool(data.get('headless', False)),
            retry_failed=bool(data.get('retry_failed', True)),
            max_retries=int(data.get('max_retries', DEFAULT_MAX_RETRIES))
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors: list[str] = []
        
        if not self.url:
            errors.append("URL is required")
        elif not (self.url.startswith('http://') or self.url.startswith('https://')):
            errors.append("URL must start with http:// or https://")
        
        if self.delay < 0:
            errors.append("Delay must be non-negative")
        
        if self.browser not in SUPPORTED_BROWSERS:
            errors.append(f"Browser must be one of: {', '.join(SUPPORTED_BROWSERS)}")
        
        if self.start_row < 0:
            errors.append("Start row must be non-negative")
        
        if self.max_retries < 0:
            errors.append("Max retries must be non-negative")
        
        return errors


@dataclass
class AutomationStats:
    """Statistics for automation run."""
    
    success: int = 0
    failed: int = 0
    total: int = 0
    current: int = 0
    start_time: Optional[float] = None
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.success = 0
        self.failed = 0
        self.total = 0
        self.current = 0
        self.start_time = time.time()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'success': self.success,
            'failed': self.failed,
            'total': self.total,
            'current': self.current,
            'start_time': self.start_time
        }


@dataclass
class FileInfo:
    """Information about uploaded file."""
    
    name: str
    rows: int
    columns: list[str]
    size: int
    preview: list[dict[str, Any]]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert file info to dictionary."""
        return {
            'name': self.name,
            'rows': self.rows,
            'columns': self.columns,
            'size': self.size,
            'preview': self.preview
        }


@dataclass
class FailedRow:
    """Information about a failed row."""
    
    index: int
    value: str
    error: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'index': self.index,
            'value': self.value,
            'error': self.error
        }


@dataclass
class LogEntry:
    """A single log entry."""
    
    timestamp: str
    message: str
    level: str
    
    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'message': self.message,
            'level': self.level
        }


@dataclass
class AutomationState:
    """Complete state of the automation system."""
    
    is_running: bool = False
    is_paused: bool = False
    should_stop: bool = False
    input_selected: bool = False
    submit_selected: bool = False
    driver: Optional[WebDriver] = None
    data: Optional[pd.DataFrame] = None
    file_info: Optional[FileInfo] = None
    file_path: Optional[str] = None
    config: AutomationConfig = field(default_factory=AutomationConfig)
    stats: AutomationStats = field(default_factory=AutomationStats)
    failed_rows: list[FailedRow] = field(default_factory=list)
    logs: list[LogEntry] = field(default_factory=list)
    element_xpath: Optional[str] = None
    submit_xpath: Optional[str] = None
    
    def reset_for_new_run(self) -> None:
        """Reset state for a new automation run."""
        self.is_running = True
        self.is_paused = False
        self.should_stop = False
        self.input_selected = False
        self.submit_selected = False
        self.element_xpath = None
        self.submit_xpath = None
        self.failed_rows = []
        self.logs = []
        self.stats.reset()
    
    def cleanup_after_run(self) -> None:
        """Clean up state after automation run."""
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.input_selected = False
        self.submit_selected = False


# Global state instance
automation_state = AutomationState()

# =============================================================================
# JavaScript for Element Selection
# =============================================================================

ELEMENT_SELECTOR_JS: str = """
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


# =============================================================================
# Custom Exceptions
# =============================================================================

class AutomationError(Exception):
    """Base exception for automation errors."""
    pass


class BrowserInitError(AutomationError):
    """Raised when browser initialization fails."""
    pass


class ElementNotFoundError(AutomationError):
    """Raised when a required element cannot be found."""
    pass


class FileValidationError(AutomationError):
    """Raised when file validation fails."""
    pass


class ConfigValidationError(AutomationError):
    """Raised when configuration validation fails."""
    pass


# =============================================================================
# Configuration Management
# =============================================================================

def load_config() -> None:
    """
    Load configuration from JSON file.
    
    Reads the configuration file and updates the global automation state.
    If the file doesn't exist or is invalid, uses default configuration.
    
    Raises:
        No exceptions are raised; errors are logged silently.
    """
    config_path = Path(app.config['CONFIG_FILE'])
    try:
        if config_path.exists():
            with config_path.open('r', encoding='utf-8') as f:
                saved = json.load(f)
                automation_state.config = AutomationConfig.from_dict(saved)
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
        log_message(f"Failed to load config: {e}", 'warning')


def save_config() -> None:
    """
    Save current configuration to JSON file.
    
    Persists the current configuration state to disk for future sessions.
    
    Raises:
        No exceptions are raised; errors are logged silently.
    """
    config_path = Path(app.config['CONFIG_FILE'])
    try:
        with config_path.open('w', encoding='utf-8') as f:
            json.dump(automation_state.config.to_dict(), f, indent=2)
    except (OSError, TypeError) as e:
        log_message(f"Failed to save config: {e}", 'warning')


# =============================================================================
# Logging and Progress
# =============================================================================

def log_message(message: str, level: str = 'info') -> None:
    """
    Send log message to frontend via WebSocket.
    
    Creates a timestamped log entry and broadcasts it to all connected clients.
    Maintains a rolling buffer of the most recent log entries.
    
    Args:
        message: The log message content.
        level: Log level - 'info', 'warning', 'error', or 'success'.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = LogEntry(timestamp=timestamp, message=message, level=level)
    
    with state_lock:
        automation_state.logs.append(log_entry)
        # Keep only last MAX_LOG_ENTRIES logs
        if len(automation_state.logs) > MAX_LOG_ENTRIES:
            automation_state.logs = automation_state.logs[-MAX_LOG_ENTRIES:]
    
    socketio.emit('log', log_entry.to_dict())


def update_progress(current: int, total: int, success: int, failed: int) -> None:
    """
    Send progress update to frontend via WebSocket.
    
    Calculates processing speed and estimated time of arrival (ETA),
    then broadcasts the progress information to all connected clients.
    
    Args:
        current: Current row being processed (1-indexed).
        total: Total number of rows to process.
        success: Count of successfully processed rows.
        failed: Count of failed rows.
    """
    elapsed: float = 0.0
    speed: float = 0.0
    eta: int = 0
    
    if automation_state.stats.start_time:
        elapsed = time.time() - automation_state.stats.start_time
        processed = success + failed
        if elapsed > 0 and processed > 0:
            speed = processed / (elapsed / 60)  # rows per minute
            remaining = total - current
            if speed > 0:
                eta = int((remaining / speed) * 60)  # seconds
    
    percent = int((current / total) * 100) if total > 0 else 0
    
    socketio.emit('progress', {
        'current': current,
        'total': total,
        'percent': percent,
        'success': success,
        'failed': failed,
        'elapsed': int(elapsed),
        'speed': round(speed, 1),
        'eta': eta
    })


# =============================================================================
# Browser Management
# =============================================================================

def get_driver(browser: str = 'chrome', headless: bool = False) -> WebDriver:
    """
    Initialize and return a WebDriver instance.
    
    Creates a configured WebDriver for the specified browser with
    optional headless mode support.
    
    Args:
        browser: Browser type - 'chrome', 'firefox', or 'edge'.
        headless: If True, run browser in headless mode.
    
    Returns:
        Configured WebDriver instance.
    
    Raises:
        BrowserInitError: If browser initialization fails.
        ValueError: If an unsupported browser is specified.
    """
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Unsupported browser: {browser}. Must be one of: {', '.join(SUPPORTED_BROWSERS)}")
    
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
        
        # Fallback (should not reach here due to validation above)
        return webdriver.Chrome()
        
    except WebDriverException as e:
        raise BrowserInitError(
            f"Failed to initialize {browser} browser. "
            f"Ensure the browser and its driver are installed. Error: {e}"
        ) from e

def inject_element_selector(driver: WebDriver, element_type: str = 'INPUT FIELD') -> None:
    """
    Inject JavaScript for interactive element selection.
    
    Injects a JavaScript overlay into the page that allows the user
    to visually select elements by clicking on them.
    
    Args:
        driver: WebDriver instance with an active page.
        element_type: Description of the element type being selected.
    """
    js = ELEMENT_SELECTOR_JS.replace('%ELEMENT_TYPE%', element_type)
    driver.execute_script(js)


def get_selected_element(driver: WebDriver) -> Optional[dict[str, str]]:
    """
    Get the selected element info from browser.
    
    Retrieves information about the element selected by the user
    via the injected JavaScript selector.
    
    Args:
        driver: WebDriver instance.
    
    Returns:
        Dictionary with 'xpath', 'tag', 'id', and 'className' keys,
        or None if no element has been selected.
    """
    try:
        result = driver.execute_script("return window.__selectedElementInfo;")
        return result
    except WebDriverException:
        return None


# =============================================================================
# Row Processing
# =============================================================================

def process_row(
    driver: WebDriver,
    value: str,
    input_xpath: str,
    submit_xpath: str,
    retry_count: int = 0,
    max_retries: int = DEFAULT_MAX_RETRIES
) -> tuple[bool, Optional[str]]:
    """
    Process a single data row with retry logic.
    
    Enters the value into the input field and clicks the submit button.
    Automatically retries on failure up to the specified limit.
    
    Args:
        driver: WebDriver instance.
        value: Value to enter into the input field.
        input_xpath: XPath selector for the input element.
        submit_xpath: XPath selector for the submit button.
        retry_count: Current retry attempt (used internally).
        max_retries: Maximum number of retry attempts.
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str]).
    """
    try:
        # Find and populate input element
        input_elem = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, input_xpath))
        )
        input_elem.clear()
        input_elem.send_keys(str(value))
        
        time.sleep(0.3)  # Brief pause for input registration
        
        # Find and click submit button
        submit_elem = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, submit_xpath))
        )
        submit_elem.click()
        
        return True, None
        
    except TimeoutException as e:
        error_msg = f"Timeout waiting for element: {e}"
    except NoSuchElementException as e:
        error_msg = f"Element not found: {e}"
    except WebDriverException as e:
        error_msg = f"Browser error: {e}"
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
    
    # Retry logic
    if retry_count < max_retries:
        time.sleep(1)  # Wait before retry
        return process_row(
            driver, value, input_xpath, submit_xpath,
            retry_count + 1, max_retries
        )
    
    return False, error_msg


# =============================================================================
# Main Automation Logic
# =============================================================================

def run_automation(column_name: str) -> None:
    """
    Main automation loop - runs in background thread.
    
    Orchestrates the complete automation workflow including browser
    initialization, element selection, and data processing.
    
    Args:
        column_name: Name of the DataFrame column containing values to process.
    """
    state = automation_state
    config = state.config
    
    try:
        with state_lock:
            state.stats.reset()
            state.failed_rows = []
        
        log_message('Initializing browser...', 'info')
        state.driver = get_driver(config.browser, config.headless)
        
        log_message(f'Navigating to: {config.url}', 'info')
        state.driver.get(config.url)
        time.sleep(2)
        
        # Element selection phase - Input field
        log_message('⚠️ Click on the INPUT FIELD in the browser window', 'warning')
        inject_element_selector(state.driver, 'INPUT FIELD')
        socketio.emit('wait_for_element', {'type': 'input'})
        
        # Wait for element selection
        while not state.input_selected and not state.should_stop:
            elem_info = get_selected_element(state.driver)
            if elem_info:
                state.element_xpath = elem_info['xpath']
                state.input_selected = True
                elem_id_display = f" #{elem_info['id']}" if elem_info.get('id') else ''
                log_message(f"✅ Input field selected: {elem_info['tag']}{elem_id_display}", 'success')
            time.sleep(0.5)
        
        if state.should_stop:
            raise AutomationError('Automation stopped by user')
        
        time.sleep(1)
        
        # Element selection phase - Submit button
        log_message('⚠️ Now click on the SUBMIT BUTTON in the browser window', 'warning')
        inject_element_selector(state.driver, 'SUBMIT BUTTON')
        socketio.emit('wait_for_element', {'type': 'submit'})
        
        while not state.submit_selected and not state.should_stop:
            elem_info = get_selected_element(state.driver)
            if elem_info:
                state.submit_xpath = elem_info['xpath']
                state.submit_selected = True
                elem_id_display = f" #{elem_info['id']}" if elem_info.get('id') else ''
                log_message(f"✅ Submit button selected: {elem_info['tag']}{elem_id_display}", 'success')
            time.sleep(0.5)
        
        if state.should_stop:
            raise AutomationError('Automation stopped by user')
        
        socketio.emit('elements_confirmed')
        log_message('Starting data processing...', 'info')
        
        # Get data range
        data = state.data
        if data is None:
            raise AutomationError('No data loaded')
        
        start = config.start_row
        end = config.end_row if config.end_row != -1 else len(data)
        data_subset = data.iloc[start:end]
        total = len(data_subset)
        
        with state_lock:
            state.stats.total = total
        
        # Process each row
        for idx, (index, row) in enumerate(data_subset.iterrows()):
            if state.should_stop:
                log_message('Automation stopped by user', 'warning')
                break
            
            while state.is_paused and not state.should_stop:
                time.sleep(0.5)
            
            value = str(row[column_name])
            state.stats.current = idx + 1
            
            max_retries = config.max_retries if config.retry_failed else 0
            
            success, error = process_row(
                state.driver,
                value,
                state.element_xpath,
                state.submit_xpath,
                max_retries=max_retries
            )
            
            # Truncate value for logging
            display_value = value[:VALUE_TRUNCATE_LENGTH]
            if len(value) > VALUE_TRUNCATE_LENGTH:
                display_value += "..."
            
            if success:
                with state_lock:
                    state.stats.success += 1
                log_message(f'Row {index + 1}: {display_value}', 'success')
            else:
                with state_lock:
                    state.stats.failed += 1
                    state.failed_rows.append(FailedRow(
                        index=index,
                        value=value,
                        error=error or 'Unknown error'
                    ))
                log_message(f'Row {index + 1} failed: {error}', 'error')
            
            update_progress(
                idx + 1, total,
                state.stats.success,
                state.stats.failed
            )
            
            time.sleep(config.delay)
        
        # Summary
        log_message('═' * 40, 'info')
        log_message(
            f'✅ Completed! Success: {state.stats.success}, Failed: {state.stats.failed}',
            'success'
        )
        
        if state.failed_rows:
            log_message(
                f'⚠️ {len(state.failed_rows)} rows failed. Check failed rows for details.',
                'warning'
            )
        
        socketio.emit('automation_complete', {
            **state.stats.to_dict(),
            'failed_rows': [fr.to_dict() for fr in state.failed_rows]
        })
        socketio.emit('play_sound', {'type': 'complete'})
        
    except BrowserInitError as e:
        log_message(f'Browser Error: {e}', 'error')
        socketio.emit('automation_error', {'error': str(e)})
        socketio.emit('play_sound', {'type': 'error'})
    except AutomationError as e:
        log_message(f'Automation Error: {e}', 'error')
        socketio.emit('automation_error', {'error': str(e)})
        socketio.emit('play_sound', {'type': 'error'})
    except Exception as e:
        log_message(f'Unexpected Error: {e}', 'error')
        socketio.emit('automation_error', {'error': str(e)})
        socketio.emit('play_sound', {'type': 'error'})
    
    finally:
        # Clean up driver
        if state.driver:
            try:
                state.driver.quit()
            except WebDriverException:
                pass  # Ignore errors during cleanup
            state.driver = None
        
        with state_lock:
            state.cleanup_after_run()
        socketio.emit('automation_stopped')


# =============================================================================
# File Management
# =============================================================================

def cleanup_uploads() -> None:
    """
    Clean up old uploaded files.
    
    Removes files from the upload directory that are older than
    FILE_CLEANUP_AGE_SECONDS (default: 1 hour).
    """
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    try:
        for filepath in upload_dir.iterdir():
            if filepath.is_file():
                file_age = time.time() - filepath.stat().st_mtime
                if file_age > FILE_CLEANUP_AGE_SECONDS:
                    filepath.unlink()
    except OSError as e:
        log_message(f"Failed to cleanup uploads: {e}", 'warning')


def validate_excel_file(filename: str) -> None:
    """
    Validate that the uploaded file is an Excel file.
    
    Args:
        filename: Name of the uploaded file.
    
    Raises:
        FileValidationError: If the file extension is not allowed.
    """
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Invalid file type '{file_ext}'. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


# =============================================================================
# Flask Routes
# =============================================================================


@app.route('/favicon.ico')
def favicon() -> Response:
    """
    Serve favicon to prevent 404 errors.
    
    Returns:
        SVG favicon as a Response object.
    """
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="#3b82f6"/>
        <text x="50" y="65" font-size="50" text-anchor="middle" fill="white">⚡</text>
    </svg>'''
    return Response(svg, mimetype='image/svg+xml')


@app.route('/')
def index() -> str:
    """
    Serve the main page.
    
    Returns:
        Rendered HTML template.
    """
    load_config()
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file() -> tuple[Response, int] | Response:
    """
    Handle Excel file upload.
    
    Accepts multipart form data with an Excel file, validates it,
    and stores it for processing.
    
    Returns:
        JSON response with file info or error message.
    """
    cleanup_uploads()  # Clean old files
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        validate_excel_file(file.filename)
    except FileValidationError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(filepath))
        
        df = pd.read_excel(filepath)
        
        # Get preview data
        preview = df.head(PREVIEW_ROW_COUNT).to_dict('records')
        
        file_info = FileInfo(
            name=filename,
            rows=len(df),
            columns=list(df.columns),
            size=filepath.stat().st_size,
            preview=preview
        )
        
        with state_lock:
            automation_state.data = df
            automation_state.file_path = str(filepath)
            automation_state.file_info = file_info
        
        return jsonify({
            'success': True,
            'file': file_info.to_dict()
        })
    
    except pd.errors.EmptyDataError:
        return jsonify({'error': 'The Excel file is empty'}), 400
    except pd.errors.ParserError as e:
        return jsonify({'error': f'Failed to parse Excel file: {e}'}), 400
    except OSError as e:
        return jsonify({'error': f'File system error: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500


@app.route('/api/clear-file', methods=['POST'])
def clear_file() -> Response:
    """
    Clear the uploaded file.
    
    Removes the uploaded file from disk and clears the state.
    
    Returns:
        JSON response confirming success.
    """
    with state_lock:
        if automation_state.file_path:
            file_path = Path(automation_state.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass  # Ignore errors during cleanup
        automation_state.data = None
        automation_state.file_info = None
        automation_state.file_path = None
    return jsonify({'success': True})


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config() -> Response:
    """
    Get or update configuration.
    
    GET: Returns current configuration.
    POST: Updates configuration with provided values.
    
    Returns:
        JSON response with configuration data.
    """
    if request.method == 'GET':
        return jsonify(automation_state.config.to_dict())
    
    data = request.json or {}
    with state_lock:
        # Update config with new values
        current_config = automation_state.config.to_dict()
        current_config.update(data)
        automation_state.config = AutomationConfig.from_dict(current_config)
    save_config()
    return jsonify({'success': True, 'config': automation_state.config.to_dict()})


@app.route('/api/start', methods=['POST'])
def start_automation() -> tuple[Response, int] | Response:
    """
    Start the automation process.
    
    Validates input and starts the automation in a background thread.
    
    Returns:
        JSON response confirming start or error message.
    """
    if automation_state.is_running:
        return jsonify({'error': 'Automation already running'}), 400
    
    if automation_state.data is None:
        return jsonify({'error': 'No data loaded. Please upload an Excel file first.'}), 400
    
    data = request.json or {}
    column = data.get('column')
    
    if not column:
        return jsonify({'error': 'No column selected'}), 400
    
    if column not in automation_state.data.columns:
        return jsonify({'error': f'Column "{column}" not found in data'}), 400
    
    # Validate configuration
    config_errors = automation_state.config.validate()
    if config_errors:
        return jsonify({'error': '; '.join(config_errors)}), 400
    
    with state_lock:
        automation_state.reset_for_new_run()
    
    thread = threading.Thread(target=run_automation, args=(column,), daemon=True)
    thread.start()
    
    return jsonify({'success': True})


@app.route('/api/stop', methods=['POST'])
def stop_automation() -> Response:
    """
    Stop the automation process.
    
    Signals the automation loop to stop at the next opportunity.
    
    Returns:
        JSON response confirming the stop signal was sent.
    """
    with state_lock:
        automation_state.should_stop = True
    return jsonify({'success': True})


@app.route('/api/pause', methods=['POST'])
def toggle_pause() -> Response:
    """
    Toggle pause state.
    
    Pauses or resumes the automation process.
    
    Returns:
        JSON response with current pause state.
    """
    with state_lock:
        automation_state.is_paused = not automation_state.is_paused
    return jsonify({'paused': automation_state.is_paused})


@app.route('/api/confirm-element', methods=['POST'])
def confirm_element() -> Response:
    """
    Confirm element selection from browser.
    
    Called by the frontend when an element is selected in the browser.
    
    Returns:
        JSON response confirming the element was recorded.
    """
    data = request.json or {}
    elem_type = data.get('type')
    
    with state_lock:
        if elem_type == 'input':
            automation_state.input_selected = True
        elif elem_type == 'submit':
            automation_state.submit_selected = True
    
    return jsonify({'success': True})


@app.route('/api/status', methods=['GET'])
def get_status() -> Response:
    """
    Get current automation status.
    
    Returns comprehensive state information including running status,
    statistics, file info, and configuration.
    
    Returns:
        JSON response with current status.
    """
    return jsonify({
        'is_running': automation_state.is_running,
        'is_paused': automation_state.is_paused,
        'stats': automation_state.stats.to_dict(),
        'file_info': automation_state.file_info.to_dict() if automation_state.file_info else None,
        'config': automation_state.config.to_dict()
    })


@app.route('/api/logs', methods=['GET'])
def get_logs() -> Response:
    """
    Get all logs.
    
    Returns:
        JSON response with list of log entries.
    """
    return jsonify({'logs': [log.to_dict() for log in automation_state.logs]})


@app.route('/api/export-logs', methods=['GET'])
def export_logs() -> Response:
    """
    Export logs as a text file.
    
    Generates a timestamped log file and returns it as a download.
    
    Returns:
        File download response.
    """
    logs = automation_state.logs
    log_lines = [
        f"[{log.timestamp}] [{log.level.upper()}] {log.message}"
        for log in logs
    ]
    content = '\n'.join(log_lines)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"automation_log_{timestamp}.txt"
    filepath = Path(app.config['UPLOAD_FOLDER']) / filename
    
    with filepath.open('w', encoding='utf-8') as f:
        f.write("Web Automation Tool - Log Export\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write('=' * 50 + '\n\n')
        f.write(content)
    
    return send_file(str(filepath), as_attachment=True, download_name=filename)


@app.route('/api/failed-rows', methods=['GET'])
def get_failed_rows() -> Response:
    """
    Get list of failed rows.
    
    Returns:
        JSON response with list of failed row details.
    """
    return jsonify({
        'failed_rows': [fr.to_dict() for fr in automation_state.failed_rows]
    })


@app.route('/api/retry-failed', methods=['POST'])
def retry_failed() -> tuple[Response, int] | Response:
    """
    Retry failed rows.
    
    Returns:
        JSON response with instructions or error.
    """
    if automation_state.is_running:
        return jsonify({'error': 'Automation already running'}), 400
    
    if not automation_state.failed_rows:
        return jsonify({'error': 'No failed rows to retry'}), 400
    
    return jsonify({'success': True, 'message': 'Use the main automation with retry enabled'})


@app.route('/api/export-failed', methods=['GET'])
def export_failed_rows() -> Response:
    """
    Export failed rows as CSV file.
    
    Returns:
        CSV file download response.
    """
    failed_rows = automation_state.failed_rows
    
    if not failed_rows:
        return jsonify({'error': 'No failed rows to export'}), 404
    
    csv_content = "Row,Value,Error\n"
    for row in failed_rows:
        # Escape quotes in values
        value = str(row.value).replace('"', '""')
        error = str(row.error).replace('"', '""')
        csv_content += f'{row.index + 1},"{value}","{error}"\n'
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"failed_rows_{timestamp}.csv"
    
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@socketio.on('connect')
def handle_connect() -> None:
    """
    Handle WebSocket connection.
    
    Sends initial connection confirmation and current configuration
    to the newly connected client.
    """
    emit('connected', {
        'status': 'Connected to server',
        'config': automation_state.config.to_dict()
    })


# =============================================================================
# Application Entry Point
# =============================================================================

def print_banner() -> None:
    """Print a colorful startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🤖  WEB AUTOMATION TOOL  v3.1                             ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                           ║
║                                                              ║
║   🌐  URL: http://localhost:5000                            ║
║   📁  Upload Excel files to automate data entry             ║
║   ⌨️   Press Ctrl+C to stop the server                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def open_browser_delayed(url: str, delay: float = 1.5) -> None:
    """Open browser after a short delay to ensure server is ready."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


if __name__ == '__main__':
    load_config()
    print_banner()
    
    # Auto-open browser
    open_browser_delayed('http://localhost:5000')
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print('\n\n👋 Server stopped. Goodbye!')
