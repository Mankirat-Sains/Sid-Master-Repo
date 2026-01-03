"""
Enhanced logging system for RAG debugging
Provides web-based log visualization with function tracking and chunk flow monitoring
"""

import functools
import json
import logging
import threading
import time
import traceback
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi.responses import HTMLResponse


class EnhancedLogCapture:
    """Enhanced log capture with function tracking and step-by-step visualization"""
    def __init__(self, max_logs=2000):
        self.logs = deque(maxlen=max_logs)
        self.function_calls = deque(maxlen=500)
        self.chunk_flow = deque(maxlen=1000)
        self.lock = threading.Lock()
        
    def add_log(self, level, logger_name, message, timestamp=None, extra_data=None):
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            self.logs.append({
                'timestamp': timestamp.isoformat(),
                'level': level,
                'logger': logger_name,
                'message': message,
                'extra_data': extra_data or {}
            })
    
    def add_function_call(self, function_name, args=None, kwargs=None, duration=None, result_type=None):
        with self.lock:
            self.function_calls.append({
                'timestamp': datetime.now().isoformat(),
                'function': function_name,
                'args': args or {},
                'kwargs': kwargs or {},
                'duration': duration,
                'result_type': result_type
            })
    
    def add_chunk_step(self, step_name, chunk_count, projects=None, details=None):
        with self.lock:
            self.chunk_flow.append({
                'timestamp': datetime.now().isoformat(),
                'step': step_name,
                'chunk_count': chunk_count,
                'projects': projects or [],
                'details': details or {}
            })
    
    def get_logs(self, level_filter=None, logger_filter=None, limit=100):
        with self.lock:
            logs = list(self.logs)
        
        if level_filter:
            logs = [log for log in logs if log['level'].lower() == level_filter.lower()]
        if logger_filter:
            logs = [log for log in logs if logger_filter.lower() in log['logger'].lower()]
        
        return logs[-limit:] if limit else logs
    
    def get_function_calls(self, limit=50):
        with self.lock:
            return list(self.function_calls)[-limit:]
    
    def get_chunk_flow(self, limit=100):
        with self.lock:
            return list(self.chunk_flow)[-limit:]
    
    def clear_all(self):
        with self.lock:
            self.logs.clear()
            self.function_calls.clear()
            self.chunk_flow.clear()


# Global enhanced log capture
enhanced_log_capture = EnhancedLogCapture()


class EnhancedWebLogHandler(logging.Handler):
    """Enhanced log handler that captures logs with emoji categorization"""
    def emit(self, record):
        # Extract emoji and categorize the log
        message = record.getMessage()
        emoji = ""
        category = "general"
        
        if "💭" in message:
            emoji = "💭"
            category = "conversation"
        elif "🔍" in message:
            emoji = "🔍"
            category = "search"
        elif "🗓️" in message:
            emoji = "🗓️"
            category = "filtering"
        elif "📦" in message:
            emoji = "📦"
            category = "chunks"
        elif "📄" in message:
            emoji = "📄"
            category = "preview"
        elif "📊" in message:
            emoji = "📊"
            category = "stats"
        
        enhanced_log_capture.add_log(
            level=record.levelname,
            logger_name=record.name,
            message=message,
            timestamp=datetime.fromtimestamp(record.created),
            extra_data={
                'emoji': emoji,
                'category': category,
                'file': record.filename,
                'line': record.lineno
            }
        )


def track_function(func):
    """Decorator to track function calls with timing and result information"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = f"{func.__module__}.{func.__name__}"
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Determine result type
            result_type = type(result).__name__
            if hasattr(result, '__len__'):
                result_type += f" (len={len(result)})"
            
            enhanced_log_capture.add_function_call(
                function_name=function_name,
                args={f"arg_{i}": str(arg)[:100] for i, arg in enumerate(args)},
                kwargs={k: str(v)[:100] for k, v in kwargs.items()},
                duration=duration,
                result_type=result_type
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            enhanced_log_capture.add_function_call(
                function_name=function_name,
                args={f"arg_{i}": str(arg)[:100] for i, arg in enumerate(args)},
                kwargs={k: str(v)[:100] for k, v in kwargs.items()},
                duration=duration,
                result_type=f"ERROR: {str(e)}"
            )
            raise
    
    return wrapper


def setup_enhanced_logging():
    """Set up enhanced logging handlers for all RAG loggers"""
    enhanced_log_handler = EnhancedWebLogHandler()
    enhanced_log_handler.setLevel(logging.DEBUG)

    # Add to all loggers
    for logger_name in ["", "QUERY_FLOW", "ROUTING", "DATABASE", "ENHANCEMENT", "SYNTHESIS"]:
        logging.getLogger(logger_name).addHandler(enhanced_log_handler)


async def render_enhanced_log_html(logs, level_filter, logger_filter, category_filter, limit):
    """Render enhanced HTML with function tracking and chunk visualization"""
    
    function_calls = enhanced_log_capture.get_function_calls(30)
    chunk_flow = enhanced_log_capture.get_chunk_flow(50)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced RAG System Debugger</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #0d1117; color: #c9d1d9; }}
            .header {{ background: #161b22; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #30363d; }}
            .controls {{ background: #161b22; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #30363d; }}
            .controls input, .controls select {{ margin: 5px; padding: 8px; background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; }}
            .controls button {{ margin: 5px; padding: 8px 16px; background: #238636; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            .controls button:hover {{ background: #2ea043; }}
            .controls button.danger {{ background: #da3633; }}
            .controls button.danger:hover {{ background: #f85149; }}
            
            .tabs {{ display: flex; margin-bottom: 20px; }}
            .tab {{ padding: 10px 20px; background: #21262d; border: 1px solid #30363d; cursor: pointer; border-radius: 4px 4px 0 0; }}
            .tab.active {{ background: #161b22; border-bottom: none; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            
            .log-entry {{ margin: 8px 0; padding: 12px; border-radius: 6px; border-left: 4px solid; }}
            .log-entry.DEBUG {{ border-left-color: #7c3aed; background: #1a0b2e; }}
            .log-entry.INFO {{ border-left-color: #0ea5e9; background: #0c1e3a; }}
            .log-entry.WARNING {{ border-left-color: #f59e0b; background: #3a2a00; }}
            .log-entry.ERROR {{ border-left-color: #ef4444; background: #3a0000; }}
            
            .timestamp {{ color: #7d8590; font-size: 0.85em; }}
            .logger {{ color: #58a6ff; font-weight: bold; }}
            .level {{ color: #f0f6fc; font-weight: bold; }}
            .emoji {{ font-size: 1.2em; margin-right: 8px; }}
            .message {{ margin-top: 8px; white-space: pre-wrap; font-family: 'Courier New', monospace; }}
            .extra-info {{ margin-top: 8px; font-size: 0.9em; color: #7d8590; }}
            
            .function-call {{ margin: 6px 0; padding: 10px; background: #21262d; border-radius: 4px; border-left: 3px solid #58a6ff; }}
            .function-name {{ color: #58a6ff; font-weight: bold; }}
            .function-duration {{ color: #7d8590; font-size: 0.9em; }}
            .function-result {{ color: #7c3aed; font-size: 0.9em; }}
            
            .chunk-step {{ margin: 6px 0; padding: 10px; background: #21262d; border-radius: 4px; border-left: 3px solid #f59e0b; }}
            .step-name {{ color: #f59e0b; font-weight: bold; }}
            .chunk-count {{ color: #7d8590; font-size: 0.9em; }}
            .projects {{ color: #7c3aed; font-size: 0.9em; }}
            
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
            .stat-card {{ background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #58a6ff; }}
            .stat-label {{ color: #7d8590; font-size: 0.9em; }}
        </style>
        <script>
            function showTab(tabName) {{
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                document.querySelector(`[data-tab="${{tabName}}"]`).classList.add('active');
                document.querySelector(`#${{tabName}}`).classList.add('active');
            }}
            
            function refreshLogs() {{
                const level = document.getElementById('level').value;
                const logger = document.getElementById('logger').value;
                const category = document.getElementById('category').value;
                const limit = document.getElementById('limit').value;
                const url = `/logs/enhanced?format=html&level=${{level}}&logger=${{logger}}&category=${{category}}&limit=${{limit}}`;
                window.location.href = url;
            }}
            
            function clearLogs() {{
                if (confirm('Clear all logs and tracking data?')) {{
                    fetch('/logs/enhanced/clear', {{method: 'POST'}})
                    .then(() => refreshLogs());
                }}
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Enhanced RAG System Debugger</h1>
            <p>Real-time debugging with function tracking and chunk flow visualization</p>
        </div>
        
        <div class="controls">
            <label>Level:</label>
            <select id="level">
                <option value="">All</option>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
            </select>
            
            <label>Logger:</label>
            <select id="logger">
                <option value="">All</option>
                <option value="QUERY_FLOW">QUERY_FLOW</option>
                <option value="ROUTING">ROUTING</option>
                <option value="DATABASE">DATABASE</option>
                <option value="ENHANCEMENT">ENHANCEMENT</option>
                <option value="SYNTHESIS">SYNTHESIS</option>
            </select>
            
            <label>Category:</label>
            <select id="category">
                <option value="">All</option>
                <option value="conversation">💭 Conversation</option>
                <option value="search">🔍 Search</option>
                <option value="filtering">🗓️ Filtering</option>
                <option value="chunks">📦 Chunks</option>
                <option value="preview">📄 Preview</option>
                <option value="stats">📊 Stats</option>
            </select>
            
            <label>Limit:</label>
            <input type="number" id="limit" value="{limit}" min="10" max="1000">
            
            <button onclick="refreshLogs()">🔄 Refresh</button>
            <button onclick="clearLogs()" class="danger">🗑️ Clear All</button>
        </div>
        
        <div class="tabs">
            <div class="tab active" data-tab="logs" onclick="showTab('logs')">📋 Logs</div>
            <div class="tab" data-tab="functions" onclick="showTab('functions')">⚙️ Functions</div>
            <div class="tab" data-tab="chunks" onclick="showTab('chunks')">📦 Chunk Flow</div>
            <div class="tab" data-tab="stats" onclick="showTab('stats')">📊 Statistics</div>
        </div>
        
        <div id="logs" class="tab-content active">
            <h2>📋 System Logs</h2>
    """
    
    # Render logs
    for log in reversed(logs):
        emoji = log.get('extra_data', {}).get('emoji', '')
        category = log.get('extra_data', {}).get('category', 'general')
        file_info = log.get('extra_data', {}).get('file', '')
        line_info = log.get('extra_data', {}).get('line', '')
        
        html_content += f"""
            <div class="log-entry {log['level']}">
                <div class="timestamp">{log['timestamp']}</div>
                <div class="logger">{log['logger']}</div>
                <div class="level">{log['level']}</div>
                <div class="message"><span class="emoji">{emoji}</span>{log['message']}</div>
                <div class="extra-info">File: {file_info}:{line_info} | Category: {category}</div>
            </div>
        """
    
    html_content += """
        </div>
        
        <div id="functions" class="tab-content">
            <h2>⚙️ Function Calls</h2>
    """
    
    # Render function calls
    for func_call in reversed(function_calls):
        html_content += f"""
            <div class="function-call">
                <div class="function-name">{func_call['function']}</div>
                <div class="function-duration">Duration: {func_call['duration']:.3f}s</div>
                <div class="function-result">Result: {func_call['result_type']}</div>
                <div class="extra-info">Args: {json.dumps(func_call['args'], indent=2)}</div>
            </div>
        """
    
    html_content += """
        </div>
        
        <div id="chunks" class="tab-content">
            <h2>📦 Chunk Processing Flow</h2>
    """
    
    # Render chunk flow
    for chunk_step in reversed(chunk_flow):
        projects_str = ', '.join(chunk_step['projects'][:5])
        if len(chunk_step['projects']) > 5:
            projects_str += f" ... (+{len(chunk_step['projects']) - 5} more)"
        
        html_content += f"""
            <div class="chunk-step">
                <div class="step-name">{chunk_step['step']}</div>
                <div class="chunk-count">Chunks: {chunk_step['chunk_count']}</div>
                <div class="projects">Projects: {projects_str}</div>
                <div class="extra-info">{chunk_step['timestamp']}</div>
            </div>
        """
    
    html_content += """
        </div>
        
        <div id="stats" class="tab-content">
            <h2>📊 Statistics</h2>
            <div class="stats-grid">
    """
    
    # Calculate statistics
    total_logs = len(logs)
    error_count = len([log for log in logs if log['level'] == 'ERROR'])
    warning_count = len([log for log in logs if log['level'] == 'WARNING'])
    
    html_content += f"""
                <div class="stat-card">
                    <div class="stat-number">{total_logs}</div>
                    <div class="stat-label">Total Logs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{error_count}</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{warning_count}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(function_calls)}</div>
                    <div class="stat-label">Function Calls</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


def get_enhanced_log_stats():
    """Get comprehensive statistics"""
    logs = enhanced_log_capture.get_logs()
    function_calls = enhanced_log_capture.get_function_calls()
    chunk_flow = enhanced_log_capture.get_chunk_flow()
    
    stats = {
        "logs": {
            "total": len(logs),
            "by_level": {},
            "by_logger": {},
            "by_category": {}
        },
        "functions": {
            "total_calls": len(function_calls),
            "by_function": {},
            "avg_duration": 0,
            "slowest_calls": []
        },
        "chunks": {
            "total_steps": len(chunk_flow),
            "by_step": {},
            "total_chunks_processed": sum(step['chunk_count'] for step in chunk_flow)
        }
    }
    
    # Log statistics
    for log in logs:
        level = log['level']
        logger = log['logger']
        category = log.get('extra_data', {}).get('category', 'general')
        
        stats["logs"]["by_level"][level] = stats["logs"]["by_level"].get(level, 0) + 1
        stats["logs"]["by_logger"][logger] = stats["logs"]["by_logger"].get(logger, 0) + 1
        stats["logs"]["by_category"][category] = stats["logs"]["by_category"].get(category, 0) + 1
    
    # Function statistics
    durations = []
    for func_call in function_calls:
        func_name = func_call['function']
        duration = func_call['duration']
        durations.append(duration)
        
        stats["functions"]["by_function"][func_name] = stats["functions"]["by_function"].get(func_name, 0) + 1
        
        if duration > 0.1:  # Slow calls
            stats["functions"]["slowest_calls"].append({
                "function": func_name,
                "duration": duration,
                "timestamp": func_call['timestamp']
            })
    
    if durations:
        stats["functions"]["avg_duration"] = sum(durations) / len(durations)
    
    # Sort slowest calls
    stats["functions"]["slowest_calls"].sort(key=lambda x: x['duration'], reverse=True)
    stats["functions"]["slowest_calls"] = stats["functions"]["slowest_calls"][:10]
    
    # Chunk statistics
    for chunk_step in chunk_flow:
        step_name = chunk_step['step']
        stats["chunks"]["by_step"][step_name] = stats["chunks"]["by_step"].get(step_name, 0) + 1
    
    return stats


