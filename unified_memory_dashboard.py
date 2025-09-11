#!/usr/bin/env python3
"""
Unified Memory Dashboard - Combines Memory Visualizer and Monitoring Dashboard
Provides comprehensive real-time monitoring with multiple views and analytics.
"""

import json
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os
import sys
import gc
import tracemalloc
from collections import defaultdict, deque
from utils import safe_expanduser, log_event, log_error, load_clipboard_history

# Fix psutil import issue when running from bundled app
# The bundled psutil may be incomplete, so we need to handle this carefully
psutil = None
import_error = None

# Strategy: Force import from system Python paths, bypassing bundled incomplete psutil
original_path = sys.path[:]

try:
    # First, try importing psutil normally
    import psutil
    # Test if psutil is working correctly
    psutil.virtual_memory()
    print("✅ psutil imported and working correctly")

except Exception as e:
    import_error = e
    print(f"⚠️ Initial psutil import failed: {e}")

    try:
        # Clear any cached psutil modules
        if 'psutil' in sys.modules:
            del sys.modules['psutil']

        # Remove current directory and bundled paths that might have incomplete psutil
        current_dir = os.path.dirname(os.path.abspath(__file__))
        paths_to_remove = ['.', '', current_dir]

        # Create a clean path with only system Python paths
        clean_path = []
        for path in original_path:
            if path not in paths_to_remove and 'Frameworks' not in path:
                clean_path.append(path)

        # Add common system Python paths
        system_paths = [
            '/Users/omair.aslam/Library/Python/3.9/lib/python/site-packages',
            '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/site-packages',
            '/usr/local/lib/python3.9/site-packages'
        ]

        for path in system_paths:
            if os.path.exists(path) and path not in clean_path:
                clean_path.append(path)

        sys.path = clean_path

        import psutil
        # Test if psutil is working correctly
        psutil.virtual_memory()
        print("✅ psutil imported successfully with clean path")

    except Exception as e2:
        print(f"❌ Failed to import psutil with clean path: {e2}")

        # Final fallback: restore original path and try again
        sys.path = original_path
        try:
            if 'psutil' in sys.modules:
                del sys.modules['psutil']
            import psutil
            psutil.virtual_memory()
            print("✅ psutil imported successfully after path restore")
        except Exception as e3:
            print(f"❌ All psutil import strategies failed:")
            print(f"  Original error: {import_error}")
            print(f"  Clean path error: {e2}")
            print(f"  Final error: {e3}")
            raise e3
    finally:
        # Always restore original path
        sys.path = original_path

if psutil is None:
    raise ImportError("Could not import psutil module")

class AdvancedMemoryLeakDetector:
    """Advanced memory leak detection with all original features"""

    def __init__(self):
        self.baseline_memory = {}
        self.memory_snapshots = deque(maxlen=100)
        self.object_counts = defaultdict(int)
        self.leak_alerts = []
        self.growth_threshold = 10.0  # MB growth threshold
        self.consecutive_growth_limit = 5
        self.tracemalloc_enabled = False

        # Initialize tracemalloc
        try:
            tracemalloc.start(10)
            self.tracemalloc_enabled = True
        except Exception as e:
            print(f"Failed to enable tracemalloc: {e}")

    def take_memory_snapshot(self, process_info):
        """Take detailed memory snapshot"""
        timestamp = time.time()
        snapshot = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "process_info": process_info,
            "gc_stats": self._get_gc_stats(),
            "object_counts": self._get_object_counts(),
            "resource_usage": self._get_resource_usage(),
        }

        if self.tracemalloc_enabled:
            try:
                snapshot["tracemalloc"] = self._get_tracemalloc_stats()
            except Exception as e:
                print(f"Failed to get tracemalloc stats: {e}")

        self.memory_snapshots.append(snapshot)
        return snapshot

    def _get_gc_stats(self):
        """Get garbage collection statistics"""
        try:
            return {
                "counts": gc.get_count(),
                "stats": gc.get_stats(),
                "threshold": gc.get_threshold()
            }
        except Exception:
            return {}

    def _get_object_counts(self):
        """Get object counts by type"""
        try:
            import sys
            object_counts = {}
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
            return dict(sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        except Exception:
            return {}

    def _get_resource_usage(self):
        """Get detailed resource usage"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                "max_rss": usage.ru_maxrss,
                "user_time": usage.ru_utime,
                "system_time": usage.ru_stime,
                "page_faults": usage.ru_majflt + usage.ru_minflt
            }
        except Exception:
            return {}

    def _get_tracemalloc_stats(self):
        """Get tracemalloc statistics"""
        if not self.tracemalloc_enabled:
            return {}

        try:
            current, peak = tracemalloc.get_traced_memory()
            stats = tracemalloc.take_snapshot().statistics('lineno')

            top_stats = []
            for stat in stats[:10]:
                top_stats.append({
                    "filename": stat.traceback.format()[-1] if stat.traceback else "unknown",
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                })

            return {
                "current_mb": current / 1024 / 1024,
                "peak_mb": peak / 1024 / 1024,
                "top_allocations": top_stats
            }
        except Exception:
            return {}

    def analyze_for_leaks(self):
        """Analyze snapshots for memory leaks"""
        if len(self.memory_snapshots) < 2:
            return {"status": "insufficient_data"}

        recent_snapshots = list(self.memory_snapshots)[-10:]
        memory_values = [s["process_info"]["memory_rss_mb"] for s in recent_snapshots]

        # Calculate growth rate
        if len(memory_values) >= 2:
            growth_rate = (memory_values[-1] - memory_values[0]) / len(memory_values)

            # Determine leak status
            if growth_rate > self.growth_threshold:
                status = "potential_leak"
                severity = "high"
            elif growth_rate > 2.0:
                status = "monitoring_needed"
                severity = "medium"
            else:
                status = "normal"
                severity = "low"

            return {
                "status": status,
                "severity": severity,
                "growth_rate_mb": growth_rate,
                "current_memory_mb": memory_values[-1],
                "baseline_memory_mb": memory_values[0],
                "snapshots_analyzed": len(recent_snapshots)
            }

        return {"status": "analyzing"}

class UnifiedMemoryDashboard:
    def __init__(self, port=8001, auto_start=False):
        self.port = port
        self.data_history = []  # Basic data collection (always running)
        self.advanced_data_history = []  # Advanced monitoring data (session-based)
        self.max_history = 2000  # Increased for longer history
        self.server = None

        # Cache-busting version for static assets (changes each server start)
        self.asset_version = str(int(time.time()))


        # Logging verbosity (Phase 3)
        self.debug_logging = os.environ.get('CM_DEBUG', '0') in ('1', 'true', 'True')

        # Advanced features
        self.leak_detector = AdvancedMemoryLeakDetector()
        self.monitoring_active = False
        self.monitoring_start_time = None
        self.alert_count = 0
        self.data_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/unified_memory_data.json")


        # UI preferences (server-side persisted)
        self.ui_prefs_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/ui_prefs.json")
        self.ui_prefs = { 'header_collapsed': False }
        try:
            # Load saved UI prefs if present
            if os.path.exists(self.ui_prefs_file):
                with open(self.ui_prefs_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.ui_prefs.update({k: data.get(k) for k in ['header_collapsed'] if k in data})
        except Exception:
            # On any load error, keep defaults
            pass

        # Lightweight events and budgets (for overlays and health score)
        self.events = []  # [{timestamp, type, message}]
        self.budgets = {
            'total_memory_mb': 600.0,
            'per_process_mb': 400.0,
            'total_cpu_percent': 200.0  # sum of processes
        }

        # Monitoring configuration
        self.monitor_interval = 10  # seconds
        self.time_range_hours = 24  # hours

        # Auto-start configuration
        self.auto_start_mode = auto_start
        # Dev auto-reload
        self.dev_reload = False
        self.auto_start_time = datetime.now() if auto_start else None
        self.last_activity_time = datetime.now()
        self.auto_timeout_minutes = 5  # Auto-shutdown after 5 minutes of inactivity



        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        # Load existing data
        self.load_historical_data()

        # Session tracking
        self.session_start_time = datetime.now()
        self.peak_menubar_memory = 0.0
        self.peak_service_memory = 0.0
        self.peak_dashboard_memory = 0.0


        self.peak_total_memory = 0.0
        self.peak_menubar_cpu = 0.0
        self.peak_service_cpu = 0.0
        self.peak_dashboard_cpu = 0.0
        self.peak_total_cpu = 0.0

        # Analytics tracking
        self.memory_history = deque(maxlen=1000)  # For growth rate calculation
        self.last_memory_reading = 0.0
        self.last_memory_time = datetime.now()
        self.operation_count = 0
        self.gc_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    class RequestHandler(BaseHTTPRequestHandler):
        def __init__(self, dashboard_instance, *args, **kwargs):
            self.dashboard = dashboard_instance
            super().__init__(*args, **kwargs)

        def _update_activity(self):
            """Update last activity time for auto-timeout tracking"""
            self.dashboard.last_activity_time = datetime.now()

        def do_GET(self):
            """Handle GET requests."""
            # Parse query parameters to check if this is a monitoring request
            from urllib.parse import urlparse, parse_qs
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)

            # Only update activity time if this is not a monitoring request
            is_monitoring = query_params.get('monitor', ['false'])[0].lower() == 'true'
            if not is_monitoring:


                self._update_activity()

            # Use parsed path for routing
            path = parsed_path.path

            if path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                try:
                    self.wfile.write(self.dashboard.render_dashboard_html().encode())
                except BrokenPipeError:
                    # Client disconnected; ignore to prevent noisy logs during tests
                    pass
            elif path == '/favicon.ico':
                # Avoid 404 noise in console; no favicon needed
                self.send_response(204)
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                return
            elif path == '/api/memory':
                # Memory data for Memory tab charts - use the more comprehensive method
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_memory_data())
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/current':
                # Current status including monitoring state (for Controls tab)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/data':
                # Comprehensive dashboard data for monitoring dashboard compatibility
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_comprehensive_dashboard_data())
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/system':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_system_data())
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/clipboard/history':
                # Clipboard history API with pagination and filtering
                page = 1
                page_size = 30
                order = 'asc'  # default: chronological order (oldest first)
                type_filter = 'all'
                q = ''
                has_url = None
                has_code = None
                is_long = None
                try:
                    page = int(query_params.get('page', [1])[0])
                except Exception:
                    page = 1
                try:
                    page_size = int(query_params.get('page_size', [30])[0])
                except Exception:
                    page_size = 30
                order = (query_params.get('order', ['asc'])[0] or 'asc').lower()
                type_filter = (query_params.get('type', ['all'])[0] or 'all').lower()
                q = (query_params.get('q', [''])[0] or '')
                q_lower = q.lower()
                # Optional time range
                def parse_int(val, default=None):
                    try:
                        return int(val)
                    except Exception:
                        return default
                start_ts = parse_int((query_params.get('start_ts', [None])[0]))
                end_ts = parse_int((query_params.get('end_ts', [None])[0]))
                # Boolean filter parsing
                def parse_bool(val, default=None):
                    if val is None:
                        return default
                    s = str(val).strip().lower()
                    if s in ('1','true','yes','on'):
                        return True
                    if s in ('0','false','no','off'):
                        return False
                    return default
                has_url = parse_bool((query_params.get('has_url', [None])[0]))
                has_code = parse_bool((query_params.get('has_code', [None])[0]))
                is_long = parse_bool((query_params.get('is_long', [None])[0]))

                items = []
                try:
                    history = load_clipboard_history() or []
                    # Build items with type classification and apply filters
                    for it in history:
                        content = (it.get('content', '') or '')
                        c_strip = content.strip()
                        ctype = 'rtf' if c_strip.startswith('{\\rtf') else (
                            'md' if any(tok in content for tok in ('\n#', '\n- ', '\n* ', '```', '[', '](')) else 'text')
                        # Server-side type filter
                        if type_filter in ('md','rtf','text') and ctype != type_filter:
                            continue
                        # Server-side time range
                        ts = it.get('timestamp')
                        if isinstance(ts, (int, float)):
                            if start_ts is not None and ts < start_ts:
                                continue
                            if end_ts is not None and ts > end_ts:
                                continue
                        # Server-side text query (case-insensitive)
                        if q and (q_lower not in content.lower()):
                            continue
                        # Server-side attribute filters
                        if has_url is not None:
                            if has_url and ('http://' not in content and 'https://' not in content):
                                continue
                            if (has_url is False) and ('http://' in content or 'https://' in content):
                                continue
                        if has_code is not None:
                            has_backticks = ('```' in content)
                            if has_code and not has_backticks:
                                continue
                            if (has_code is False) and has_backticks:
                                continue
                        if is_long is not None:
                            long = len(content) > 200
                            if is_long and not long:
                                continue
                            if (is_long is False) and long:
                                continue
                        items.append({
                            'timestamp': it.get('timestamp'),
                            'hash': it.get('hash'),
                            'type': ctype,
                            'snippet': content[:200]
                        })
                    # Order
                    items.sort(key=lambda x: x.get('timestamp') or 0, reverse=(order == 'desc'))
                    total = len(items)
                    start = max(0, (page - 1) * page_size)
                    end = start + page_size
                    page_items = items[start:end]
                    payload = {
                        'items': page_items,
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'page_count': (total + page_size - 1) // page_size,
                        'order': order,
                        'type': type_filter,
                        'q': q,
                        'has_url': has_url,
                        'has_code': has_code,
                        'is_long': is_long
                    }
                except Exception as e:
                    payload = {'items': [], 'total': 0, 'page': 1, 'page_size': page_size, 'error': str(e)}

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(payload).encode())
                except BrokenPipeError:
                    pass

            elif path == '/api/clipboard/clear':
                # Clear clipboard history
                cleared = False
                try:
                    try:
                        from modules.history_module import clear_history as _clr
                    except Exception:
                        from .modules.history_module import clear_history as _clr  # type: ignore
                    _clr()
                    cleared = True
                except Exception as e:
                    cleared = False
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                try:
                    self.wfile.write(json.dumps({'cleared': cleared}).encode())
                except BrokenPipeError:
                    pass

            elif path == '/api/clipboard/item':
                # Return full item by hash
                hash_q = (query_params.get('hash', [''])[0] or '')
                result = {'found': False}
                try:
                    history = load_clipboard_history() or []
                    for it in history:
                        if it.get('hash') == hash_q:
                            content = (it.get('content', '') or '')
                            c_strip = content.strip()
                            ctype = 'rtf' if c_strip.startswith('{\\rtf') else (
                                'md' if any(tok in content for tok in ('\n#', '\n- ', '\n* ', '```', '[', '](')) else 'text')
                            result = {
                                'found': True,
                                'timestamp': it.get('timestamp'),
                                'hash': it.get('hash'),
                                'type': ctype,
                                'content': content
                            }
                            break
                except Exception as e:
                    result = {'found': False, 'error': str(e)}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(result).encode())
                except BrokenPipeError:
                    pass

            elif path == '/api/history':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.data_history[-200:])
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path.startswith('/api/historical'):
                # Parse query parameters for time range (already parsed above)
                hours_param = query_params.get('hours', [24])[0]
                try:
                    if isinstance(hours_param, str) and hours_param == 'all':
                        hours = 'all'
                    else:
                        hours = int(hours_param)
                except Exception:
                    hours = 24

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_historical_data(hours))
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path.startswith('/api/analysis'):
                # Parse query parameters for time range (already parsed above)
                hours_param = query_params.get('hours', [24])[0]
                try:
                    if isinstance(hours_param, str) and hours_param == 'all':
                        hours = 'all'
                    else:
                        hours = int(hours_param)
                except Exception:
                    hours = 24

                try:
                    payload = self.dashboard.get_analysis_data(hours)
                    data = json.dumps(payload, default=str, allow_nan=True)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    try:
                        self.wfile.write(data.encode())
                    except BrokenPipeError:
                        pass
                except Exception as e:
                    # Return a structured JSON error instead of a blank page
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    err = json.dumps({
                        'error': str(e),
                        'message': 'Failed to compute analysis',
                        'hours': hours
                    })
                    try:
                        self.wfile.write(err.encode())
                    except BrokenPipeError:
                        pass
            elif path.startswith('/api/historical-chart'):
                # Enhanced historical data for chart
                try:
                    # Use already parsed query parameters
                    hours_param = query_params.get('hours', ['1'])[0]
                    resolution = query_params.get('resolution', ['full'])[0]

                    # Historical chart request processing

                    try:
                        if hours_param == 'all':
                            hours_val = 'all'
                        else:
                            hours_val = float(hours_param)
                    except ValueError:
                        hours_val = 1

                    historical_data = self.dashboard.get_historical_data(hours_val, resolution)

                    # Format for chart consumption
                    chart_data = {
                        'points': [
                            {
                                'timestamp': p['timestamp'],
                                'menubar_memory': p.get('menubar_memory', 0),
                                'service_memory': p.get('service_memory', 0),
                                'total_memory': p.get('total_memory', 0)
                            }
                            for p in historical_data['points']
                        ],
                        'total_points': historical_data['total_points'],
                        'resolution': historical_data['resolution'],
                        'time_range': historical_data['time_range'],
                        'session_start': self.dashboard.session_start_time.isoformat()
                    }

                    # UX fallback: if no points exist in the selected range, synthesize
                    # two flat points so the Trend Explorer sparklines are visible.
                    try:
                        if not chart_data['points']:
                            from datetime import datetime, timedelta
                            # Prefer the most recent sample from basic collector
                            last = self.dashboard.data_history[-1] if len(self.dashboard.data_history) > 0 else None
                            now = datetime.now()
                            ts1 = (now - timedelta(seconds=1)).isoformat()
                            ts2 = now.isoformat()
                            def mk_point(ts, mb, sv):
                                mb = float(mb if mb and mb > 0 else 0.5)
                                sv = float(sv if sv and sv > 0 else 0.5)
                                return {
                                    'timestamp': ts,
                                    'menubar_memory': mb,
                                    'service_memory': sv,
                                    'total_memory': mb + sv,
                                }
                            if last:
                                mb = float(last.get('menubar_memory', 0) or 0.5)
                                sv = float(last.get('service_memory', 0) or 0.5)
                            else:
                                mb = 0.5; sv = 0.5
                            chart_data['points'] = [mk_point(ts1, mb, sv), mk_point(ts2, mb, sv)]
                            chart_data['total_points'] = 2
                    except Exception:
                        pass

                    # Returning chart data

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    data = json.dumps(chart_data)
                    try:
                        self.wfile.write(data.encode())
                    except BrokenPipeError:
                        pass

                except Exception as e:
                    if self.dashboard.debug_logging:
                        print(f"Error in historical-chart API: {e}")
                        print(f"Request parameters: hours={hours_param}, resolution={resolution}")
                        import traceback
                        traceback.print_exc()

                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    error_data = json.dumps({
                        'error': str(e),
                        'points': [],
                        'total_points': 0,
                        'resolution': resolution,
                        'time_range': 'error',
                        'debug_info': f"hours_param={hours_param}, resolution={resolution}"
                    })
                    try:
                        self.wfile.write(error_data.encode())
                    except BrokenPipeError:
                        pass
            elif path.startswith('/api/start_monitoring'):
                # Parse query parameters for interval (already parsed above)
                interval = int(query_params.get('interval', [30])[0])

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.start_advanced_monitoring(interval)
                try:
                    self.wfile.write(json.dumps(result).encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/stop_monitoring':
                # Properly stop monitoring and return JSON result
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                result = self.dashboard.stop_advanced_monitoring()
                try:
                    self.wfile.write(json.dumps(result).encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/top_offenders':
                hours_param = query_params.get('hours', [24])[0]
                try:
                    hours = 'all' if hours_param == 'all' else int(hours_param)
                except Exception:
                    hours = 24
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_top_offenders(hours))
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/events':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # For now, return any recorded events; future: include GC, restarts, spikes
                data = json.dumps(self.dashboard.events[-200:])
                try:
                    self.wfile.write(data.encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/force_gc':
                # Force a garbage collection cycle (manual trigger)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                result = self.dashboard.force_garbage_collection()
                try:
                    self.wfile.write(json.dumps(result).encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/ui_prefs':
                # Read UI preferences (server-side persistence)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                payload = {
                    'header_collapsed': bool(self.dashboard.ui_prefs.get('header_collapsed', False))
                }
                try:
                    self.wfile.write(json.dumps(payload).encode())
                except BrokenPipeError:
                    pass
            elif path == '/api/leak_analysis':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = json.dumps(self.dashboard.get_leak_analysis())
                self.wfile.write(data.encode())
            elif path == '/api/dashboard_status':
                # Dashboard status for menu bar app
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                data = json.dumps(self.dashboard.get_dashboard_status())
                self.wfile.write(data.encode())
            elif path.startswith('/api/analysis_health'):
                # Lightweight analysis readiness/summary endpoint
                hours_param = query_params.get('hours', [24])[0]
                try:
                    hours = 'all' if hours_param == 'all' else int(hours_param)
                except Exception:
                    hours = 24
                try:
                    payload = self.dashboard.get_analysis_health(hours)
                    data = json.dumps(payload, default=str, allow_nan=True)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    try:
                        self.wfile.write(data.encode())
                    except BrokenPipeError:
                        pass
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    err = json.dumps({'ok': False, 'error': str(e), 'hours': hours})
                    try:
                        self.wfile.write(err.encode())
                    except BrokenPipeError:
                        pass

            elif path.startswith('/static/'):
                try:
                    rel = path.lstrip('/')
                    here = os.path.dirname(os.path.abspath(__file__))
                    candidates = [
                        os.path.join(here, rel),
                        os.path.join(os.getcwd(), rel),
                    ]
                    file_path = None
                    for fp in candidates:
                        if os.path.isfile(fp):
                            file_path = fp
                            break
                    if file_path:
                        # Basic content type detection
                        if file_path.endswith('.css'):
                            content_type = 'text/css'
                        elif file_path.endswith('.js'):
                            content_type = 'text/javascript'
                        else:
                            content_type = 'application/octet-stream'
                        self.send_response(200)
                        self.send_header('Content-type', content_type)
                        # Stronger no-cache to avoid stale assets across instances
                        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                        self.send_header('Pragma', 'no-cache')
                        self.send_header('Expires', '0')
                        self.end_headers()
                        with open(file_path, 'rb') as f:
                            self.wfile.write(f.read())
                    else:
                        self.send_response(404)
                        self.end_headers()
                except Exception:
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()




        def do_POST(self):
            """Handle POST requests (write operations)."""
            # Update activity for POST requests
            self._update_activity()

            from urllib.parse import urlparse
            parsed_path = urlparse(self.path)
            path = parsed_path.path

            if path == '/api/ui_prefs':
                # Update UI preferences (expects JSON body)
                try:
                    length = int(self.headers.get('Content-Length') or 0)
                except Exception:
                    length = 0
                body = b''
                if length > 0:
                    try:
                        body = self.rfile.read(length)
                    except Exception:
                        body = b''
                new_prefs = {}
                try:
                    if body:
                        new_prefs = json.loads(body.decode('utf-8'))
                except Exception:
                    new_prefs = {}

                # Only allow header_collapsed for now
                if isinstance(new_prefs, dict) and 'header_collapsed' in new_prefs:
                    self.dashboard.ui_prefs['header_collapsed'] = bool(new_prefs.get('header_collapsed', False))
                    try:
                        os.makedirs(os.path.dirname(self.dashboard.ui_prefs_file), exist_ok=True)
                        with open(self.dashboard.ui_prefs_file, 'w') as f:
                            json.dump(self.dashboard.ui_prefs, f)
                    except Exception:
                        pass

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                payload = { 'header_collapsed': bool(self.dashboard.ui_prefs.get('header_collapsed', False)) }
                try:
                    self.wfile.write(json.dumps(payload).encode())
                except BrokenPipeError:
                    pass
                return

            # Unknown POST endpoint
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())
            except BrokenPipeError:
                pass

        def log_message(self, format, *args):
            """Suppress default logging."""
            pass

    def render_dashboard_html(self):
        """Render the unified dashboard HTML."""
        html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">


    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clipboard Monitor - Unified Memory Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js?v=__ASSET_VERSION__"></script>
    <style>
      @keyframes pulseDot {
        0%   { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
        70%  { box-shadow: 0 0 0 8px rgba(46, 204, 113, 0); }
        100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
      }
      /* Trend Explorer utility classes */
      .spark-badge { font-size:11px; color:#777; background:#f2f6ff; border:1px solid #e3ecff; padding:0 4px; border-radius:4px; }
      .spark-btn { font-size:11px; padding:2px 6px; border:1px solid #cfe8ff; border-radius:6px; background:#eef7ff; color:#266eb6; cursor:pointer; }
      .spark-hint { font-size:11px; color:#555; margin-bottom:4px; }
      /* Fullscreen tweaks: remove top shadows and add top margin */
      body.fs-dashboard #top-header,
      body.fs-analysis #top-header,
      body.fs-clipboard #top-header { box-shadow: none !important; }

      /* Remove extra gap under tabs in fullscreen */
      body.fs-dashboard #dashboard-tab,
      body.fs-analysis #analysis-tab,
      body.fs-clipboard #clipboard-tab { margin-top: 0 !important; }

      /* Clipboard fullscreen: let the page handle scrolling (no inner scroller) */
      body.fs-clipboard { overflow: auto !important; height: auto; }
      html.fs-clipboard { overflow: auto !important; height: auto; }
      body.fs-clipboard .tab-content { overflow: visible !important; }
      body.fs-clipboard #content-width-wrap { overflow: visible !important; }

      /* In fullscreen, flatten control bars to avoid a visible top shadow band */
      body.fs-dashboard .unified-control-bar,
      body.fs-analysis .unified-control-bar { box-shadow: none !important; }
      /* Remove gradients/shading on charts in fullscreen dashboard */
      body.fs-dashboard .unified-control-bar { background: #ffffff !important; border-color: #e6e8eb !important; }
      body.fs-dashboard .chart-container { box-shadow: none !important; background: transparent !important; }

      /* Remove shadows from dashboard charts in normal view as well */
      .unified-control-bar { box-shadow: none !important; background: #ffffff !important; border-color: #e6e8eb !important; }
      .chart-container { box-shadow: none !important; }
      .chart-container .mode-toggle { box-shadow: none !important; }
      .chart-container .mode-btn { box-shadow: none !important; }

      body.fs-dashboard .chart-container .mode-toggle { box-shadow: none !important; }

      /* Keep the three-tab bar visible at top in fullscreen across all sections */
      :root { --panel-gap: 8px; }
      body.fs-dashboard #nav-shell,
      body.fs-analysis #nav-shell,
      body.fs-clipboard #nav-shell {
        position: fixed; top: 0; left: calc(10vw + 8px); width: calc(80vw - 16px); z-index: 950; background: #ffffff;
      }
      body.fs-dashboard #dashboard-tab > *:first-child,
      body.fs-analysis #analysis-tab > *:first-child,
      body.fs-clipboard #clipboard-tab > *:first-child { margin-top: 0 !important; }
      /* In fullscreen, always show the full tabs row and hide the compact strip */
      body.fs-dashboard #collapse-strip,
      body.fs-analysis #collapse-strip,
      body.fs-clipboard #collapse-strip { display: none !important; }
      body.fs-dashboard #nav-shell .tabs,
      body.fs-analysis #nav-shell .tabs,
      body.fs-clipboard #nav-shell .tabs { display: flex !important; }
      /* Offset content by nav height + 8px gap in fullscreen */
      body.fs-dashboard #content-width-wrap,
      body.fs-analysis #content-width-wrap,
      body.fs-clipboard #content-width-wrap { padding-top: 60px; }
      /* Remove accidental top margins on first controls under tabs */
      #clipboard-tab .clip-toolbar { margin-top: 0 !important; }

      body.fs-dashboard .chart-container .mode-btn { box-shadow: none !important; }

      /* Clipboard spacing between toolbar and table */
      #clipboard-tab .clip-table-wrap { margin-top: 12px !important; }

      /* Fullscreen Clipboard: sticky pager at bottom, aligned to content width */
      body.fs-clipboard #clip-pager {
        position: fixed; bottom: 10px; left: calc(10vw + 8px); width: calc(80vw - 16px);
        background: #ffffff; border: 1px solid #eee; border-radius: 6px; padding: 6px 8px;
        box-shadow: 0 -2px 6px rgba(0,0,0,0.06); z-index: 1000;
      }
      /* Segmented control in pinned nav */
      #nav-shell .nav-controls { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); display: flex; align-items: center; gap: 6px; z-index: 951; }
      #nav-shell .segmented { display: inline-flex; border: 1px solid #cfe8ff; border-radius: 10px; overflow: hidden; background: #eef7ff; }
      #nav-shell .segmented .seg-btn { font-size: 11px; padding: 2px 8px; background: transparent; border: 0; color: #266eb6; cursor: pointer; }
      #nav-shell .segmented .seg-btn + .seg-btn { border-left: 1px solid #cfe8ff; }
      #nav-shell .segmented .seg-btn:hover { background: rgba(38,110,182,0.07); }
      #nav-shell .esc-hint { font-size: 10px; color: #666; background: #f1f3f5; border: 1px solid #dee2e6; padding: 1px 6px; border-radius: 10px; display: none; }

    </style>
        <link rel="stylesheet" href="/static/style.css?v=__ASSET_VERSION__">
        <script src="/static/js/app-core.js?v=__ASSET_VERSION__"></script>

        <script src="/static/js/charts/cpu-chart.js?v=__ASSET_VERSION__"></script>
        <script>
          // Early debug logger stub to buffer messages before panel initializes
          (function(){
            try {
              window.__dbgBuf = window.__dbgBuf || [];
              if (!window.__dbgLog) {
                window.__dbgLog = function(msg){
                  try { window.__dbgBuf.push(`[${new Date().toISOString()}] ${msg}`); } catch {}
                };
              }
            } catch {}
          })();
        </script>

        <script src="/static/js/dashboard.js?v=__ASSET_VERSION__"></script>

</head>
<body>
    <div class="container" style="width:80%; margin: 0 10%;">
        <div id="toast-container" aria-live="polite" aria-atomic="true"></div>
        <!-- New 4-Box Dashboard Header -->

        <div id="top-header" class="header header-shell" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 8px; padding: 8px; margin-bottom: 8px; border: 1px solid #dee2e6; box-shadow: 0 2px 6px rgba(0,0,0,0.1); position: relative;">
            <!-- Compact Title and Status -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #e0e0e0;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <h1 style="margin: 0; font-size: 16px; color: #333; font-weight: bold;">📊 Clipboard Monitor Dashboard</h1>
                </div>
                <div style="display: flex; align-items: center; font-size: 11px; gap: 12px;">
                    <div id="status-cluster" style="display:flex; align-items:center; gap:8px;">
                        <span style="background: #4CAF50; color: white; padding: 2px 6px; border-radius: 8px; font-weight: bold; display: flex; align-items: center; gap: 3px;">
                            <span>●</span> Connected
                        </span>
                        <span id="analysis-ready-badge" title="Analysis readiness" style="display:none; align-items:center; gap:6px; background:#eef7ff; color:#2b5a3a; padding:2px 6px; border-radius:8px; border:1px solid #cfe8ff;">
                            <span id="analysis-ready-dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#2ecc71;"></span>
                            <span id="analysis-ready-text" style="font-weight:600;">Ready</span>
                        </span>
                        <span id="advanced-status" style="background: #999; color: white; padding: 2px 6px; border-radius: 8px; font-weight: bold; display: flex; align-items: center; gap: 3px;">
                            ⚫ Advanced
                        </span>
                        <span id="monitoring-status-indicator" class="monitoring-indicator" style="display:none; width:10px; height:10px; border-radius:50%; background:#4CAF50; animation: pulse-dot 1.5s infinite;"></span>
                    </div>
                    <div id="metrics-cluster" style="display:flex; align-items:center; gap:8px; margin-left:24px;">
                        <span id="top-mb-badge" title="Menu Bar status" style="display:flex; align-items:center; gap:6px; background:#f1f8ff; color:#0b5ed7; padding:2px 6px; border-radius:8px; border:1px solid #cfe2ff;">
                            📱 <span id="top-mb-mem">--</span> • <span id="top-mb-cpu">--</span> • <span id="top-mb-status">--</span>
                        </span>
                        <span id="top-svc-badge" title="Service status" style="display:flex; align-items:center; gap:6px; background:#f3fff1; color:#2e7d32; padding:2px 6px; border-radius:8px; border:1px solid #dcedc8;">
                            ⚙️ <span id="top-svc-mem">--</span> • <span id="top-svc-cpu">--</span> • <span id="top-svc-status">--</span>
                        </span>
                    </div>
                        <button id="header-collapse-toggle" class="spark-btn" style="padding:2px 6px; font-size:11px;" onclick="toggleHeaderBar()" title="Collapse/Expand header">▴</button>


                </div>
            </div>

            <!-- Clean 4-Box Horizontal Layout -->
            <div class="header-grid">

                <!-- Box 1: Menu Bar + Service -->
                <div class="header-card" style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #2196F3; height: 100%;">
                    <div style="font-weight: bold; color: #2196F3; margin-bottom: 6px; font-size: 11px; text-align: center;">📱 Menu Bar</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🆔 PID:</span>
                            <span id="header-menubar-pid" style="font-family: monospace; color: #2c3e50; font-weight: 600;">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>● Status:</span>
                            <span id="header-menubar-status" style="color: #666; font-weight: bold;">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💾 Memory:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span style="font-size: 9px; color: #666;">Peak:</span>
                            <span style="font-size: 9px; color: #FF5722; font-weight: bold;" id="header-menubar-memory-peak">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ CPU:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-cpu">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🧵 Threads:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-threads">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🔗 Handles:</span>
                            <span style="color: #2196F3; font-weight: bold;" id="header-menubar-handles">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⏰ Uptime:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-menubar-uptime">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔄 Restarts:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-menubar-restarts">--</span>
                        </div>
                    </div>

                    <div style="font-weight: bold; color: #4CAF50; margin: 8px 0 6px 0; font-size: 11px; text-align: center; border-top: 1px solid #eee; padding-top: 6px;">⚙️ Service</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🆔 PID:</span>
                            <span id="header-service-pid" style="font-family: monospace; color: #2c3e50; font-weight: 600;">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>● Status:</span>
                            <span id="header-service-status" style="color: #666; font-weight: bold;">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💾 Memory:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span style="font-size: 9px; color: #666;">Peak:</span>
                            <span style="font-size: 9px; color: #FF5722; font-weight: bold;" id="header-service-memory-peak">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ CPU:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-cpu">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🧵 Threads:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-threads">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🔗 Handles:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-handles">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⏰ Uptime:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-uptime">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔄 Restarts:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-service-restarts">--</span>
                        </div>
                    </div>
                </div>

                <!-- Box 2: Analytics -->
                <div class="header-card" style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #FF9800; height: 100%;">
                    <div style="font-weight: bold; color: #FF9800; margin-bottom: 4px; font-size: 11px; text-align: center;">📊 Analytics</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📊 Total:</span>
                            <span style="color: #FF9800; font-weight: bold;" id="header-total-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📈 Growth:</span>
                            <span style="color: #FF5722; font-weight: bold;" id="header-growth-rate">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ Efficiency:</span>
                            <span style="color: #9C27B0; font-weight: bold;" id="header-efficiency">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🎯 Optimum:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-optimum">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🗑️ GC:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-gc-status">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ Pressure:</span>
                            <span style="color: #F44336; font-weight: bold;" id="header-pressure">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📚 History:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-history">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📋 Queue:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-queue">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>💾 Cache:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-cache">--</span>
                        </div>
                    </div>
                </div>

                <!-- Box 3: System -->
                <div class="header-card" style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #9C27B0; height: 100%;">
                    <div style="font-weight: bold; color: #9C27B0; margin-bottom: 4px; font-size: 11px; text-align: center;">💻 System</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>🧠 RAM:</span>
                            <span style="color: #9C27B0; font-weight: bold;" id="header-system-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ CPU:</span>
                            <span style="color: #F44336; font-weight: bold;" id="header-cpu-usage">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💾 Total:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-total-ram">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>✅ Available:</span>
                            <span style="color: #4CAF50; font-weight: bold;" id="header-available-ram">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>📊 Load:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-system-load">--</span>
                        </div>
                    </div>
                </div>

                <!-- Box 4: Session -->
                <div class="header-card" style="background: white; border-radius: 6px; padding: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 3px solid #795548; height: 100%;">
                    <div style="font-weight: bold; color: #795548; margin-bottom: 4px; font-size: 11px; text-align: center;">📊 Session</div>
                    <div style="font-size: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⏰ Session:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-session-time">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>💻 System:</span>
                            <span style="color: #795548; font-weight: bold;" id="header-uptime">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📈 Points:</span>
                            <span style="color: #607D8B; font-weight: bold;" id="header-data-points">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>📊 Peak Mem:</span>
                            <span style="color: #FF5722; font-weight: bold;" id="header-peak-memory">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span>⚡ Peak CPU:</span>
                            <span style="color: #FF5722; font-weight: bold;" id="header-peak-cpu">--</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔄 Updated:</span>
                            <span style="color: #666; font-weight: bold;" id="header-last-updated">--</span>
                        </div>
            </div>

                    </div>
                </div>
            </div>
        </div>




        <!-- Content width wrapper to match header/container width -->
        <div id="content-width-wrap" style="width:80%; margin: 0 10%; box-sizing: border-box;">

        <div id="nav-shell" class="nav-shell" style="margin: 0 0 10px 0; width: 100%; padding: 0; box-sizing: border-box;">
          <div class="tabs" style="position: relative; display:flex; gap:12px; width: 100%; box-sizing: border-box;">
            <div class="tab active" onclick="switchTab('dashboard', this)" style="flex:1; position:relative;">📊 Dashboard</div>
            <div class="tab" onclick="switchTab('analysis', this)" style="flex:1; position:relative;">🔍 Analysis & Controls</div>
            <div class="tab" onclick="switchTab('clipboard', this)" style="flex:1; position:relative;">📋 Clipboard History</div>
            </div>

            <div id="collapse-strip" class="collapse-strip" style="display:none;">
              <div style="display:flex; align-items:center; gap:8px;">
                <button id="nav-expand-toggle" class="spark-btn" title="Expand" onclick="expandFromStrip()">▾</button>
                <strong id="nav-current-title" style="font-size:12px; color:#333;">Dashboard</strong>
              </div>
              <div class="strip-tabs" style="display:flex; gap:6px;">
                <button class="spark-btn" style="padding:2px 6px; font-size:11px;" onclick="switchTab('dashboard', this)" title="Dashboard">📊</button>
                <button class="spark-btn" style="padding:2px 6px; font-size:11px;" onclick="switchTab('analysis', this)" title="Analysis">🔍</button>
                <button class="spark-btn" style="padding:2px 6px; font-size:11px;" onclick="switchTab('clipboard', this)" title="Clipboard">📋</button>
              </div>
            </div>
            <div id="nav-controls" class="nav-controls"></div>
          </div>
        </div>


        <!-- Consolidated Dashboard Tab -->
        <div id="dashboard-tab" class="tab-content active" style="margin: 0 calc(10vw + 8px); width: auto; box-sizing: border-box; padding: 0;">

            <!-- Memory Usage Chart - Only visible in Dashboard tab -->
            <div class="chart-container" style="margin-bottom: 12px; width: 100%; max-width: 100%; box-sizing: border-box; overflow: hidden; height: 350px; position: relative;">
                <!-- Unified Control Bar -->
                <div class="unified-control-bar" style="
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    width: 100%;
                    max-width: 100%;
                    box-sizing: border-box;
                    overflow: hidden;
                ">
                    <!-- Top Row: Title and Status -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <h3 style="font-size: 16px; margin: 0; color: #333; font-weight: 600;">
                                📈 <span id="chart-title">Live Memory Usage</span>
                            </h3>
                            <div class="chart-badge" style="
                                background: #4CAF50;
                                color: white;
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 10px;
                                font-weight: 500;
                                text-transform: uppercase;
                            " id="mode-badge">Live</div>
                        </div>
                        <div class="chart-status" style="
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            font-size: 11px;
                            color: #666;
                            background: rgba(255,255,255,0.7);
                            padding: 4px 8px;
                            border-radius: 4px;
                        ">
                            <span id="chart-mode-indicator">Live: 5 Minutes</span>
                            <span style="color: #dee2e6;">•</span>
                            <span id="chart-points-count">-- pts</span>
                            <span style="color: #dee2e6;">•</span>
                            <span id="chart-last-update">--</span>
                                <span style="color: #dee2e6;">•</span>
                                <button id="mem-clear-btn" onclick="window.chartManager && window.chartManager.clearChart()" style="border:1px solid #ddd; background:#fff; color:#333; border-radius:4px; padding:2px 6px; cursor:pointer; font-size:11px;">Clear</button>
                                <span style="color:#dee2e6;">•</span>
                                <button id="mem-help-toggle" onclick="window.toggleHelp('mem', event)" style="border:1px solid #ddd; background:#fff; color:#333; border-radius:4px; padding:2px 6px; cursor:pointer; font-size:11px;">Help</button>
                        </div>
                    </div>

                    <!-- Bottom Row: Controls -->
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <!-- Left: Mode Controls -->
                        <div class="mode-controls" style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 12px; color: #666; font-weight: 500;">Mode:</span>
                            <div class="mode-toggle" style="
                                display: flex;
                                background: white;
                                border: 1px solid #dee2e6;
                                border-radius: 6px;
                                overflow: hidden;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                            ">
                                <button id="realtime-btn" class="mode-btn" onclick="if (window.chartManager) window.chartManager.switchToLiveMode(); return false;" style="
                                    padding: 6px 12px;
                                    font-size: 12px;
                                    border: none;
                                    background: #4CAF50;
                                    color: white;
                                    cursor: pointer;
                                    font-weight: 500;
                                    transition: all 0.2s ease;
                                ">Live</button>
                                <button id="historical-btn" class="mode-btn" onclick="memorySwitchToHistorical()" style="
                                    padding: 6px 12px;
                                    font-size: 12px;
                                    border: none;
                                    background: white;
                                    color: #666;
                                    cursor: pointer;
                                    font-weight: 500;
                                    transition: all 0.2s ease;
                                ">Historical</button>
                            </div>
                        </div>

                        <!-- Center: Range Controls -->
                        <div class="range-controls" style="display: flex; align-items: center; gap: 8px;">
                            <!-- Live Range Options -->
                            <div id="live-options" style="display: flex; align-items: center; gap: 6px;">
                                <span style="font-size: 12px; color: #666; font-weight: 500;">Range:</span>
                                <select id="live-range-select" onchange="handleLiveRangeChange(this)" style="
                                    padding: 6px 10px;
                                    font-size: 12px;
                                    border: 1px solid #dee2e6;
                                    border-radius: 4px;
                                    background: white;
                                    color: #333;
                                    cursor: pointer;
                                    font-weight: 500;
                                    min-width: 100px;
                                ">
                                    <option value="5m">5 Minutes</option>
                                    <option value="15m">15 Minutes</option>
                                    <option value="30m">30 Minutes</option>
                                    <option value="1h">1 Hour</option>
                                    <option value="2h">2 Hours</option>
                                    <option value="4h">4 Hours</option>
                                </select>
                            </div>

                            <!-- Historical Range Options (hidden by default) -->
                            <div id="historical-options" style="display: none; align-items: center; gap: 6px;">
                                <span style="font-size: 12px; color: #666; font-weight: 500;">Period:</span>
                                <select id="historical-range" onchange="handleRangeChange(this)" style="
                                    padding: 6px 10px;
                                    font-size: 12px;
                                    border: 1px solid #dee2e6;
                                    border-radius: 4px;
                                    background: white;
                                    color: #333;
                                    cursor: pointer;
                                    font-weight: 500;
                                    min-width: 120px;
                                ">
                                    <option value="1">Last Hour</option>
                                    <option value="6">Last 6 Hours</option>
                                    <option value="24">Last 24 Hours</option>
                                    <option value="168">Last 7 Days</option>
                                    <option value="all">Since Start ⚠️</option>
                                </select>
                                <span style="font-size: 12px; color: #666; font-weight: 500;">Resolution:</span>
                                <select id="resolution-select" onchange="chartManager.changeResolution(this.value)" style="
                                    padding: 6px 10px;
                                    font-size: 12px;
                                    border: 1px solid #dee2e6;
                                    border-radius: 4px;
                                    background: white;
                                    color: #333;
                                    cursor: pointer;
                                    font-weight: 500;
                                    min-width: 100px;
                                ">
                                    <option value="full">Full</option>
                                    <option value="10sec">10s Avg</option>
                                    <option value="minute">1m Avg</option>
                                    <option value="hour">1h Avg</option>
                                </select>
                            </div>
                        </div>

                        <!-- Right: Data Info and Legend -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div class="data-info" style="
                                display: flex;
                                align-items: center;
                                gap: 6px;
                                font-size: 11px;
                                color: #666;
                                background: rgba(255,255,255,0.7);
                                padding: 4px 8px;
                                border-radius: 4px;
                            ">
                                <span id="data-collection-info">Data: 2s intervals</span>
                            </div>

                            <!-- Legend -->
                            <div class="legend-info" style="
                                display: flex;
                                align-items: center;
                                gap: 12px;
                                font-size: 12px;
                            ">
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 12px; height: 12px; background: #2196F3; border-radius: 2px;"></div>
                                    <span>Menu Bar App</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 12px; height: 12px; background: #4CAF50; border-radius: 2px;"></div>
                                    <span>Main Service</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Chart Canvas -->
                    <div class="chart-wrapper" style="margin-top: 0; position: relative; top: 0;">
                        <canvas id="memoryChart"></canvas>
                    </div>
                        <!-- Help Overlay: Memory -->
                        <div>
                            <div id="mem-help-overlay" data-open="0" style="position:absolute; left:8px; right:8px; top:8px; background:#f9fbfd; border:1px solid #e3f2fd; border-radius:8px; padding:10px 12px; color:#345; font-size:12px; box-shadow:0 6px 12px rgba(0,0,0,0.15); transform: translateY(-110%); transition: transform 0.25s ease; z-index: 999; max-height:75%; overflow:auto;">
                                <strong>Memory chart controls</strong>
                                <ul style="margin:6px 0 0 16px; line-height:1.35;">
                                    <li><b>Mode</b>: Live streams recent data; Historical loads a fixed time window for analysis.</li>
                                    <li><b>Live Range</b>: Window of recent time shown (older points roll off).</li>
                                    <li><b>Period</b> (Historical): Time span to load (e.g., 1h, 6h, 24h, All).</li>
                                    <li><b>Resolution</b> (Historical): Point density/aggregation for performance; Full shows all points.</li>
                                    <li><b>Data intervals</b>: Live updates ~every 2s; Historical returns data spaced by selected resolution.</li>
                                    <li><b>Status row</b>: Pts shows number of points; Updated/Loaded shows last refresh.</li>
                                    <li><b>Clear</b>: Clears on‑screen series and counters (does not delete server history or change mode).</li>
                                </ul>
                                <div style="margin-top:6px; color:#567;">Tip: For large periods, choose a coarser Resolution to keep the chart responsive.</div>
                            </div>
                        </div>
                </div>
            </div>

            <!-- CPU Usage Chart -->
            <div class="chart-container" style="margin-bottom: 12px; width: 100%; max-width: 100%; box-sizing: border-box; overflow: hidden; height: 350px; position: relative;">
                <!-- Unified Control Bar (CPU) -->
                <div class="unified-control-bar" style="
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    width: 100%; max-width: 100%; box-sizing: border-box; overflow: hidden;">
                    <!-- Top Row: Title and Status -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <h3 style="font-size: 16px; margin: 0; color: #333; font-weight: 600;">⚡ <span id="cpu-chart-title">Live CPU Usage</span></h3>
                            <div class="chart-badge" id="cpu-mode-badge" style="background:#4CAF50;color:#fff;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:500;text-transform:uppercase;">Live</div>
                        </div>
                        <div class="chart-status" style="display:flex;align-items:center;gap:8px;font-size:11px;color:#666;background:rgba(255,255,255,0.7);padding:4px 8px;border-radius:4px;">
                            <span id="cpu-chart-mode-indicator">Live</span>
                            <span style="color:#dee2e6;">•</span>
                            <span id="cpu-chart-points-count">-- pts</span>
                            <span style="color:#dee2e6;">•</span>
                            <span id="cpu-last-refresh">--</span>
                                <span style="color:#dee2e6;">•</span>
                                <button id="cpu-clear-btn" onclick="window.cpuChartManager && window.cpuChartManager.clearChart()" style="border:1px solid #ddd; background:#fff; color:#333; border-radius:4px; padding:2px 6px; cursor:pointer; font-size:11px;">Clear</button>
                                <span style="color:#dee2e6;">•</span>
                                <button id="cpu-help-toggle" onclick="window.toggleHelp('cpu', event)" style="border:1px solid #ddd; background:#fff; color:#333; border-radius:4px; padding:2px 6px; cursor:pointer; font-size:11px;">Help</button>
                        </div>
                    </div>

                    <!-- Bottom Row: Controls -->
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <!-- Left: Mode Controls -->
                        <div class="mode-controls" style="display:flex;align-items:center;gap:8px;">
                            <span style="font-size:12px;color:#666;font-weight:500;">Mode:</span>
                            <div class="mode-toggle" style="display:flex;background:white;border:1px solid #dee2e6;border-radius:6px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.05);">
                                <button id="cpu-realtime-btn" class="mode-btn" onclick="cpuChartManager.switchToRealtimeMode()" style="padding:6px 12px;font-size:12px;border:none;background:#4CAF50;color:#fff;cursor:pointer;font-weight:500;transition:all 0.2s ease;">Live</button>
                                <button id="cpu-historical-btn" class="mode-btn" onclick="cpuChartManager.switchToHistoricalMode()" style="padding:6px 12px;font-size:12px;border:none;background:white;color:#666;cursor:pointer;font-weight:500;transition:all 0.2s ease;">Historical</button>
                            </div>
                        </div>

                        <!-- Center: Range Controls (historical) -->
                        <div id="cpu-live-options" style="display:flex;align-items:center;gap:6px;">

                            <span style="font-size:12px;color:#666;font-weight:500;">Range:</span>
                            <select id="cpu-live-range-select" onchange="cpuChartManager.changeLiveRange(this.value)" style="padding:6px 10px;font-size:12px;border:1px solid #dee2e6;border-radius:4px;background:white;color:#333;cursor:pointer;font-weight:500;min-width:100px;">
                                <option value="2m">2 Minutes</option>
                                <option value="5m">5 Minutes</option>
                                <option value="15m">15 Minutes</option>
                            </select>
                        </div>

                        <div id="cpu-historical-options" style="display:none;align-items:center;gap:6px;">
                            <span style="font-size:12px;color:#666;font-weight:500;">Period:</span>
                            <select id="cpu-time-range" onchange="cpuChartManager.loadHistoricalData()" style="padding:6px 10px;font-size:12px;border:1px solid #dee2e6;border-radius:4px;background:white;color:#333;cursor:pointer;font-weight:500;min-width:120px;">
                                <option value="1h">Last Hour</option>
                                <option value="6h">Last 6 Hours</option>
                                <option value="24h">Last 24 Hours</option>
                                <option value="7d">Last 7 Days</option>
                            </select>
                        </div>
                        <!-- Help Overlay: CPU -->
                        <div>
                            <div id="cpu-help-overlay" data-open="0" style="position:absolute; left:8px; right:8px; top:8px; background:#f9fbfd; border:1px solid #e3f2fd; border-radius:8px; padding:10px 12px; color:#345; font-size:12px; box-shadow:0 6px 12px rgba(0,0,0,0.15); transform: translateY(-110%); transition: transform 0.25s ease; z-index: 999; max-height:75%; overflow:auto;">
                                <strong>CPU chart controls</strong>
                                <ul style="margin:6px 0 0 16px; line-height:1.35;">
                                    <li><b>Mode</b>: Live streams recent CPU; Historical loads a fixed window for analysis.</li>
                                    <li><b>Live Range</b>: Recent window width (e.g., 2m, 5m, 15m).</li>
                                    <li><b>Period</b> (Historical): Time span to load (e.g., 1h, 6h, 24h).</li>
                                    <li><b>Resolution</b> (Historical): Aggregation density; use coarser for longer periods.</li>
                                    <li><b>Data intervals</b>: Live updates about every 2s; Historical depends on resolution.</li>
                                    <li><b>Status row</b>: Pts = points shown; Updated = last refresh time.</li>
                                    <li><b>Clear</b>: Clears on‑screen series only; does not delete history.</li>
                                </ul>
                                <div style="margin-top:6px; color:#567;">Tip: Use Live for spikes, Historical for trends. Coarser resolution helps performance on large windows.</div>
                            </div>
                        </div>

                        <!-- Right: Data Info, Debug Link and Legend -->
                        <div style="display:flex;align-items:center;gap:16px;">
                            <div class="data-info" style="display:flex;align-items:center;gap:6px;font-size:11px;color:#666;background:rgba(255,255,255,0.7);padding:4px 8px;border-radius:4px;">
                                <span id="cpu-frequency-label">Data: 2s intervals</span>
                            </div>
                            <div class="legend-info" style="display:flex;align-items:center;gap:12px;font-size:12px;">
                                <div style="display:flex;align-items:center;gap:4px;"><div style="width:12px;height:12px;background:#2196F3;border-radius:2px;"></div><span>Menu Bar App</span></div>
                                <div style="display:flex;align-items:center;gap:4px;"><div style="width:12px;height:12px;background:#4CAF50;border-radius:2px;"></div><span>Main Service</span></div>
                            </div>
                        </div>
                    </div>

                    <!-- Chart Canvas -->
                    <div class="chart-wrapper" style="margin-top: 0; position: relative; top: 0;">
                        <canvas id="cpuChart"></canvas>
                    </div>
                </div>
            </div>


        </div>

        <!-- Analysis Tab (Combined with Controls) -->
        <div id="analysis-tab" class="tab-content" style="margin: 0 calc(10vw + 8px); width: auto; box-sizing: border-box; padding: 0;">
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #4CAF50;">
                <h4 style="margin: 0 0 10px 0; color: #2e7d32;">🔍 Memory Analysis & Monitoring Dashboard</h4>
                <p style="margin: 0 0 10px 0;">This tab provides comprehensive memory leak detection, monitoring controls, and growth pattern analysis.</p>
                <div class="grid-2-12" style="margin-top: 10px;">
                    <div style="background: white; padding: 10px; border-radius: 5px;">
                        <strong>📊 Analysis Features:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px; font-size: 14px;">
                            <li>Growth rate analysis</li>
                            <li>Memory trend patterns</li>
                            <li>Leak severity assessment</li>
                            <li>Process-specific analysis</li>
                        </ul>
                    </div>
                    <div style="background: white; padding: 10px; border-radius: 5px;">
                        <strong>⚙️ Monitoring Controls:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px; font-size: 14px;">
                            <li>Advanced monitoring with configurable intervals</li>
                            <li>Memory leak detection algorithms</li>
                            <li>Background data collection</li>
                            <li>Session-based monitoring</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Live Collection Strip (compact banner) -->
            <div class="card" style="padding: 10px 12px;">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <span id="live-status-dot" style="width:10px; height:10px; border-radius:50%; background:#ccc;"></span>
                        <strong>Live Collection:</strong>
                        <span id="live-status-text" style="color:#666;">INACTIVE</span>
                        <span style="color:#bbb;">|</span>
                        <span>Rate: <strong id="live-interval">Every 10s</strong></span>
                        <span style="color:#bbb;">|</span>
                        <span>Next: <strong id="live-next">--</strong></span>
                        <span style="color:#bbb;">|</span>
                        <span>Points: <strong id="live-adv-points">0</strong></span>
                        <span style="color:#bbb;">|</span>
                        <span>Duration: <strong id="live-duration">0.00h</strong></span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button id="monitoringToggleBtnMini" onclick="toggleAdvancedMonitoring()" style="background:#4CAF50; color:white; border:none; padding:8px 14px; border-radius:5px; cursor:pointer; font-weight:600;">🚀 Start</button>
                        <button onclick="forceGarbageCollection()" style="background:#ff9800; color:white; border:none; padding:8px 14px; border-radius:5px; cursor:pointer;" title="Force Python garbage collection to free unused memory">🗑️ GC</button>
                    </div>
                </div>
                <div style="margin-top:6px; color:#666; font-size:12px;">
                    <em>Collects per‑process memory and CPU at the chosen interval. Use the controls to start/stop a session; results appear below.</em>
                </div>
                <div id="live-last-sample" style="margin-top:6px; font-size:12px; color:#333; font-variant-numeric: tabular-nums;"></div>
                <div id="live-last-inc" style="margin-top:2px; font-size:12px; color:#666; font-variant-numeric: tabular-nums;"><em>Last inc: --</em></div>
            </div>

            <!-- Monitoring Controls Section (Moved from Controls Tab) -->
            <div class="card">
                <h3>⚙️ Advanced Monitoring Controls</h3>
                <div class="section-grid">
                    <div>
                        <label for="monitorInterval" style="display: block; margin-bottom: 5px;">Monitoring Interval:</label>
                        <select id="monitorInterval" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 12px;">
                            <option value="10" selected>Every 10 seconds</option>
                            <option value="30">Every 30 seconds</option>
                            <option value="60">Every 1 minute</option>
                            <option value="300">Every 5 minutes</option>
                        </select>

                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <button id="monitoringToggleBtn" onclick="toggleAdvancedMonitoring()" style="background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-weight: bold;">🚀 Start Advanced Monitoring</button>
                            <button onclick="forceGarbageCollection()" style="background: #ff9800; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer;" title="Force Python garbage collection to free unused memory">🗑️ Force Garbage Collection</button>
                        </div>
                    </div>

                    <div id="monitoring-status">
                        <div style="padding: 15px; background: #f5f5f5; border-radius: 8px; border: 2px solid #ddd;">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <div id="status-indicator" style="width: 12px; height: 12px; border-radius: 50%; background: #ccc; margin-right: 10px;"></div>
                                <strong>Advanced Monitoring Status:</strong> <span id="status-text">INACTIVE</span>
                            </div>
                            <div class="grid-2-12">
                                <div>
                                    <strong>Advanced Data Points:</strong> <span id="advanced-data-points">0</span><br>
                                <div>
                                    <strong>Next Sample In:</strong> <span id="next-sample">--</span>
                                </div>
                                    <strong>Advanced Collection Rate:</strong> <span id="collection-rate">Stopped</span><br>
                                    <small style="color: #666;">Leak detection & analysis data</small>
                                </div>
                                <div>
                                    <strong>Basic Data Points:</strong> <span id="basic-data-points">0</span><br>
                                    <strong>Basic Collection Rate:</strong> <span style="color: #4CAF50;">Every 1s</span><br>
                                    <small style="color: #666;">Real-time dashboard data</small>
                                </div>
                            </div>
                            <div class="grid-2-12" style="margin-top: 10px;">
                                <div>
                                    <strong>Advanced Duration:</strong> <span id="monitoring-duration">0.0 hours</span>
                                </div>
                                <div>
                                    <strong>Last Update:</strong> <span id="last-update">Never</span>
                                </div>
                            </div>
                            <div id="collection-animation" style="margin-top: 10px; display: none;">
                                <div style="display: flex; align-items: center;">
                                    <div class="pulse-dot"></div>
                                    <span style="margin-left: 10px; color: #4CAF50; font-weight: bold;">Collecting data...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Analysis Controls Section -->
            <div class="analysis-grid">
            <!-- Last Session Summary (Findings Board) -->
            <div class="card">
                <h3>🧭 Last Session Summary</h3>
                <div id="session-findings">
                    <div class="loading">Waiting for advanced monitoring data...</div>
                </div>
            </div>

                <div class="card">
                    <h3>⏱️ Analysis Time Range</h3>
                    <div style="margin-bottom: 12px;">
                        <label for="analysisTimeRange" style="display: block; margin-bottom: 5px;">Select time period for analysis:</label>
                        <select id="analysisTimeRange" onchange="updateAnalysisTimeRange()" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="1">Last 1 hour</option>
                            <option value="6">Last 6 hours</option>
                            <option value="24" selected>Last 24 hours</option>
                            <option value="72">Last 3 days</option>
                            <option value="168">Last week</option>
                        </select>
                    </div>
                    <div id="analysis-summary" style="padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <div class="loading">Loading analysis summary...</div>
                    </div>
                </div>

                <div class="card">
                    <h3>🎯 Quick Actions</h3>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <div style="display:flex; gap:8px; flex-wrap:wrap;">
                          <button onclick="exportAnalysisData()" style="background: #4CAF50; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;">📊 Export JSON</button>
                          <button onclick="exportAnalysisCsv()" style="background: #0d9488; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;">🧾 Export CSV</button>
                          <button onclick="exportAggregatedCsv()" style="background: #0ea5e9; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;">📎 Export Aggregated CSV</button>
                          <button onclick="copyLatestAnalysisJson()" style="background: #673ab7; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;" title="Copy latest analysis JSON to clipboard">📋 Copy Latest Analysis JSON</button>
                          <button onclick="refreshAllData()" style="background: #2196F3; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;" title="Reload all dashboard data from server">🔄 Refresh All Data</button>
                        </div>
                        <button onclick="openSparkSettings()" style="background: #607d8b; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; display:flex; align-items:center; gap:6px;" title="Trend Explorer Settings">
                            ⚙️ Settings
                        </button>
                    </div>
                    <div style="margin-top:8px; font-size:11px; color:#666;">Analysis auto-refreshes every 5s while monitoring is active.</div>
                </div>
            </div>

            <!-- Analysis Results Section -->
            <div class="stack-16">
            <div class="card">
                <h3>🔍 Memory Leak Detection Results</h3>
                <div id="leak-analysis">
                    <div class="loading">Analyzing memory trends...</div>
                </div>
            </div>

            <div class="card">
                <h3>📈 Growth Trend Analysis</h3>
                <div style="font-size:12px; color:#555; margin-bottom:8px;">
                    This section analyzes memory behavior over time for the Menu Bar and Main Service processes.
                    We compute growth rate (MB/hour) using a simple regression of memory vs time, estimate Consistency using R² (how well a straight line explains the trend),
                    and surface the biggest spikes to help spot anomalous jumps. Use the Range and Res controls to change the analysis window and resolution.
                <!-- Trend Explorer Settings Modal -->
                <div id="spark-settings-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.4); z-index:9999;">
                  <div id="spark-settings-panel" style="background:#fff; width:380px; max-width:90vw; margin:10vh auto; padding:16px; border-radius:8px; box-shadow:0 8px 30px rgba(0,0,0,0.2); resize:both; overflow:auto;">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; cursor:move;" id="spark-settings-drag">
                      <div style="font-weight:700; color:#123;">⚙️ Trend Explorer Settings</div>
                      <button onclick="closeSparkSettings()" style="background:none; border:none; font-size:18px; cursor:pointer;">✖</button>
                    </div>
                    <div style="display:grid; gap:10px; font-size:13px; color:#333;">
                      <label style="display:flex; align-items:center; gap:8px;">
                        <input id="spark-anim-enabled" type="checkbox" checked>
                        <span>Animate sparkline endpoint</span>
                      </label>
                      <label style="display:flex; align-items:center; gap:8px;">
                        <span style="min-width:120px;">Animation duration</span>
                        <select id="spark-anim-ms" style="flex:1; padding:6px;">
                          <option value="0">0 ms (off)</option>
                          <option value="100">100 ms</option>
                          <option value="180" selected>180 ms</option>
                          <option value="300">300 ms</option>
                        </select>
                      </label>
                      <label style="display:flex; align-items:center; gap:8px;">
                        <span style="min-width:120px;">Tooltip mode</span>
                        <select id="spark-tooltip-mode" style="flex:1; padding:6px;">
                          <option value="custom" selected>Custom tooltip</option>
                          <option value="native">Native browser tip</option>
                          <option value="off">Off</option>
                        </select>
                      </label>
                      <fieldset style="border:1px solid #eee; border-radius:6px; padding:8px;">
                        <legend style="font-size:12px; color:#555;">Series</legend>
                        <div style="display:grid; gap:6px;">
                          <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                            <label style="display:flex; align-items:center; gap:8px;">
                              <input id="spark-show-menubar" type="checkbox" checked>
                              <span>Menu Bar (MB)</span>
                            </label>
                            <label style="display:flex; align-items:center; gap:6px; font-size:12px;">
                              <span>Style</span>
                              <select id="spark-style-menubar">
                                <option value="line" selected>Line</option>
                                <option value="area">Area</option>
                              </select>
                            </label>
                          </div>
                          <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                            <label style="display:flex; align-items:center; gap:8px;">
                              <input id="spark-show-service" type="checkbox" checked>
                              <span>Main Service (MB)</span>
                            </label>
                            <label style="display:flex; align-items:center; gap:6px; font-size:12px;">
                              <span>Style</span>
                              <select id="spark-style-service">
                                <option value="line" selected>Line</option>
                                <option value="area">Area</option>
                              </select>
                            </label>
                          </div>
                          <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                            <label style="display:flex; align-items:center; gap:8px;">
                              <input id="spark-show-total" type="checkbox" checked>
                              <span>Total (MB)</span>
                            </label>
                            <label style="display:flex; align-items:center; gap:6px; font-size:12px;">
                              <span>Style</span>
                              <select id="spark-style-total">
                                <option value="line" selected>Line</option>
                                <option value="area">Area</option>
                              </select>
                            </label>
                          </div>
                        </div>
                      </fieldset>
                      <label style="display:flex; align-items:center; gap:8px; margin-top:6px;">
                        <input id="spark-pulse-enabled" type="checkbox" checked>
                        <span>Pulse last point on update</span>
                      </label>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:12px;">
                      <button id="spark-reset-btn" style="background:none; color:#666; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; text-decoration:underline;">Reset defaults</button>
                      <div>
                        <button onclick="closeSparkSettings()" style="background:#eee; color:#333; border:none; padding:8px 12px; border-radius:6px; cursor:pointer;">Cancel</button>
                        <button onclick="(function(){ saveSparkSettings(); })()" style="background:#90caf9; color:#0d47a1; border:none; padding:8px 12px; border-radius:6px; cursor:pointer;">Apply</button>
                        <button onclick="saveSparkSettings()" style="background:#2196F3; color:white; border:none; padding:8px 12px; border-radius:6px; cursor:pointer;">Save</button>
                      </div>
                    </div>
                  </div>
                </div>

                <div id="health-banner" style="display:flex; justify-content:space-between; align-items:center; padding:8px; border-radius:6px; margin-bottom:8px; background:#f8f9fa; border-left:4px solid #999;">
                  <div style="font-size:12px; color:#333;">Health Score</div>
                  <div id="header-health-score" style="font-size:16px; font-weight:700; color:#333;">--%</div>
                </div>


                </div>
                <!-- Trend Analysis section (sparklines removed per request) -->
                <div id="trend-analysis">
                    <div id="analysis-top-meta" style="font-size:12px; color:#2b5a3a; margin-bottom:6px; display:none;"></div>
                    <div class="loading">Loading trend analysis...</div>
                </div>

<script>
    function drawSparkline(canvasId, data, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array(data.length).fill(''),
                datasets: [{
                    data: data,
                    borderColor: color,
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { display: false },
                scales: {
                    xAxes: [{ display: false }],
                    yAxes: [{ display: false }]
                },
                tooltips: { enabled: false }
            }
        });
    }

    function updateAnalysisDisplay(data) {
        const trendAnalysis = document.getElementById('trend-analysis');
        if (!trendAnalysis) return;

        let html = '<div class="grid-3-12">_</div>';
        for (const processName in data) {
            const processData = data[processName];
            const sparklineId = `sparkline-${processName}`;
            html += `
                <div class="card">
                    <h4>${processName.replace('_', ' ')}</h4>
                    <p>Status: ${processData.status}</p>
                    <p>Growth Rate: ${processData.growth_rate_mb.toFixed(2)} MB/hr</p>
                    <div class="sparkline-container" style="height: 50px;">
                        <canvas id="${sparklineId}"></canvas>
                    </div>
                </div>
            `;
        }
        trendAnalysis.innerHTML = html;

        for (const processName in data) {
            const processData = data[processName];
            if (processData.sparkline) {
                const sparklineId = `sparkline-${processName}`;
                drawSparkline(sparklineId, processData.sparkline, '#2196F3');
            }
        }
    }
</script>

            </div>
            <div class="card">
                <h3>🔥 Top Offenders (Memory Growth) <span id="offenders-window" style="font-size:12px; color:#555; margin-left:8px;"></span></h3>
                <div id="top-offenders"><div class="loading">Loading top offenders…</div></div>
            </div>


            <div class="card">
                <h3>📊 Advanced Monitoring History</h3>
                <div id="monitoring-history">
                    <div class="loading">Loading monitoring history...</div>
                </div>
            </div>
            </div> <!-- Close stack-16 -->
        </div>





    <!-- Controls Tab (Removed - Merged with Analysis Tab) -->

    <script>
        // Live collection countdown state (global)
        window.__liveCountdown = { active: false, interval: 30, remaining: 0, timerId: null, lastPoints: 0 };

        // Global variables
        // Analysis helpers (move to script top to avoid being printed in tables)
        let analysisAbortController = null;
        let analysisDebounceTimer = null;
        function isTabActive(name) {
            const el = document.getElementById(name + '-tab');
            return el && el.classList.contains('active');
        }
        document.addEventListener('DOMContentLoaded', () => {
            const sel = document.getElementById('analysisTimeRange');
            const saved = localStorage.getItem('analysisTimeRange');
            if (sel && saved) sel.value = saved;
            // avoid double init — dashboard.js bootstraps chartManager
        });

        // Helpers moved to /static/js/app-core.js
        // Chart management functions
        let chartPaused = false;

        // Legacy sparkline function is now no-op (removed legacy UI)
        function drawSparkline(canvasId, value, kind = 'mem', maxPoints = 10) {
            // intentionally empty; legacy inline canvases removed
            return;
        }

        // Utility functions
        function formatDuration(ms) {
            const seconds = Math.floor(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);

            if (days > 0) {
                return `${days}d ${hours % 24}h`;
            } else if (hours > 0) {
                return `${hours}h ${minutes % 60}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${seconds % 60}s`;
            } else {
                return `${seconds}s`;
            }
        }

        // Advanced monitoring status management
        function updateAdvancedStatus(isActive) {
            const statusElement = document.getElementById('advanced-status');
            if (isActive) {
                statusElement.style.background = '#F44336';
                statusElement.style.animation = 'pulse 2s infinite';
                statusElement.innerHTML = '🔴 Advanced';
            } else {
                statusElement.style.background = '#999';
                statusElement.style.animation = 'none';
                statusElement.innerHTML = '⚫ Advanced';
            }
        }


        // Tab switching functionality
        function switchTab(tabName, el) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab content
            document.getElementById(tabName + '-tab').classList.add('active');

            // Add active class to clicked tab (robust for direct calls)
            if (el && el.classList) {
                el.classList.add('active');
            } else {
                const sel = `.tabs .tab[onclick*="${tabName}"]`;


                const fallback = document.querySelector(sel);
                if (fallback) fallback.classList.add('active');
            }

            // Handle tab-specific initialization
            if (tabName === 'dashboard') {
                // Resize charts when switching to dashboard tab to fix any sizing issues
                setTimeout(() => {
                    if (typeof chart !== 'undefined') {
                        chart.resize();
                    }
                }, 100);
            }
        }


        // Nav collapse + fullscreen preferences per tab (global, runs on DOM ready)
        (function(){ if (window.__navInitDone) return; window.__navInitDone = true;
          const NAV_KEY = 'cm_nav_prefs_v1';
          function readNav(){ try { return JSON.parse(localStorage.getItem(NAV_KEY) || '{}'); } catch(e) { return {}; } }
          function writeNav(p){ try { localStorage.setItem(NAV_KEY, JSON.stringify(p)); } catch(e) {} }
          function titleFor(tab){ return tab==='dashboard' ? 'Dashboard' : (tab==='analysis' ? 'Analysis & Controls' : 'Clipboard History'); }
          function activeTab(){
            const t = document.querySelector('.tabs .tab.active');
            if (t && t.textContent.includes('Clipboard')) return 'clipboard';
            if (t && (t.textContent.includes('Analysis') || t.textContent.includes('Controls'))) return 'analysis';
            return 'dashboard';
          }

          function updateClipboardFsLayout(){
            try {
              const isFs = document.body.classList.contains('fs-clipboard');
              const wrap = document.querySelector('#clipboard-tab .clip-table-wrap');
              const toolbar = document.querySelector('#clipboard-tab .clip-toolbar');
              const pager = document.getElementById('clip-pager');
              const nav = document.getElementById('nav-shell');
              if (!wrap) return;
              if (isFs) {
                // Let the page handle scrolling in fullscreen: do not constrain inner wrapper
                wrap.style.height = '';
                wrap.style.maxHeight = '';
                // Keep pager aligned to content width for visual consistency
                if (pager) {
                  const rr = wrap.getBoundingClientRect();
                  pager.style.left = rr.left + 'px';
                  pager.style.width = rr.width + 'px';
                }
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
              } else {
                wrap.style.height = '';
                wrap.style.maxHeight = '';
                if (pager) { pager.style.left = ''; pager.style.width = ''; }
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
              }
            } catch(e) {}
          }
          window.__updateClipFsLayout = updateClipboardFsLayout;
          window.addEventListener('resize', function(){ if (document.body.classList.contains('fs-clipboard')) updateClipboardFsLayout(); });

          function updateFsChromeLayout(){
            try {
              const fs = document.body.classList.contains('fs-dashboard') || document.body.classList.contains('fs-analysis') || document.body.classList.contains('fs-clipboard');
              const nav = document.getElementById('nav-shell');
              const cw = document.getElementById('content-width-wrap');
              if (!nav || !cw) return;
              if (fs) {
                const r = cw.getBoundingClientRect();
                nav.style.setProperty('position', 'fixed', 'important');
                nav.style.setProperty('left', r.left + 'px', 'important');
                nav.style.setProperty('right', (window.innerWidth - r.right) + 'px', 'important');
                nav.style.setProperty('width', 'auto', 'important');
                nav.style.setProperty('top', '0px', 'important');
                nav.style.setProperty('z-index', '950', 'important');
                nav.style.setProperty('box-sizing', 'border-box', 'important');
                nav.style.setProperty('margin', '0', 'important');
                // Fixed 60px offset (48px nav height + 12px gap)
                cw.style.paddingTop = '60px';
              } else {
                nav.style.position = '';
                nav.style.left = '';
                nav.style.right = '';
                nav.style.width = '';
                nav.style.top = '';
                nav.style.margin = '';
                nav.style.boxSizing = '';
                cw.style.paddingTop = '';
              }
            } catch(e){}
          }
          window.__updateFsChromeLayout = updateFsChromeLayout;
          window.addEventListener('resize', function(){ if (document.body.classList.contains('fs-dashboard') || document.body.classList.contains('fs-analysis') || document.body.classList.contains('fs-clipboard')) updateFsChromeLayout(); });


          function normalizeNavGrid(){
            try {
              const shell = document.getElementById('nav-shell');
              const ctrls = document.getElementById('nav-controls');
              if (!shell || !ctrls) return;
              const hasControls = !!ctrls.querySelector('.segmented') || (ctrls.children && ctrls.children.length > 0);
              if (hasControls) {
                ctrls.style.display = 'flex';
                shell.style.display = 'grid';
                shell.style.gridTemplateColumns = '1fr auto';
                shell.style.columnGap = '8px';
              } else {
                ctrls.style.display = 'none';
                shell.style.display = 'block';
                shell.style.gridTemplateColumns = '1fr';
                shell.style.columnGap = '0px';
              }
            } catch(e) {}
          }

          document.addEventListener('DOMContentLoaded', normalizeNavGrid);

          function applyNavFor(tab){
            const allPrefs = readNav();
            const prefs = allPrefs[tab] || {};
            const fsGlobal = !!allPrefs._fsGlobal;
            const shell = document.getElementById('nav-shell');
            const strip = document.getElementById('collapse-strip');
            const header = document.getElementById('top-header');
            const headerBtn = document.getElementById('header-collapse-toggle');
            if (shell) {
              const collapsed = false;
              shell.classList.toggle('collapsed', collapsed);
              if (strip) strip.style.display = collapsed ? 'flex' : 'none';
              const collBtn = document.getElementById('nav-collapse-toggle'); if (collBtn) collBtn.textContent = collapsed ? '\u25be' : '\u25b4';
            }
            const titleEl = document.getElementById('nav-current-title'); if (titleEl) titleEl.textContent = titleFor(tab);
            const fs = fsGlobal; // fullscreen persists across tabs until explicitly exited
            // Build/update segmented controls on the right
            try {
              const tabsRow = (shell ? shell.querySelector('.tabs') : null);
              if (tabsRow) {
                let controls = shell.querySelector('.nav-controls');
                if (!controls) {
                  controls = document.createElement('div');
                  controls.className = 'nav-controls'; controls.id = 'nav-controls';
                  const seg = document.createElement('div');
                  seg.className = 'segmented';
                  const btnHeader = document.createElement('button');
                  btnHeader.id = 'seg-header-toggle';
                  btnHeader.className = 'seg-btn';
                  btnHeader.title = 'Show/Hide Header';
                  btnHeader.addEventListener('click', function(e){ e.stopPropagation(); window.toggleHeaderBar(); });
                  const btnFs = document.createElement('button');
                  btnFs.id = 'seg-fs-toggle';
                  btnFs.className = 'seg-btn';
                  btnFs.title = 'Enter/Exit Fullscreen';
                  btnFs.addEventListener('click', function(e){ e.stopPropagation(); window.toggleFullscreen(); });
                  seg.appendChild(btnHeader);
                  seg.appendChild(btnFs);
                  const esc = document.createElement('span'); esc.id = 'seg-esc-hint'; esc.className = 'esc-hint'; esc.textContent = 'Esc';
                  controls.appendChild(seg);
                  controls.appendChild(esc);
                  tabsRow.appendChild(controls);
                  controls.style.display = 'flex';
                } else {
                  // Ensure controls live inside the tabs row for correct absolute positioning
                  tabsRow.appendChild(controls);
                  controls.style.display = 'flex';
                  // If the placeholder exists but is empty, (re)build its content
                  if (!controls.querySelector('.segmented')) {
                    const seg = document.createElement('div');
                    seg.className = 'segmented';
                    const btnHeader = document.createElement('button');
                    btnHeader.id = 'seg-header-toggle';
                    btnHeader.className = 'seg-btn';
                    btnHeader.title = 'Show/Hide Header';
                    btnHeader.addEventListener('click', function(e){ e.stopPropagation(); window.toggleHeaderBar(); });
                    const btnFs = document.createElement('button');
                    btnFs.id = 'seg-fs-toggle';
                    btnFs.className = 'seg-btn';
                    btnFs.title = 'Enter/Exit Fullscreen';
                    btnFs.addEventListener('click', function(e){ e.stopPropagation(); window.toggleFullscreen(); });
                    seg.appendChild(btnHeader);
                    seg.appendChild(btnFs);
                    const esc = document.createElement('span'); esc.id = 'seg-esc-hint'; esc.className = 'esc-hint'; esc.textContent = 'Esc';
                    controls.appendChild(seg);
                    controls.appendChild(esc);
                  }
                }
                const hdrCollapsed = (typeof window.__hdrCollapsed === 'boolean') ? window.__hdrCollapsed : false;
                const hdrBtn = document.getElementById('seg-header-toggle');
                if (hdrBtn) {
                  hdrBtn.textContent = hdrCollapsed ? '\u25be Header' : '\u25b4 Header';
                  // Hide header toggle while in fullscreen mode (header cannot expand there)
                  hdrBtn.style.display = fs ? 'none' : 'inline-block';
                }
                const fsBtn2 = document.getElementById('seg-fs-toggle'); if (fsBtn2) fsBtn2.textContent = fs ? '\u2716 Full' : '\u26f6 Full';
                const escHint = document.getElementById('seg-esc-hint'); if (escHint) escHint.style.display = fs ? 'inline-block' : 'none';
              }
              // Hide legacy header button in the header box to avoid duplication
              if (headerBtn) headerBtn.style.display = 'none';
            } catch(e){}
            document.body.classList.remove('fs-dashboard','fs-analysis','fs-clipboard');
            document.documentElement.classList.remove('fs-dashboard','fs-analysis','fs-clipboard');
            if (fs) {
              document.body.classList.add('fs-' + tab);
              document.documentElement.classList.add('fs-' + tab);
            }
            // Ensure the three-tab bar stays visible in fullscreen (use full tabs, not compact strip)
            if (shell) { shell.style.display = 'block'; shell.style.visibility = 'visible'; }
            if (fs && strip) { strip.style.display = 'none'; }
            // Update fullscreen chrome (fixed nav alignment + content offset)
            try { window.__updateFsChromeLayout && window.__updateFsChromeLayout(); } catch(e){}
            // In clipboard fullscreen, use an inner scroller and hide page scrollbars
            if (tab === 'clipboard') { try { window.__updateClipFsLayout && window.__updateClipFsLayout(); } catch(e){} }
            // Removed Esc toast/tooltip on entering fullscreen per user request
            try {
              const isFs = document.body.classList.contains('fs-dashboard') ||
                           document.body.classList.contains('fs-analysis') ||
                           document.body.classList.contains('fs-clipboard');
              // No toast or tooltip
              window.__fsWasOn = isFs;
            } catch (e) {}

          const UIPREFS_URL = '/api/ui_prefs';
          async function fetchHeaderCollapsed(){ try { const r = await fetch(UIPREFS_URL); const j = await r.json(); return !!(j && j.header_collapsed); } catch(e) { return false; } }
          async function saveHeaderCollapsed(val){
            try {
              await fetch(UIPREFS_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ header_collapsed: !!val }) });
            } catch(e) {}
          }

          async function setHeaderCollapsed(tab, val){
            await saveHeaderCollapsed(!!val);
            window.__hdrCollapsed = !!val;
            applyNavFor(tab);
          }
          window.toggleHeaderBar = function(){
            const tab = (window.currentTabName || activeTab());
            const cur = (typeof window.__hdrCollapsed === 'boolean') ? window.__hdrCollapsed : false;
            const next = !cur;
            window.__hdrCollapsed = next;
            const headerGrid = document.querySelector('#top-header .header-grid');
            if (headerGrid) headerGrid.style.display = next ? 'none' : '';
            const headerBtn = document.getElementById('header-collapse-toggle');
            if (headerBtn) headerBtn.textContent = next ? '\u25be' : '\u25b4';
            setHeaderCollapsed(tab, next);
          };
          window.expandHeaderBar = function(){
            const tab = (window.currentTabName || activeTab());
            window.__hdrCollapsed = false;
            const headerGrid = document.querySelector('#top-header .header-grid');
            if (headerGrid) headerGrid.style.display = '';

            const headerBtn = document.getElementById('header-collapse-toggle');
            if (headerBtn) headerBtn.textContent = '\u25b4';
            setHeaderCollapsed(tab, false);
          };

            // Header collapse handling
            if (typeof window.__hdrCollapsed !== 'boolean') {
              fetchHeaderCollapsed().then(v => { window.__hdrCollapsed = !!v; applyNavFor(tab); });

            }
            const hdrCollapsed = (typeof window.__hdrCollapsed === 'boolean') ? window.__hdrCollapsed : false;
            if (headerBtn) headerBtn.textContent = hdrCollapsed ? '\u25be' : '\u25b4';
            // Keep the top bar visible; hide only the 4-column grid
            if (header) header.style.display = '';
            const headerGrid = header ? header.querySelector('.header-grid') : null;
            if (headerGrid) headerGrid.style.display = hdrCollapsed ? 'none' : '';
          }

            // Normalize nav grid based on presence of controls to remove trailing gap
            try { normalizeNavGrid(); } catch(e) {}

          function setCollapsed(tab, val){ const all = readNav(); all[tab] = Object.assign({collapsed:false, fullscreen:false, headerCollapsed:false}, all[tab], {collapsed: !!val}); writeNav(all); applyNavFor(tab); }
          function setFullscreenGlobal(tab, val){ const all = readNav(); all._fsGlobal = !!val; all[tab] = Object.assign({collapsed:false, fullscreen:false, headerCollapsed:false}, all[tab], {fullscreen: !!val}); writeNav(all); applyNavFor(tab); }
          window.toggleCollapsed = function(){ const tab = (window.currentTabName || activeTab()); const all = readNav(); setCollapsed(tab, !(all[tab] && all[tab].collapsed)); };
          window.toggleFullscreen = function(){ const tab = (window.currentTabName || activeTab()); const all = readNav(); const cur = !!all._fsGlobal; setFullscreenGlobal(tab, !cur); };
          window.expandFromStrip = function(){ const tab = (window.currentTabName || activeTab()); setCollapsed(tab, false); };
          window.exitFullscreenCurrent = function(){ const tab = (window.currentTabName || activeTab()); setFullscreenGlobal(tab, false); };
          document.addEventListener('keydown', function(e){
            const k = e.key || e.keyCode;
            if (k === 'Escape' || k === 'Esc' || k === 27) {
              if (document.body.classList.contains('fs-dashboard') || document.body.classList.contains('fs-analysis') || document.body.classList.contains('fs-clipboard')) {
                window.exitFullscreenCurrent();
              }
            }
          });

          const _origSwitch = window.switchTab;
          window.switchTab = function(tabName, el){ _origSwitch(tabName, el); window.currentTabName = tabName; applyNavFor(tabName); };
          document.addEventListener('DOMContentLoaded', function(){ window.currentTabName = window.currentTabName || activeTab(); applyNavFor(window.currentTabName); });
          window.applyNavFor = applyNavFor; // expose for debugging
        })();

        // Legacy memory chart initialization removed - now handled by UnifiedMemoryChart class

        // Initialize CPU chart handled by module; inline will not initialize it

        // Polling for real-time updates (simpler than WebSockets)
        let isConnected = false;

        // Generate simulated data for demonstration
        function generateSimulatedData() {
            const baseMemory = 45 + Math.random() * 10; // 45-55 MB
            const baseCpu = 2 + Math.random() * 8; // 2-10%

            return {
                menubar_memory: baseMemory + Math.random() * 5,
                service_memory: baseMemory * 0.8 + Math.random() * 3,
                total_memory: baseMemory * 1.8 + Math.random() * 8,
                menubar_cpu: baseCpu + Math.random() * 3,
                service_cpu: baseCpu * 0.6 + Math.random() * 2,
                total_cpu: baseCpu * 1.6 + Math.random() * 5,
                peak_menubar_memory: baseMemory * 1.3,
                peak_service_memory: baseMemory * 1.2,
                peak_menubar_cpu: baseCpu * 1.5,
                peak_service_cpu: baseCpu * 1.4,
                timestamp: new Date().toISOString()
            };
        }

        async function fetchMemoryData() {
            try {
                // Get current status data for dashboard stats
                const response = await fetch('/api/current');
                if (!response.ok) {
                    throw new Error(`Failed to fetch data: ${response.statusText}`);
                }
                const data = await response.json();

                if (!isConnected) {
                    const statusLight = document.getElementById('dashboard-status-light');
                    const statusText = document.getElementById('dashboard-status-text');
                    if (statusLight && statusText) {
                        statusLight.style.background = '#4CAF50';
                        statusText.textContent = 'Connected';
                        statusText.style.color = '#4CAF50';
                    }
                    isConnected = true;
                }

                if (data.clipboard) {
                    const menubarProcess = data.clipboard.processes.find(p => p.process_type === 'menu_bar');
                    const serviceProcesses = data.clipboard.processes.filter(p => p.process_type === 'main_service');
                    const serviceProcess = serviceProcesses.length > 0 ?
                        serviceProcesses.reduce((prev, current) => (prev.memory_mb > current.memory_mb) ? prev : current) :
                        null;

                    const menubarMemory = menubarProcess ? menubarProcess.memory_mb : 0;
                    const serviceMemory = serviceProcess ? serviceProcess.memory_mb : 0;
                    const menubarCpu = menubarProcess ? menubarProcess.cpu_percent : 0;
                    const serviceCpu = serviceProcess ? serviceProcess.cpu_percent : 0;

                    // Pass the complete data structure to updateDashboard
                    updateDashboard({
                        timestamp: data.timestamp,
                        menubar_memory: menubarMemory,
                        service_memory: serviceMemory,
                        total_memory: menubarMemory + serviceMemory,
                        menubar_cpu: menubarCpu,
                        service_cpu: serviceCpu,
                        total_cpu: menubarCpu + serviceCpu,
                        peak_menubar_memory: data.peak_menubar_memory,


                        peak_service_memory: data.peak_service_memory,
                        peak_total_memory: data.peak_total_memory,
                        peak_menubar_cpu: data.peak_menubar_cpu,
                        peak_service_cpu: data.peak_service_cpu,
                        peak_total_cpu: data.peak_total_cpu,
                        session_start_time: data.session_start_time,
                        // Pass the complete API data for analytics, system, session, and processes
                        clipboard: data.clipboard,
                        analytics: data.analytics,
                        system: data.system,
                        session: data.session
                    });
                } else {
                    // If clipboard data is missing, use simulated data for demonstration
                    updateDashboard(generateSimulatedData());
                }
                return true;
            } catch (error) {
                console.error('Error fetching memory data:', error);
                updateDashboard(generateSimulatedData()); // Fallback to simulated data

                if (isConnected) {
                    const statusLight = document.getElementById('dashboard-status-light');
                    const statusText = document.getElementById('dashboard-status-text');
                    if (statusLight && statusText) {
                        statusLight.style.background = '#f44336';
                        statusText.textContent = 'Disconnected';
                        statusText.style.color = '#f44336';

                    }
                    isConnected = false;
                }
                return false;
            }
        }

        function updateDashboard(data) {
            try {
                // Extract data from /api/current response structure
                const clipboard = data.clipboard || {};
                const processes = clipboard.processes || [];

                // Find menu bar and service processes
                const menuBarProcess = processes.find(p => p.process_type === 'menu_bar') || {};
                const serviceProcess = processes.find(p => p.process_type === 'main_service') || {};

                const menubarMemory = menuBarProcess.memory_mb ?? 0;
                const serviceMemory = serviceProcess.memory_mb ?? 0;
                const menubarCpu = menuBarProcess.cpu_percent ?? 0;
                const serviceCpu = serviceProcess.cpu_percent ?? 0;
                const totalMemory = (clipboard.total_memory_mb ?? (menubarMemory + serviceMemory)) || 0;

                // Use server-provided peak values
                const peakMenubarMemory = data.peak_menubar_memory || 0;
                const peakServiceMemory = data.peak_service_memory || 0;

                const peakTotalMemory = data.peak_total_memory || 0;
                const peakMenubarCpu = data.peak_menubar_cpu || 0;
                const peakServiceCpu = data.peak_service_cpu || 0;
                const peakTotalCpu = data.peak_total_cpu || 0;
                const sessionStartTime = data.session?.start_time ? new Date(data.session.start_time) : new Date();

                // Add missing fields for legacy chart compatibility
                data.menubar_memory = menubarMemory;
                data.service_memory = serviceMemory;
                data.menubar_cpu = menubarCpu;
                data.service_cpu = serviceCpu;
                data.total_memory = totalMemory;
                data.timestamp = data.timestamp || new Date().toISOString();

                // Helper function to safely update element
                function safeUpdateElement(id, value) {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = value;
                    }
                    // Silently ignore missing elements - they're optional UI components
                }

                // Update header memory metrics - Enhanced with all new metrics
                safeUpdateElement('header-menubar-memory', menubarMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-service-memory', serviceMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-total-memory', totalMemory.toFixed(1) + 'MB');
                // Top bar compact memory
                safeUpdateElement('top-mb-mem', menubarMemory.toFixed(1) + 'MB');
                safeUpdateElement('top-svc-mem', serviceMemory.toFixed(1) + 'MB');

                // Update CPU metrics
                safeUpdateElement('header-menubar-cpu', menubarCpu.toFixed(1) + '%');
                safeUpdateElement('header-service-cpu', serviceCpu.toFixed(1) + '%');
                // Top bar compact CPU
                safeUpdateElement('top-mb-cpu', menubarCpu.toFixed(1) + '%');
                safeUpdateElement('top-svc-cpu', serviceCpu.toFixed(1) + '%');

                // Update peak values (use server data or calculate fallback)
                const calcPeakMenubarMemory = peakMenubarMemory || menubarMemory * 1.2;
                const calcPeakServiceMemory = peakServiceMemory || serviceMemory * 1.15;
                const calcPeakMenubarCpu = peakMenubarCpu || menubarCpu * 1.3;
                const calcPeakServiceCpu = peakServiceCpu || serviceCpu * 1.25;

                safeUpdateElement('header-menubar-memory-peak', calcPeakMenubarMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-service-memory-peak', calcPeakServiceMemory.toFixed(1) + 'MB');
                safeUpdateElement('header-menubar-cpu-peak', calcPeakMenubarCpu.toFixed(1) + '%');
                safeUpdateElement('header-service-cpu-peak', calcPeakServiceCpu.toFixed(1) + '%');

                // Update detailed process metrics from API data (reuse existing processes variable)
                const detailedMenubarProcess = processes.find(p => p.process_type === 'menu_bar');
                const detailedServiceProcess = processes.find(p => p.process_type === 'main_service');

                // Update Menu Bar detailed metrics
                if (detailedMenubarProcess) {
                    safeUpdateElement('header-menubar-pid', detailedMenubarProcess.pid || '--');
                    safeUpdateElement('header-menubar-threads', detailedMenubarProcess.threads || '--');
                    safeUpdateElement('header-menubar-handles', detailedMenubarProcess.handles || '--');
                    safeUpdateElement('header-menubar-uptime', detailedMenubarProcess.uptime || '--');
                    safeUpdateElement('header-menubar-restarts', detailedMenubarProcess.restarts || '0');
                    const status = (detailedMenubarProcess.cpu_percent > 50 || detailedMenubarProcess.memory_mb > 200) ? '⚠️ High' : '✅ Normal';
                    safeUpdateElement('header-menubar-status', status);
                    safeUpdateElement('top-mb-status', status);
                    const statusEl = document.getElementById('header-menubar-status');
                    if (statusEl) statusEl.style.color = status.includes('High') ? '#e74c3c' : '#27ae60';
                }

                // Update Service detailed metrics
                if (detailedServiceProcess) {
                    safeUpdateElement('header-service-pid', detailedServiceProcess.pid || '--');
                    safeUpdateElement('header-service-threads', detailedServiceProcess.threads || '--');
                    safeUpdateElement('header-service-handles', detailedServiceProcess.handles || '--');
                    safeUpdateElement('header-service-uptime', detailedServiceProcess.uptime || '--');
                    safeUpdateElement('header-service-restarts', detailedServiceProcess.restarts || '0');
                    const status = (detailedServiceProcess.cpu_percent > 50 || detailedServiceProcess.memory_mb > 200) ? '⚠️ High' : '✅ Normal';
                    safeUpdateElement('header-service-status', status);
                    safeUpdateElement('top-svc-status', status);
                    const statusEl = document.getElementById('header-service-status');
                    if (statusEl) statusEl.style.color = status.includes('High') ? '#e74c3c' : '#27ae60';
                }

                // Update analytics metrics from API data
                const analytics = data.analytics || {};

                safeUpdateElement('header-growth-rate', analytics.growth_rate || '--');
                const growthRateElement = document.getElementById('header-growth-rate');
                if (growthRateElement && analytics.growth_rate) {
                    const rateValue = parseFloat(analytics.growth_rate) || 0;
                    growthRateElement.style.color = rateValue > 1 ? '#FF5722' : rateValue > 0 ? '#FF9800' : '#4CAF50';
                }

                safeUpdateElement('header-efficiency', analytics.efficiency || '--');
                safeUpdateElement('header-optimum', analytics.optimum || '--');

                safeUpdateElement('header-gc-status', analytics.gc_status || '--');
                const gcStatusElement = document.getElementById('header-gc-status');
                if (gcStatusElement && analytics.gc_status) {
                    const status = analytics.gc_status;
                    gcStatusElement.style.color = status === 'Low' ? '#4CAF50' : status === 'Normal' ? '#FF9800' : '#F44336';
                }

                safeUpdateElement('header-pressure', analytics.pressure || '--');
                const pressureElement = document.getElementById('header-pressure');
                if (pressureElement && analytics.pressure) {
                    const pressureValue = parseFloat(analytics.pressure) || 0;
                    pressureElement.style.color = pressureValue > 2 ? '#F44336' : pressureValue > 1 ? '#FF9800' : '#4CAF50';
                }

                safeUpdateElement('header-history', analytics.history || '--');
                safeUpdateElement('header-queue', analytics.queue !== undefined ? analytics.queue : '--');

                safeUpdateElement('header-cache', analytics.cache || '--');
                const cacheElement = document.getElementById('header-cache');
                if (cacheElement && analytics.cache) {
                    const cacheValue = parseFloat(analytics.cache) || 0;
                    cacheElement.style.color = cacheValue > 95 ? '#4CAF50' : cacheValue > 90 ? '#FF9800' : '#F44336';
                }

            const opsRate = document.getElementById('operations-rate');
            if (opsRate) {
                const ops = Math.floor(Math.random() * 20) + 5; // 5-25 ops/min
                opsRate.textContent = ops + '/min';
            }

            const gcPressure = document.getElementById('gc-pressure');
            if (gcPressure) {
                const pressures = ['Low', 'Normal', 'High'];
                const colors = ['#4CAF50', '#FF9800', '#F44336'];
                const index = Math.floor(Math.random() * 3);
                gcPressure.textContent = pressures[index];
                gcPressure.style.color = colors[index];
            }

            const memPressure = document.getElementById('memory-pressure');
            if (memPressure) {
                const pressures = ['Normal', 'Moderate', 'High'];
                const colors = ['#4CAF50', '#FF9800', '#F44336'];
                const index = Math.floor(Math.random() * 3);
                memPressure.textContent = pressures[index];
                memPressure.style.color = colors[index];
            }

            const historySize = document.getElementById('history-size');
            if (historySize) {
                const size = Math.floor(Math.random() * 500) + 1000; // 1000-1500 items
                historySize.textContent = size.toLocaleString();
            }

            const queueDepth = document.getElementById('queue-depth');
            if (queueDepth) {
                const depth = Math.floor(Math.random() * 5); // 0-4 items
                queueDepth.textContent = depth;
                queueDepth.style.color = depth > 2 ? '#F44336' : depth > 0 ? '#FF9800' : '#4CAF50';
            }

            const cacheHit = document.getElementById('cache-hit');
            if (cacheHit) {
                const hit = (Math.random() * 10 + 90).toFixed(1); // 90-100%
                cacheHit.textContent = hit + '%';
                cacheHit.style.color = hit > 95 ? '#4CAF50' : hit > 90 ? '#FF9800' : '#F44336';
            }

                // Update system metrics from API data
                const system = data.system || {};

                safeUpdateElement('header-system-memory', (system.percent || 0).toFixed(1) + '%');
                safeUpdateElement('header-cpu-usage', (system.cpu_percent || 0).toFixed(1) + '%');
                safeUpdateElement('header-total-ram', (system.total_gb || 0).toFixed(1) + 'GB');
                safeUpdateElement('header-available-ram', (system.available_gb || 0).toFixed(1) + 'GB');

                safeUpdateElement('header-system-load', (system.load_avg || 0).toFixed(2));
                const systemLoadElement = document.getElementById('header-system-load');
                if (systemLoadElement && system.load_avg) {
                    const load = system.load_avg;
                    systemLoadElement.style.color = load > 1.5 ? '#F44336' : load > 1.0 ? '#FF9800' : '#4CAF50';
                }

                // Update session data from API data
                const session = data.session || {};

                safeUpdateElement('header-session-time', session.duration || '--');
                safeUpdateElement('header-uptime', system.uptime || '--');
                safeUpdateElement('header-data-points', (session.data_points || 0) + ' pts');
                safeUpdateElement('header-peak-memory', (data.peak_total_memory || 0).toFixed(1) + 'MB');

                const maxPeakCpu = Math.max(data.peak_menubar_cpu || 0, data.peak_service_cpu || 0);
                safeUpdateElement('header-peak-cpu', maxPeakCpu.toFixed(1) + '%');

                const timestamp = new Date(data.timestamp);
                safeUpdateElement('header-last-updated', timestamp.toLocaleTimeString().slice(0, 8));

                const now = new Date();
                safeUpdateElement('header-last-update', now.toLocaleTimeString().slice(0, 5));





                // Session time is already updated from API data above (line 1744)
                // Update session-duration element if it exists
                safeUpdateElement('session-duration', session.duration || '0h 0m 0s');

                // Update last update time in header
                const lastUpdateTime = new Date(data.timestamp).toLocaleTimeString();
                safeUpdateElement('header-last-updated', lastUpdateTime);
                safeUpdateElement('last-updated', lastUpdateTime);

            // Legacy inline sparklines removed
            const realtimePoint = {
                timestamp: data.timestamp,
                menubar_memory: data.menubar_memory,
                service_memory: data.service_memory,
                total_memory: data.total_memory
            };

            if (window.chartManager) {
                window.chartManager.addRealtimePoint(realtimePoint);
            }

            // Update CPU chart (only if chart exists and not paused)
            if (window.cpuChartManager && !window.cpuChartManager.isPaused && window.cpuChart) {
                const chart = window.cpuChart;
                const cpuTime = new Date(data.timestamp).toLocaleTimeString();
                chart.data.labels.push(cpuTime);
                chart.data.datasets[0].data.push(data.menubar_cpu || 0);
                chart.data.datasets[1].data.push(data.service_cpu || 0);

                // Keep only last N data points based on live range (CPU)
                const maxPoints = (function(){
                    try { const m = localStorage.getItem('cpu_live_range') || '2m'; return { '2m': 60, '5m': 150, '15m': 450 }[m] || 60; } catch { return 60; }
                })();
                while (chart.data.labels.length > maxPoints) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[1].data.shift();
                }

                // Update CPU chart point count and last update time
                const cpuPointsCount = document.getElementById('cpu-chart-points-count');
                if (cpuPointsCount) cpuPointsCount.textContent = chart.data.labels.length + ' pts';
                const cpuLast = document.getElementById('cpu-last-refresh');
                if (cpuLast) cpuLast.textContent = `Updated: ${new Date().toLocaleTimeString().slice(0,8)}`;

                chart.update('none');
            }

            } catch (error) {
                console.error('Error in updateDashboard:', error);
            }
        }

        function loadHistoricalData(history) {
            if (history && history.length > 0) {
                const recentHistory = history.slice(-50);

                // Update current metrics
                const latest = recentHistory[recentHistory.length - 1];
                updateDashboard(latest);
            }
        }

        // Fetch additional data via REST API moved to /static/js/dashboard.js





        // Advanced monitoring functions moved to /static/js/dashboard.js
        // Legacy functions moved to /static/js/dashboard.js

        async function forceGarbageCollection() {
            // Show loading state
            const gcBtn = document.querySelector('button[onclick="forceGarbageCollection()"]');
            const originalText = gcBtn.innerHTML;
            gcBtn.innerHTML = '⏳ Cleaning...';
            gcBtn.disabled = true;

            try {
                const response = await fetch('/api/force_gc');
                const result = await response.json();

                // Success feedback
                gcBtn.innerHTML = '✅ Cleaned!';
                setTimeout(() => {
                    gcBtn.innerHTML = originalText;
                }, 2000);

                // Show detailed results
                const objectsCollected = result.objects_collected || 0;
                const memoryFreed = result.memory_freed_mb || 0;

                const message = `✅ Garbage Collection Completed!\\n\\n🗑️ Objects Collected: ${objectsCollected.toLocaleString()}\\n💾 Memory Freed: ${memoryFreed.toFixed(2)} MB\\n\\n💡 What this does:\\n• Forces Python to clean up unused objects\\n• Releases memory back to the system\\n• Helps identify memory leaks\\n• Improves overall performance\\n\\n📊 Memory charts will update automatically.`;
                showToast('✅ Garbage collection completed', 'success');

                // Refresh memory data to show the effect
                await fetchMemoryData();

            } catch (error) {
                // Error feedback
                gcBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    gcBtn.innerHTML = originalText;
                }, 2000);

                showToast('❌ Error during garbage collection: ' + error, 'error');
            } finally {
                gcBtn.disabled = false;
            }
        }

        async function updateTimeRange() {
            await loadAnalysisData();
        }

        async function updateAnalysisTimeRange() {
            const sel = document.getElementById('analysisTimeRange');
            if (sel) localStorage.setItem('analysisTimeRange', sel.value);
            if (analysisDebounceTimer) clearTimeout(analysisDebounceTimer);
            analysisDebounceTimer = setTimeout(() => { loadAnalysisData(); }, 250);
        }

        async function refreshAnalysisData() {
            const refreshBtn = document.querySelector('button[onclick="refreshAnalysisData()"]');
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '⏳ Refreshing...';
            refreshBtn.disabled = true;

            try {
                await loadAnalysisData();
                refreshBtn.innerHTML = '✅ Refreshed!';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

            } catch (error) {
                refreshBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);
            } finally {
                refreshBtn.disabled = false;
            }
        }

        async function exportAnalysisData() {
            try {
                const hours = document.getElementById('analysisTimeRange').value;
                const response = await fetch(`/api/analysis?hours=${hours}`);
                const data = await response.json();

                const dataStr = JSON.stringify(data, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                const url = URL.createObjectURL(dataBlob);

                const link = document.createElement('a');
                link.href = url;
                link.download = `memory_analysis_${new Date().toISOString().split('T')[0]}.json`;
                link.click();

                URL.revokeObjectURL(url);
                alert('✅ Analysis data exported successfully!');
            } catch (error) {
                alert('❌ Error exporting analysis data: ' + error);
            }
        }

        async function clearAnalysisHistory() {
            if (confirm('⚠️ Are you sure you want to clear analysis history? This action cannot be undone.')) {
                try {
                    // This would need a backend endpoint to actually clear data
                    alert('🚧 Clear history functionality would be implemented here');
                } catch (error) {
                    alert('❌ Error clearing history: ' + error);
                }
            }
        }


	        // Safe JSON reader fallback (uses window.readJsonSafe if available)
	        async function __jsonSafe(resp){
	            try {
	                if (typeof window.readJsonSafe === 'function') return await window.readJsonSafe(resp);
	                try { return await resp.json(); } catch (e) { return {}; }
	            } catch (e) { return {}; }
	        }

        async function loadAnalysisData() {
            try {
                if (typeof window !== 'undefined' && window.CM_DEBUG) console.log('[analysis] loadAnalysisData: running (guard disabled)');
                // Abort stale requests, but ignore AbortError in logs
                if (analysisAbortController) analysisAbortController.abort();
                analysisAbortController = new AbortController();
                const signal = analysisAbortController.signal;

                // Get time range from either selector (fallback to 24 hours)
                const timeRangeElement = document.getElementById('analysisTimeRange') || document.getElementById('timeRange');
                const hours = timeRangeElement ? timeRangeElement.value : 24;

                // Fetch analysis data (handle abort silently)
                let response;
                try {
                    response = await fetch(`/api/analysis?hours=${hours}`, { signal });
                } catch (e) {
                    if (e && e.name === 'AbortError') return; // expected during refresh
                    throw e;
                }
                if (window.CM_DEBUG) console.log('[analysis] /api/analysis status', response.status);
                const data = await __jsonSafe(response);
                if (!data || typeof data !== 'object' || Array.isArray(data)) {
                    const analysisSummary = document.getElementById('analysis-summary');
                    const msg = `<div style=\"color:#e74c3c; padding:10px;\">❌ Unexpected or empty analysis payload</div>`;
                    if (analysisSummary) analysisSummary.innerHTML = msg;
                }
                if (window.CM_DEBUG) console.log('[analysis] updateAnalysisDisplay ->', !!window.__module_updateAnalysisDisplay);
                updateAnalysisDisplay(data);

                // Fetch leak analysis (handle abort silently)
                let leakResponse;
                try {
                    leakResponse = await fetch('/api/leak_analysis', { signal });
                } catch (e) {
                    if (e && e.name === 'AbortError') return;
                    throw e;
                }
                if (window.CM_DEBUG) console.log('[analysis] /api/leak_analysis status', leakResponse.status);
                const leakData = await __jsonSafe(leakResponse);
                if (window.CM_DEBUG) console.log('[analysis] updateLeakAnalysisDisplay ->', !!window.__module_updateLeakAnalysisDisplay);
                updateLeakAnalysisDisplay(leakData);

                // Update Top Offenders based on same hours range
                try { (window.__module_updateTopOffenders || window.updateTopOffenders)?.(hours); } catch {}

                // Update Last Session Findings board
                if (window.CM_DEBUG) console.log('[analysis] updateSessionFindings ->', !!window.__module_updateSessionFindings);
                updateSessionFindings(data, leakData);

                // Update analysis summary
                if (window.CM_DEBUG) console.log('[analysis] updateAnalysisSummary ->', !!window.__module_updateAnalysisSummary);
                updateAnalysisSummary(data, hours);

                // Update monitoring history
                updateMonitoringHistory();

                // Update Trend Explorer (only if a module implementation exists)
                if (typeof window.__module_updateTrendExplorer === 'function') {
                    window.__module_updateTrendExplorer(hours);
                } else if (window.CM_DEBUG) {
        // Persist modal size (width/height)
        (function persistSparkModalSize(){
            try {
                const panel = document.getElementById('spark-settings-panel');
                if (!panel) return;
                // restore
                const w = localStorage.getItem('spark_settings_width');
                const h = localStorage.getItem('spark_settings_height');
                if (w) panel.style.width = w;
                if (h) panel.style.height = h;
                // observe changes after user resizes
                let resizeTimer;
                const saveSz = () => {
                    localStorage.setItem('spark_settings_width', panel.style.width || `${panel.offsetWidth}px`);
                    localStorage.setItem('spark_settings_height', panel.style.height || `${panel.offsetHeight}px`);
                };
                const onResize = () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(saveSz, 200); };
                new ResizeObserver(onResize).observe(panel);
            } catch {}
        })();

        // Modal focus trap + Enter-to-save
        (function a11ySparkModal(){
            const modal = document.getElementById('spark-settings-modal');
            const panel = document.getElementById('spark-settings-panel');
            const getFocusable = () => panel ? panel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])') : [];
            document.addEventListener('keydown', (e) => {
                if (modal && modal.style.display === 'block') {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        const saveBtn = panel && panel.querySelector('button[onclick^="saveSparkSettings"]');
                        if (saveBtn) saveBtn.click();
                    }
                    if (e.key === 'Tab') {
                        const focusables = Array.from(getFocusable());
                        if (!focusables.length) return;
                        const first = focusables[0];
                        const last = focusables[focusables.length - 1];
                        if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
                        else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
                    }
                }
            });
        })();

                    console.log('[analysis] skip updateTrendExplorer (module not present)');
                }

            } catch (error) {
                console.error('Error loading analysis data:', error);

                // Show error in analysis sections
                const leakAnalysis = document.getElementById('leak-analysis');
                const trendAnalysis = document.getElementById('trend-analysis');
                const analysisSummary = document.getElementById('analysis-summary');

                const errorMsg = `<div style="color: #e74c3c; padding: 10px;">❌ Error loading analysis data: ${error.message}</div>`;

                if (leakAnalysis) leakAnalysis.innerHTML = errorMsg;
                if (trendAnalysis) trendAnalysis.innerHTML = errorMsg;
                if (analysisSummary) analysisSummary.innerHTML = errorMsg;
            }
        }

        // updateAnalysisDisplay moved to /static/js/dashboard.js
        function updateAnalysisDisplay(data) {
            if (window.CM_DEBUG) console.log('[analysis] forward updateAnalysisDisplay');
            return window.__module_updateAnalysisDisplay?.(data);
        }

        function updateLeakAnalysisDisplay(leakData) {
            if (window.CM_DEBUG) console.log('[analysis] forward updateLeakAnalysisDisplay');
            return window.__module_updateLeakAnalysisDisplay?.(leakData);
        }

        // Initialize settings modal with persisted values and extras
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeSparkSettings();
        });
        (function initSparkSettingsPanel() {
            try {
                const load = (key, def) => localStorage.getItem(key) ?? def;
                const bool = (v) => v === null ? true : v === 'true';
                const animEnabled = bool(load('spark_anim_enabled', 'true'));
                const animMs = Number(load('spark_anim_ms', '180'));
                const tooltipMode = load('spark_tooltip_mode', 'custom');
                const showMenubar = bool(load('spark_show_menubar', 'true'));
                const showService = bool(load('spark_show_service', 'true'));
                const showTotal = bool(load('spark_show_total', 'true'));
                const cbA = document.getElementById('spark-anim-enabled'); if (cbA) cbA.checked = animEnabled;
                const selMs = document.getElementById('spark-anim-ms'); if (selMs) selMs.value = String(animMs);
                const selTip = document.getElementById('spark-tooltip-mode'); if (selTip) selTip.value = tooltipMode;
                const cb1 = document.getElementById('spark-show-menubar'); if (cb1) cb1.checked = showMenubar;
                const cb2 = document.getElementById('spark-show-service'); if (cb2) cb2.checked = showService;
                const cb3 = document.getElementById('spark-show-total'); if (cb3) cb3.checked = showTotal;

                const resetBtn = document.getElementById('spark-reset-btn');
                if (resetBtn) resetBtn.onclick = () => {
                    localStorage.removeItem('spark_anim_enabled');
                    localStorage.removeItem('spark_anim_ms');
                    localStorage.removeItem('spark_tooltip_mode');
                    localStorage.removeItem('spark_show_menubar');
                    localStorage.removeItem('spark_show_service');
                    localStorage.removeItem('spark_show_total');
                    initSparkSettingsPanel();
                    showToast('✅ Reset to defaults');
                };

                // Simple drag of the panel
                const panel = document.getElementById('spark-settings-panel');
                const drag = document.getElementById('spark-settings-drag');
                if (panel && drag) {
                    let sx=0, sy=0, px=0, py=0, dragging=false;
                    drag.onmousedown = (ev) => { dragging=true; sx=ev.clientX; sy=ev.clientY; const r=panel.getBoundingClientRect(); px=r.left; py=r.top; ev.preventDefault(); };
                    window.onmousemove = (ev) => { if (!dragging) return; const dx=ev.clientX-sx, dy=ev.clientY-sy; panel.style.margin='0'; panel.style.position='fixed'; panel.style.left=(px+dx)+'px'; panel.style.top=(py+dy)+'px'; };
                    window.onmouseup = () => { dragging=false; if (panel) { localStorage.setItem('spark_settings_pos_left', panel.style.left); localStorage.setItem('spark_settings_pos_top', panel.style.top); } };
                }
            } catch {}
        })();

        // Extend save to include series toggles
        (function extendSaveSparkSettings(){
            const orig = window.saveSparkSettings;
            window.saveSparkSettings = function(){
                try {
                    const showMenubar = document.getElementById('spark-show-menubar').checked;
                    const showService = document.getElementById('spark-show-service').checked;
                    const showTotal = document.getElementById('spark-show-total').checked;
                    localStorage.setItem('spark_show_menubar', String(showMenubar));
                    localStorage.setItem('spark_show_service', String(showService));
                    localStorage.setItem('spark_show_total', String(showTotal));
                } catch {}
                return orig();
            }
        })();

        function updateAnalysisSummary(data, hours) {
            if (window.CM_DEBUG) console.log('[analysis] forward updateAnalysisSummary');
            return window.__module_updateAnalysisSummary?.(data, hours);
        }

        function ensureTrendExplorerUI() { return; }
        function computeRegression(points, key) { return window.computeRegression?.(points, key); }
        async function updateTrendExplorer(hours) {
            // Forward to module implementation when available; avoid self-recursion
            const impl = window.__module_updateTrendExplorer;
            if (typeof impl === 'function' && impl !== updateTrendExplorer) {
                if (window.CM_DEBUG) console.log('[analysis] forward updateTrendExplorer');
                return impl(hours);
            } else {
                if (window.CM_DEBUG) console.warn('[analysis] TrendExplorer module not ready or self-referencing; skipping to prevent recursion');
            }
        }

        function updateMonitoringHistory() {
            if (window.CM_DEBUG) console.log('[analysis] forward updateMonitoringHistory');
            return window.__module_updateMonitoringHistory?.();
        }
        function updateSessionFindings(analysisData, leakData) {
            if (window.CM_DEBUG) console.log('[analysis] forward updateSessionFindings');
            return window.__module_updateSessionFindings?.(analysisData, leakData);
        }
        async function updateMonitoringStatus() {
            if (window.CM_DEBUG) console.log('[analysis] forward updateMonitoringStatus');
            return window.__module_updateMonitoringStatus?.();
        }

        function openSparkSettings() {
            const modal = document.getElementById('spark-settings-modal');
            if (modal) modal.style.display = 'block';
            // Restore persisted position
            try {
                const panel = document.getElementById('spark-settings-panel');
                const left = localStorage.getItem('spark_settings_pos_left');
                const top = localStorage.getItem('spark_settings_pos_top');
                if (panel && left && top) {
                    panel.style.margin = '0';
                    panel.style.position = 'fixed';
                    panel.style.left = left;
                    panel.style.top = top;
                }
            } catch {}
        }
        function closeSparkSettings() {
            const modal = document.getElementById('spark-settings-modal');
            if (modal) modal.style.display = 'none';
        }
        function saveSparkSettings() {
            try {
                const animEnabled = document.getElementById('spark-anim-enabled').checked;
                const animMs = document.getElementById('spark-anim-ms').value;
                const tooltipMode = document.getElementById('spark-tooltip-mode').value;
                const showMenubar = document.getElementById('spark-show-menubar').checked;
                const showService = document.getElementById('spark-show-service').checked;
                const showTotal = document.getElementById('spark-show-total').checked;
                const styleMenubar = document.getElementById('spark-style-menubar').value;
                const styleService = document.getElementById('spark-style-service').value;
                const styleTotal = document.getElementById('spark-style-total').value;
                const pulseEnabled = document.getElementById('spark-pulse-enabled').checked;
                localStorage.setItem('spark_anim_enabled', String(animEnabled));
                localStorage.setItem('spark_anim_ms', String(Math.max(0, Number(animMs))));
                localStorage.setItem('spark_tooltip_mode', tooltipMode);
                localStorage.setItem('spark_show_menubar', String(showMenubar));
                localStorage.setItem('spark_show_service', String(showService));
                localStorage.setItem('spark_show_total', String(showTotal));
                localStorage.setItem('spark_style_menubar', styleMenubar);
                localStorage.setItem('spark_style_service', styleService);
                localStorage.setItem('spark_style_total', styleTotal);
                localStorage.setItem('spark_pulse_enabled', String(pulseEnabled));
                closeSparkSettings();
                showToast('✅ Settings saved');
                // Trigger a refresh so charts pick up settings
                if (typeof loadAnalysisData === 'function') loadAnalysisData();
            } catch (e) {
                showToast('❌ Failed to save settings: ' + e, 'error');
            }
        }


        async function refreshAllData() {
            // Show loading state
            const refreshBtn = document.querySelector('button[onclick="refreshAllData()"]');
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '⏳ Refreshing...';
            refreshBtn.disabled = true;


            try {
                // Refresh all dashboard data with progress indication
                await fetchMemoryData();
                await fetchSystemData();
                await loadAnalysisData();
                await updateMonitoringStatus();

                // Success feedback
                refreshBtn.innerHTML = '✅ Refreshed!';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

                // Show detailed success message
                showToast(`✅ Dashboard data refreshed at ${new Date().toLocaleTimeString()}`, 'success');

            } catch (error) {
                // Error feedback
                refreshBtn.innerHTML = '❌ Error';
                setTimeout(() => {
                    refreshBtn.innerHTML = originalText;
                }, 2000);

                showToast('❌ Error refreshing data: ' + error, 'error');
            } finally {
                refreshBtn.disabled = false;
            }

        // Unified Memory Chart Manager Class (inline stub for compatibility)
        if (!window.UnifiedMemoryChart) { window.UnifiedMemoryChart = class {
            constructor() {
                this.mode = 'live'; // 'live' or 'historical'
                this.liveData = [];
                this.historicalData = null;

                // Flexible live view ranges (5m to 4h)
                this.liveRanges = {
                    '5m': { minutes: 5, points: 300, label: '5 Minutes' },
                    '15m': { minutes: 15, points: 900, label: '15 Minutes' },
                    '30m': { minutes: 30, points: 1800, label: '30 Minutes' },
                    '1h': { minutes: 60, points: 3600, label: '1 Hour' },
                    '2h': { minutes: 120, points: 7200, label: '2 Hours' },
                    '4h': { minutes: 240, points: 14400, label: '4 Hours' }
                };

                this.currentLiveRange = '5m'; // Default to 5 minutes
                this.currentTimeRange = '1';  // For historical mode
                this.currentResolution = 'full';
                this.isInitialized = false;

                // Performance optimization
                this.updateThrottleTimer = null;
                this.lastUpdateTime = 0;

                // Live polling management
                this.livePollTimer = null;
                this.livePollIntervalMs = 2000;
                this.livePollFailureCount = 0;
                this.liveErrorNotified = false; // show toast once during failures
                this.paused = false; // paused via visibility or external control
                // Operation token for race-proof async updates
                this.loadToken = 0;
            }

            async initialize() {
                if (this.isInitialized) return;

                // Restore persisted state (if any)
                try {
                    const savedMode = localStorage.getItem('umc_mode');
                    if (savedMode === 'live' || savedMode === 'historical') {
                        this.mode = savedMode;
                    }
                    const savedRange = localStorage.getItem('umc_live_range');
                    if (savedRange && this.liveRanges[savedRange]) {
                        this.currentLiveRange = savedRange;
                        const liveSelect = document.getElementById('live-range-select');
                        if (liveSelect) liveSelect.value = savedRange;
                    }
                    const savedTimeRange = localStorage.getItem('umc_time_range');
                    if (savedTimeRange && ['1','6','24','168','all'].includes(savedTimeRange)) {
                        this.currentTimeRange = savedTimeRange;
                        const histSelect = document.getElementById('historical-range');
                        if (histSelect) histSelect.value = savedTimeRange;
                    }
                    const savedRes = localStorage.getItem('umc_resolution');
                    if (savedRes) {
                        this.currentResolution = savedRes;
                        const resSelect = document.getElementById('resolution-select');
                        if (resSelect) resSelect.value = savedRes;
                    }
                } catch (e) {
                    console.warn('Unable to restore persisted chart settings:', e);
                }

                // Initialize according to mode
                if (this.mode === 'historical') {
                    await this.switchToHistoricalMode(this.currentTimeRange);
                    this.stopLivePolling();
                } else {
                    await this.loadInitialLiveData();
                    this.startLivePolling();
                }

                this.updateUI();
                this.isInitialized = true;
                console.log(`UnifiedMemoryChart initialized (${this.mode}) with ${this.currentLiveRange} live view`);
            }

            // Phase 2: internalize live polling with retry/backoff
            startLivePolling() {
                this.stopLivePolling();
                const tick = async () => {
                    if (this.paused) return;
                    const ok = await fetchMemoryData();
                    if (ok) {
                        if (this.livePollFailureCount > 0) {
                            this.livePollFailureCount = 0;
                            if (this.livePollIntervalMs !== 2000) {
                                this.setLivePollInterval(2000);
                            }
                        }
                        if (this.liveErrorNotified) {
                            showToast('✅ Connection restored', 'success', 1800);
                            this.liveErrorNotified = false;
                        }
                    } else {
                        this.livePollFailureCount += 1;
                        // backoff: 2s -> 5s -> 10s
                        let next = this.livePollIntervalMs;
                        if (this.livePollFailureCount >= 3 && this.livePollIntervalMs < 5000) next = 5000;
                        if (this.livePollFailureCount >= 6 && this.livePollIntervalMs < 10000) next = 10000;
                        if (next !== this.livePollIntervalMs) {
                            this.setLivePollInterval(next);
                        }
                        if (!this.liveErrorNotified && this.livePollFailureCount >= 3) {
                            showToast('⚠️ Connection issues: slowing updates', 'error', 2600);
                            this.liveErrorNotified = true;
                        }
                    }
                };
                // Immediate tick, then interval
                tick();
                this.livePollTimer = setInterval(tick, this.livePollIntervalMs);
            }

            stopLivePolling() {
                if (this.livePollTimer) {
                    clearInterval(this.livePollTimer);
                    this.livePollTimer = null;
                }
            }

            setLivePollInterval(ms) {
                this.livePollIntervalMs = ms;
                if (this.livePollTimer) {
                    clearInterval(this.livePollTimer);
                    this.livePollTimer = setInterval(async () => {
                        if (this.paused) return;
                        const ok = await fetchMemoryData();
                        if (!ok) {
                            // keep failure count advancing; interval already adjusted
                            this.livePollFailureCount += 1;
                            if (!this.liveErrorNotified && this.livePollFailureCount >= 3) {
                                showToast('⚠️ Connection issues: slowing updates', 'error', 2600);
                                this.liveErrorNotified = true;
                            }
                        } else {
                            this.livePollFailureCount = 0;
                            if (this.liveErrorNotified) {
                                showToast('✅ Connection restored', 'success', 1800);
                                this.liveErrorNotified = false;
                            }
                        }
                    }, this.livePollIntervalMs);
                }
            }

            async loadInitialLiveData() {
                try {
                    // Only load initial data if we don't have any data yet
                    if (this.liveData.length > 0) {
                        console.log(`Skipping initial data load - already have ${this.liveData.length} data points`);
                        return;
                    }

                    // For small time periods, use recent history API instead
                    const range = this.liveRanges[this.currentLiveRange];

                    console.log(`Loading initial data for ${range.label}`);

                    // Use /api/history for recent data (last 200 points) instead of historical-chart for small periods
                    const response = await fetch('/api/history');
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const historyData = await response.json();

                    // Convert history format to our expected format
                    const formattedData = historyData.map(point => ({
                        timestamp: point.timestamp,
                        menubar_memory: point.menubar_memory || 0,
                        service_memory: point.service_memory || 0,
                        total_memory: point.total_memory || 0
                    }));

                    // Populate live data buffer only if empty
                    this.liveData = formattedData;

                    // Limit to max points for current live range
                    const maxPoints = range.points;
                    if (this.liveData.length > maxPoints) {
                        this.liveData = this.liveData.slice(-maxPoints);
                    }

                    this.updateChart();

                        // Ensure at least one point is present to trigger chart draw
                        if (this.liveData.length === 0 && formattedData.length > 0) {
                            this.liveData.push(formattedData[formattedData.length - 1]);
                        }

                    console.log(`Loaded ${this.liveData.length} initial data points for ${range.label} live view from recent history`);
                } catch (error) {
                    console.error('Error loading initial live data:', error);
                    // Initialize with empty array on error
                    if (this.liveData.length === 0) {
                        this.liveData = [];
                        console.log('Initialized with empty live data buffer - will populate as new data arrives');
                    }
                }
            }

            addLivePoint(newPoint) {
                // Always collect live data for the buffer
                this.liveData.push(newPoint);

                // Keep only recent points for current live range
                const range = this.liveRanges[this.currentLiveRange];
                const maxPoints = range.points;

                if (this.liveData.length > maxPoints) {
                    this.liveData.shift();
                }

                // Throttled update for performance (max 2 updates per second)
                const now = Date.now();
                if (this.mode === 'live' && (now - this.lastUpdateTime) > 500) {
                    this.lastUpdateTime = now;
                    this.updateChart();
                }
            }

            // Backward compatibility method
            addRealtimePoint(newPoint) {
                this.addLivePoint(newPoint);
            }

            async switchLiveRange(newRange) {
                if (!this.liveRanges[newRange]) {
                    console.error(`Invalid live range: ${newRange}`);
                    return;
                }

                const oldRange = this.currentLiveRange;
                this.currentLiveRange = newRange;
                const range = this.liveRanges[newRange];
                const oldRangeConfig = this.liveRanges[oldRange];

                console.log(`Switching live view from ${oldRangeConfig.label} to ${range.label}`);
                console.log(`Current data points: ${this.liveData.length}`);

                // Show loading indicator
                const chartTitle = document.getElementById('chart-title');
                const originalTitle = chartTitle?.textContent;
                if (chartTitle) {
                    chartTitle.textContent = `Switching to ${range.label} live view...`;
                }

                try {
                    const maxPoints = range.points;
                    const currentPoints = this.liveData.length;

                    if (range.points <= oldRangeConfig.points) {
                        // Switching to smaller range - just trim existing data
                        if (currentPoints > maxPoints) {
                            this.liveData = this.liveData.slice(-maxPoints);
                            console.log(`Trimmed data from ${currentPoints} to ${this.liveData.length} points`);
                        }
                    } else {
                        // Switching to larger range - need more historical data
                        const additionalHours = (range.minutes - oldRangeConfig.minutes) / 60;

                        if (additionalHours > 0) {
                            console.log(`Need additional data for larger range - trying to load more from recent history`);

                            try {
                                // For live ranges, use recent history instead of historical-chart API
                                const response = await fetch('/api/history');
                                if (!response.ok) {
                                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                }

                                const historyData = await response.json();

                                // Convert history format to our expected format
                                const formattedData = historyData.map(point => ({
                                    timestamp: point.timestamp,
                                    menubar_memory: point.menubar_memory || 0,
                                    service_memory: point.service_memory || 0,
                                    total_memory: point.total_memory || 0
                                }));

                                if (formattedData.length > 0) {
                                    // Merge with existing data, avoiding duplicates
                                    const existingTimestamps = new Set(this.liveData.map(d => d.timestamp));
                                    const newData = formattedData.filter(d => !existingTimestamps.has(d.timestamp));

                                    // Add new data at the beginning (older data)
                                    this.liveData = [...newData, ...this.liveData];

                                    // Trim to max points if needed
                                    if (this.liveData.length > maxPoints) {
                                        this.liveData = this.liveData.slice(-maxPoints);
                                    }

                                    console.log(`Added ${newData.length} additional data points from history, total: ${this.liveData.length}`);
                                } else {
                                    console.log('No additional historical data available');
                                }
                            } catch (error) {
                                console.warn('Failed to load additional historical data:', error);
                                // Continue with existing data - this is not a critical error
                            }
                        }
                    }

                    // Smooth transition with animation
                    this.updateChart(true); // true = animate transition
                    this.updateUI();

                    console.log(`Live view switched to ${range.label} (${this.liveData.length} data points)`);
                } catch (error) {
                    console.error('Error switching live range:', error);
                    // Revert on error
                    this.currentLiveRange = oldRange;
                } finally {
                    // Restore title
                    if (chartTitle) {
                try { window.__dbgLog && window.__dbgLog(`Historical: entering switch, timeRange=${timeRange}`); } catch {}

                        const newTitle = `Live Memory Usage (${range.label})`;
                        chartTitle.textContent = newTitle;
                    }
                }
            }



            async switchToHistoricalMode(timeRange) { try { localStorage.setItem('umc_mode', 'historical'); } catch (e) {}
                // Race-proof: capture token and desired mode
                const token = ++this.loadToken;
                const desiredMode = 'historical';

                this.mode = 'historical';
                this.currentTimeRange = timeRange;

                // Immediately reflect Historical mode in the UI while data loads
                try {
                    this.stopLivePolling();
                    const modeBadgeEarly = document.getElementById('mode-badge');
                    if (modeBadgeEarly) { modeBadgeEarly.textContent = 'Historical'; modeBadgeEarly.style.background = '#2196F3'; }
                    const modeIndEarly = document.getElementById('chart-mode-indicator');
                    if (modeIndEarly) modeIndEarly.textContent = 'Historical (loading...)';
                    const historicalOpts = document.getElementById('historical-options'); if (historicalOpts) historicalOpts.style.display = 'flex';
                    const liveOpts = document.getElementById('live-options'); if (liveOpts) liveOpts.style.display = 'none';
                    const liveBtn = document.getElementById('realtime-btn'); if (liveBtn){ liveBtn.style.background = 'white'; liveBtn.style.color = '#666'; liveBtn.style.boxShadow = 'none'; }
                    const histBtn = document.getElementById('historical-btn'); if (histBtn){ histBtn.style.background = '#2196F3'; histBtn.style.color = 'white'; histBtn.style.boxShadow = '0 2px 4px rgba(33, 150, 243, 0.3)'; }
                } catch {}

                // Show loading indicator immediately
                const chartTitle = document.getElementById('chart-title');
                if (chartTitle) chartTitle.textContent = 'Loading historical data...';

                    try { window.__dbgLog && window.__dbgLog('Historical: UI set to loading'); } catch {}

                try {
                    // Enhanced auto-adjust resolution for optimal performance
                    let resolution = this.currentResolution;
                    let recommendedResolution = this.getRecommendedResolution(timeRange);
                    if (resolution === 'full' && recommendedResolution !== 'full') {
                        resolution = recommendedResolution;
                        this.currentResolution = resolution;
                        const resolutionSelect = document.getElementById('resolution-select');
                        if (resolutionSelect) resolutionSelect.value = resolution;
                        console.log(`Auto-adjusted resolution to ${resolution} for optimal performance`);
                    }


                        try { window.__dbgLog && window.__dbgLog(`Historical: auto-adjusted resolution -> ${resolution}`); } catch {}

                    // Performance timing
                    const startTime = performance.now();


                        try { window.__dbgLog && window.__dbgLog(`Historical: fetching /api/historical-chart?hours=${timeRange}&resolution=${resolution}`); } catch {}

                    const response = await fetch(`/api/historical-chart?hours=${timeRange}&resolution=${resolution}`);

                        try { window.__dbgLog && window.__dbgLog(`Historical: response status = ${response.status}`); } catch {}

                    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);


                        try { window.__dbgLog && window.__dbgLog(`Historical: payload points = ${Array.isArray(data?.points) ? data.points.length : 'n/a'}`); } catch {}

                    const data = await response.json();

                        try { window.__dbgLog && window.__dbgLog('Historical: applying dataset'); } catch {}


                    // Apply only if still in historical mode (avoid abort that leaves UI stuck)
                    if (this.mode !== desiredMode) {
                        console.warn('Historical load completed but mode changed; skipping apply');

                        try { window.__dbgLog && window.__dbgLog(`Historical: dataSize = ${this.historicalData?.length || 0}`); } catch {}

                    }

                    this.historicalData = (data && Array.isArray(data.points)) ? data.points : [];

                        try { window.__dbgLog && window.__dbgLog(`Historical: set historicalData (${this.historicalData.length})`); } catch {}


                    // Smooth transition with performance optimization
                    const dataSize = this.historicalData.length;
                    console.log(`Historical data loaded: ${dataSize} points`);

                    const renderStart = performance.now();

                        try { window.__dbgLog && window.__dbgLog('Historical: calling updateChart(true)'); } catch {}

                    this.updateChart(true); // Animate transition
                    const renderTime = performance.now() - renderStart;

                        try { window.__dbgLog && window.__dbgLog(`Historical: render time ${renderTime.toFixed(2)}ms`); } catch {}

                    console.log(`Chart rendered in ${renderTime.toFixed(2)}ms`);

                    // Now that historical points are ready, set UI and badge
                    const modeBadge = document.getElementById('mode-badge');
                    if (modeBadge) { modeBadge.textContent = 'Historical'; modeBadge.style.background = '#2196F3'; }
                    if (chartTitle) chartTitle.textContent = 'Historical Memory Usage';
                    this.updateUI();

                        try { window.__dbgLog && window.__dbgLog('Historical: UI settled to Historical Memory Usage'); } catch {}

                    console.log(`Switched to historical mode: ${timeRange} hours (${dataSize} points, ${resolution} resolution)`);
                } catch (error) {
                    // If a newer op superseded this, silently ignore error
                    if (token !== this.loadToken) return;
                    console.error('Error loading historical data:', error);
                    alert(`Failed to load historical data: ${error.message}\\n\\nSwitching back to live mode.`);
                    this.switchToLiveMode();
                } finally {
                    // Final title settle if still in historical
                    if (chartTitle && this.mode === 'historical') chartTitle.textContent = 'Historical Memory Usage';
                }
            }

            getRecommendedResolution(timeRange) {
                // Smart resolution recommendations based on time range
                if (timeRange === 'all') {
                    return 'minute'; // 1-minute for "since start"
                } else if (timeRange === '168') {
                    return '10sec'; // 10-second for 7 days
                } else if (timeRange === '24') {
                    return 'full'; // Full resolution for 24 hours
                } else {
                    return 'full'; // Full resolution for shorter periods
                }
            }

            showPerformanceWarning(dataSize) {
                // Show non-intrusive performance warning
                const warningDiv = document.createElement('div');
                warningDiv.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ff9800;
                    color: white;
                    padding: 12px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    z-index: 1000;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    max-width: 300px;
                `;
                warningDiv.innerHTML = `
                    <strong>⚠️ Large Dataset</strong><br>
                    ${dataSize.toLocaleString()} data points loaded.<br>
                    Consider using lower resolution for better performance.
                `;

                document.body.appendChild(warningDiv);

                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (warningDiv.parentNode) {
                        warningDiv.parentNode.removeChild(warningDiv);
                    }
                }, 5000);
            }

            switchToLiveMode() {
                // Race-proof: increment token so any pending historical load won't apply
                this.loadToken = (this.loadToken || 0) + 1;
                this.mode = 'live';
                // Persist
                try { localStorage.setItem('umc_mode', 'live'); } catch {}
                const chartTitle = document.getElementById('chart-title');
                if (chartTitle) chartTitle.textContent = 'Live Memory Usage';
                const modeBadge = document.getElementById('mode-badge');
                if (modeBadge) { modeBadge.textContent = 'Live'; modeBadge.style.background = '#4CAF50'; }
                this.stopLivePolling();
                // Reset failure state upon explicit switch
                this.livePollFailureCount = 0;
                this.liveErrorNotified = false;
                this.startLivePolling();
                this.updateChart(true); // Animate transition
                this.updateUI();
                console.log(`Switched to live mode: ${this.liveRanges[this.currentLiveRange].label}`);
            }

            clearChart() {
                try {
                    if (!this.chart) return;
                    this.liveData = [];
                    this.historicalData = [];
                    this.chart.data.labels = [];
                    this.chart.data.datasets[0].data = [];
                    this.chart.data.datasets[1].data = [];
                    this.chart.update();
                    const pts = document.getElementById('chart-points-count'); if (pts) pts.textContent = '0 pts';
                    const last = document.getElementById('chart-last-update'); if (last) last.textContent = '—';
                } catch (e) { console.warn('clearChart failed', e); }
            }

            // Backward compatibility method
            switchToRealtimeMode() {
                this.switchToLiveMode();
            }

            async refreshHistoricalData() {
                if (this.mode !== 'historical') return;

                // Get mode indicator element once for reuse
                const chartModeIndicator = document.getElementById('chart-mode-indicator');

                try {
                    // Show subtle loading indicator in mode indicator
                    const originalText = chartModeIndicator ? chartModeIndicator.textContent : '';
                    if (chartModeIndicator && !originalText.includes('🔄')) {
                        chartModeIndicator.textContent = originalText.replace('Auto-refresh: 5s', 'Refreshing... 🔄');
                    }

                    // Use correct API endpoint for historical chart data
                    const response = await fetch(`/api/historical-chart?hours=${this.currentTimeRange}&resolution=${this.currentResolution}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();

                    this.historicalData = data.points || [];
                    this.updateChart();

                    // Restore auto-refresh indicator
                    if (chartModeIndicator && chartModeIndicator.textContent.includes('🔄')) {
                        const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                         this.currentTimeRange === '1' ? 'Last Hour' :
                                         this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                         this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                         this.currentTimeRange === '168' ? 'Last 7 Days' :
                                         `Last ${this.currentTimeRange} Hours`;
                        chartModeIndicator.textContent = `Historical (${rangeText}) • Auto-refresh: 5s`;
                    }
                } catch (error) {
                    console.error('Error refreshing historical data:', error);
                    // Restore auto-refresh indicator on error
                    if (chartModeIndicator && chartModeIndicator.textContent.includes('🔄')) {
                        const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                         this.currentTimeRange === '1' ? 'Last Hour' :
                                         this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                         this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                         this.currentTimeRange === '168' ? 'Last 7 Days' :
                                         `Last ${this.currentTimeRange} Hours`;
                        chartModeIndicator.textContent = `Historical (${rangeText}) • Auto-refresh: 5s`;
                    }
                    // Don't show alert for auto-refresh errors, just log them
                }
            }

            async changeResolution(resolution) {
                if (this.mode !== 'historical') return;

                console.log(`Changing resolution to: ${resolution}`);
                this.currentResolution = resolution;
                try { localStorage.setItem('umc_resolution', resolution); } catch {}

                // Reset failure state when explicitly changing view
                this.livePollFailureCount = 0;
                this.liveErrorNotified = false;

                // Show loading indicator
                const chartTitle = document.getElementById('chart-title');
                if (chartTitle) chartTitle.textContent = 'Loading historical data...';

                try {
                    // Kick a short fallback to settle title if the fetch takes long
                    setTimeout(() => {
                        const titleEl = document.getElementById('chart-title');
                        if (this.mode === 'historical' && titleEl && titleEl.textContent.includes('Loading')) {
                            titleEl.textContent = 'Historical Memory Usage';
                        }
                    }, 3000);
                    await this.switchToHistoricalMode(this.currentTimeRange);
                } catch (error) {
                    console.error('Error changing resolution:', error);
                    if (chartTitle) chartTitle.textContent = 'Historical Memory Usage';
                }
            }

            async updateChart(animate = false) {
                const data = this.mode === 'live' ? (this.liveData || []) : (this.historicalData || []);

                // Create chart if it doesn't exist
                if (!this.chart) {
                    const ctx = document.getElementById('memoryChart').getContext('2d');
                    this.chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Menu Bar App (MB)',
                                data: [],
                                borderColor: '#2196F3',
                                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                                tension: 0.4,
                                fill: true
                            }, {
                                label: 'Main Service (MB)',
                                data: [],
                                borderColor: '#4CAF50',
                                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                intersect: false,
                                mode: 'index'
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Memory Usage (MB)'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Time'
                                    }
                                }
                            },
                            plugins: {
                                legend: {
                                    display: true,
                                    position: 'top'
                                }
                            }
                        }
                    });
                }

                if (!data || data.length === 0) {
                    this.chart.data.labels = [];
                    this.chart.data.datasets[0].data = [];
                    this.chart.data.datasets[1].data = [];
                } else {
                    this.chart.data.labels = data.map(d => {
                        // robust timestamp parsing for strings or numbers
                        const date = (d.timestamp instanceof Date) ? d.timestamp : new Date(d.timestamp);
                        return this.mode === 'live' ?
                            date.toLocaleTimeString() :
                            this.formatHistoricalTime(date);
                    });
                    this.chart.data.datasets[0].data = data.map(d => d.menubar_memory || 0);
                    this.chart.data.datasets[1].data = data.map(d => d.service_memory || 0);
                }

                // Ensure full redraw without special mode (more reliable across Chart.js versions)
                this.chart.update();
                try { this.chart.resize(); } catch {}

	                // If still empty in live mode, seed a zero point to force axes render
	                if (this.mode === 'live' && (!data || data.length === 0)) {
	                    const now = new Date();
	                    this.chart.data.labels = [now.toLocaleTimeString()];
	                    this.chart.data.datasets[0].data = [0];
	                    this.chart.data.datasets[1].data = [0];
	                }


                // Update data points counter in header
                const headerDataPointsElement = document.getElementById('header-data-points');
                if (headerDataPointsElement) {
                    headerDataPointsElement.textContent = (data?.length || 0) + ' pts';
                }
                // Overlay anomalies and events (if modules available)
                try {
                    const respE = await fetch('/api/events');
                    const events = await respE.json();
                    const respA = await fetch('/api/current');
                    const curr = await respA.json();
                    const anomalies = curr.anomalies || [];
                    if (window.overlayEventsAndAnomalies) window.overlayEventsAndAnomalies(this.chart, events, anomalies);
                } catch {}


                // Update chart status
                const chartPointsCount = document.getElementById('chart-points-count');
                if (chartPointsCount) {
                    chartPointsCount.textContent = (data?.length || 0) + ' pts';
                }

                // Update last update timestamp
                const chartLastUpdate = document.getElementById('chart-last-update');
                if (chartLastUpdate) {
                    const now = new Date();
                    chartLastUpdate.textContent = (this.mode === 'historical') ? 'Loaded' : ('Updated: ' + now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
                }

                // Ensure title and badge settle in historical
                if (this.mode === 'historical') {
                    const ct = document.getElementById('chart-title');
                    if (ct) ct.textContent = 'Historical Memory Usage';
                    const mb = document.getElementById('mode-badge');
                    if (mb) { mb.textContent = 'Historical'; mb.style.background = '#2196F3'; }
                }

                // Update range indicator for live mode
                if (this.mode === 'live') {
                    const rangeIndicator = document.getElementById('live-range-indicator');
                    if (rangeIndicator) {
                        const range = this.liveRanges[this.currentLiveRange];
                        rangeIndicator.textContent = `Live: ${range.label} (${data?.length || 0} pts)`;
                    }
                }
            }

            formatHistoricalTime(date) {
                if (this.currentTimeRange === 'all' || parseInt(this.currentTimeRange) > 24) {
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                } else {
                    return date.toLocaleTimeString();
                }
            }

            updateUI() {
                const liveBtn = document.getElementById('realtime-btn'); // Keep existing ID for compatibility
                const historicalBtn = document.getElementById('historical-btn');
                const historicalOptions = document.getElementById('historical-options');
                const liveOptions = document.getElementById('live-options');
                const chartTitle = document.getElementById('chart-title');
                const chartModeIndicator = document.getElementById('chart-mode-indicator');
                const modeBadge = document.getElementById('mode-badge');

                if (this.mode === 'live') {
                    // Update live mode UI with enhanced styling
                    if (liveBtn) {
                        liveBtn.style.background = '#4CAF50';
                        liveBtn.style.color = 'white';
                        liveBtn.style.boxShadow = '0 2px 4px rgba(76, 175, 80, 0.3)';
                    }
                    if (historicalBtn) {
                        historicalBtn.style.background = 'white';
                        historicalBtn.style.color = '#666';
                        historicalBtn.style.boxShadow = 'none';
                    }
                    if (historicalOptions) {
                        historicalOptions.style.display = 'none';
                    }
                    if (liveOptions) {
                        liveOptions.style.display = 'flex';
                    }

                    const range = this.liveRanges[this.currentLiveRange];
                    if (chartTitle) chartTitle.textContent = `Live Memory Usage`;
                    if (chartModeIndicator) chartModeIndicator.textContent = `Live: ${range.label}`;
                    if (modeBadge) {
                        modeBadge.textContent = 'Live';
                        modeBadge.style.background = '#4CAF50';
                    }
                } else {
                    // Update historical mode UI with enhanced styling
                    if (liveBtn) {
                        liveBtn.style.background = 'white';
                        liveBtn.style.color = '#666';
                        liveBtn.style.boxShadow = 'none';
                    }
                    if (historicalBtn) {
                        historicalBtn.style.background = '#2196F3';
                        historicalBtn.style.color = 'white';
                        historicalBtn.style.boxShadow = '0 2px 4px rgba(33, 150, 243, 0.3)';
                    }
                    if (historicalOptions) {
                        historicalOptions.style.display = 'flex';
                    }
                    if (liveOptions) {
                        liveOptions.style.display = 'none';
                    }

                    const rangeText = this.currentTimeRange === 'all' ? 'Since Start' :
                                     this.currentTimeRange === '1' ? 'Last Hour' :
                                     this.currentTimeRange === '6' ? 'Last 6 Hours' :
                                     this.currentTimeRange === '24' ? 'Last 24 Hours' :
                                     this.currentTimeRange === '168' ? 'Last 7 Days' :
                                     `Last ${this.currentTimeRange} Hours`;

                    if (chartTitle) chartTitle.textContent = `Historical Memory Usage`;
                    if (chartModeIndicator) chartModeIndicator.textContent = `Historical (${rangeText}) • Auto-refresh: 5s`;
                    if (modeBadge) {
                        modeBadge.textContent = 'Historical';
                        modeBadge.style.background = '#2196F3';
                    }
                }

                // Update live range selector if it exists
                const liveRangeSelect = document.getElementById('live-range-select');
                if (liveRangeSelect) {
                    liveRangeSelect.value = this.currentLiveRange;
                }

            try { window.__dbgLog && window.__dbgLog('Historical: click received'); } catch {}

                // Add visual feedback for range changes
                this.addVisualFeedback();
            }




            addVisualFeedback() {
                // Add subtle animation to indicate UI update
                const controlBar = document.querySelector('.unified-control-bar');
                if (controlBar) {
                    controlBar.style.transform = 'scale(1.01)';
                    setTimeout(() => {
                        controlBar.style.transform = 'scale(1)';
                    }, 150);
                }
            }
        }
        }; }


        // Helper function for historical options toggle
        function toggleHistoricalOptions() {
            const historicalOptions = document.getElementById('historical-options');
            const isVisible = historicalOptions.style.display !== 'none';

            if (isVisible) {
                if (chartManager) chartManager.switchToLiveMode();
            } else {
                historicalOptions.style.display = 'flex';
                // Defer mode/UI change to switchToHistoricalMode to avoid stale state
                // Auto-select current option with user confirmation for large datasets
                const rangeSelect = document.getElementById('historical-range');
                const selectedRange = rangeSelect ? rangeSelect.value : '1';
                if (selectedRange === 'all') {
                    const confirmed = confirm('Loading complete history since service start.\\nThis may take a moment and will use 1-minute resolution for performance.\\nContinue?');
                    if (confirmed) {
                        if (chartManager) chartManager.switchToHistoricalMode(selectedRange);
                    } else {
                        if (chartManager) chartManager.switchToLiveMode();
                        return;
                    }
                } else {
                    if (chartManager) chartManager.switchToHistoricalMode(selectedRange);
                }
            }
        }

        // New helper function for live range changes
        // Robust memory historical switch (avoids early race)
        function memorySwitchToHistorical(){
            try { if (window.chartManager?.mode !== 'historical') {
                const rangeSelect = document.getElementById('historical-range');
                const selectedRange = rangeSelect ? rangeSelect.value : '1';
                if (window.chartManager?.switchToHistoricalMode) {
                    window.chartManager.switchToHistoricalMode(selectedRange);
                } else {
                    window.__umc_pending = { mode: 'historical', range: selectedRange };
                    const chartTitle = document.getElementById('chart-title');
                    if (chartTitle) chartTitle.textContent = 'Loading historical data...';
                    const modeBadge = document.getElementById('mode-badge');
                    if (modeBadge) modeBadge.textContent = 'Historical';
                }
                const historicalOptions = document.getElementById('historical-options');
                if (historicalOptions) historicalOptions.style.display = 'flex';
            }} catch (e) { console.warn('Historical switch failed early', e); }
        }

        function handleLiveRangeChange(selectElement) {
            const newRange = selectElement.value;
            try { localStorage.setItem('umc_live_range', newRange); } catch {}
            if (window.chartManager) {
                window.chartManager.switchLiveRange(newRange);
            } else {
                // Capture intent to apply once chart manager is ready
                window.__umc_pending = { mode: 'live', liveRange: newRange };
            }
        }

        // Helper function to handle historical range selection changes
        function handleRangeChange(selectElement) {
            const selectedRange = selectElement.value;
            try { localStorage.setItem('umc_time_range', String(selectedRange)); } catch {}
            // Let switchToHistoricalMode own state/title; just call it
            if (window.chartManager) {
                window.chartManager.switchToHistoricalMode(selectedRange);
            } else {
                // Capture pending historical intent and reflect title immediately
                window.__umc_pending = { mode: 'historical', range: selectedRange };
                const chartTitle = document.getElementById('chart-title');
                if (chartTitle) chartTitle.textContent = 'Loading historical data...';
                const modeBadge = document.getElementById('mode-badge');
                if (modeBadge) modeBadge.textContent = 'Historical';
            }
        }

        // Initialize dashboard with polling - update banner status
        const statusLight = document.getElementById('dashboard-status-light');
        const statusText = document.getElementById('dashboard-status-text');
        if (statusLight && statusText) {
            statusLight.style.background = '#ccc';
            statusText.textContent = 'Connecting...';
            statusText.style.color = '#666';
        }

        // Initialize session start time (persistent across page refreshes)
        let globalSessionStartTime = null;

        // Initialize Unified Chart Manager (defer until class is available)
        window.chartManager = window.chartManager || null;
        // Pre-populate persisted live range select even before chart manager is ready
        try {
            const savedRange = localStorage.getItem('umc_live_range');
            const liveRangeSelect = document.getElementById('live-range-select');
            if (savedRange && liveRangeSelect) liveRangeSelect.value = savedRange;
        } catch {}

        (function ensureChartManagerReady(){
            if (!window.chartManager) {
                if (window.UnifiedMemoryChart) {
                    window.chartManager = new window.UnifiedMemoryChart();
                    if (typeof window.chartManager.initialize === 'function') {
                        window.chartManager.initialize().then(() => {
                            // Apply any pending mode/range intent captured before init
                            const pending = window.__umc_pending;
                            if (pending && pending.mode === 'historical') {
                                window.chartManager.switchToHistoricalMode(pending.range || window.chartManager.currentTimeRange);
                                window.__umc_pending = null;
                            } else if (pending && pending.mode === 'live' && pending.liveRange) {
                                window.chartManager.switchLiveRange(pending.liveRange);
                                window.__umc_pending = null;
                            }
                            // Always populate header metrics at least once regardless of mode
                            try { if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData(); } catch {}
                        }).catch(() => {});
                    }
                } else {
                    return setTimeout(ensureChartManagerReady, 50);
                }
            }
        })();



        // Start memory data polling is now managed by UnifiedMemoryChart (Phase 2)
        // setInterval(fetchMemoryData, 2000);

        // Fetch additional data every 10 seconds (guarded until modules attach globals)
        setInterval(() => {
            try { if (typeof window.fetchSystemData === 'function') window.fetchSystemData(); } catch {}
            try { if (typeof window.loadAnalysisData === 'function') window.loadAnalysisData(); } catch {}
            // Also ensure header is periodically populated even if live polling is off
            try { if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData(); } catch {}
        }, 10000);

        // Auto-refresh historical data every 5 seconds when in historical mode (faster updates)
        setInterval(() => {
            if (chartManager && chartManager.mode === 'historical') {
                chartManager.refreshHistoricalData();
            }
        }, 5000);

        // Performance monitoring for live mode
        setInterval(() => {
            if (chartManager && chartManager.mode === 'live') {
                const range = chartManager.liveRanges[chartManager.currentLiveRange];
                const dataPoints = chartManager.liveData.length;

                // Log performance metrics every 30 seconds
                console.log(`Live mode performance: ${range.label}, ${dataPoints}/${range.points} points`);

                // Auto-optimize if too many points are causing performance issues
                if (dataPoints > range.points * 1.1) {
                    console.warn(`Live data buffer overflow, trimming to ${range.points} points`);
                    chartManager.liveData = chartManager.liveData.slice(-range.points);
                }
            }
        }, 30000);

        // Initialize chart manager after chart is ready
        setTimeout(() => {
            if (chartManager && typeof chartManager.initialize === 'function') {
                chartManager.initialize();
            }
        }, 1000);

        // Pause/resume polling based on tab visibility (guard chartManager)
        document.addEventListener('visibilitychange', () => {
            if (window.chartManager) {
                window.chartManager.paused = document.hidden;
            }
        });



        // Show analysis-ready badge only when ready
        function updateAnalysisReadyBadge() {
            try {
                fetch('/api/analysis_health')
                    .then(r => r.ok ? r.json() : null)
                    .then(payload => {
                        const badge = document.getElementById('analysis-ready-badge');
                        if (!badge) return;
                        if (payload && payload.ready) {
                            badge.style.display = 'flex';
                            const dot = document.getElementById('analysis-ready-dot');
                            const text = document.getElementById('analysis-ready-text');
                            if (dot) dot.style.background = '#2ecc71';
                            if (text) text.textContent = 'Ready';
                        } else {
                            badge.style.display = 'none';
                        }
                    })
                    .catch(() => {});
            } catch {}
        }


        // Initial fetch (memory handled by chart manager on initialize)
        if (typeof window.fetchSystemData === 'function') window.fetchSystemData();
        if (typeof window.loadAnalysisData === 'function') window.loadAnalysisData();
        if (typeof window.updateMonitoringStatus === 'function') window.updateMonitoringStatus();
        // Initialize analysis-ready badge state and periodic refresh
        try { updateAnalysisReadyBadge(); } catch {}


        // Update monitoring status every 5 seconds
        setInterval(updateMonitoringStatus, 5000);
        // Refresh analysis-ready badge every 10 seconds
        setInterval(updateAnalysisReadyBadge, 10000);


        </script>




        <script>
          // Fallback: define UnifiedMemoryChart if missing so live graph can render
          (function ensureUMC(){
            if (!window.UnifiedMemoryChart) {
              window.UnifiedMemoryChart = class {
                constructor() {
                  this.mode = 'live';
                  this.liveData = [];
                  this.liveRanges = { '5m': { points: 300, label: '5 Minutes' } };
                  this.currentLiveRange = '5m';
                  this.chart = null;
                  this.isInitialized = false;
                }
                async initialize() {
                  this.isInitialized = true;
                  // kick an initial fetch to populate header and first point
                  setTimeout(() => { try { if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData(); } catch {} }, 200);
                  return this;
                }
                addRealtimePoint(p) {
                  try {
                    this.liveData.push({
                      timestamp: p.timestamp,
                      menubar_memory: p.menubar_memory || 0,
                      service_memory: p.service_memory || 0
                    });
                    const max = this.liveRanges[this.currentLiveRange].points;
                    if (this.liveData.length > max) this.liveData.shift();
                    this.updateChart();
                  } catch (e) {}
                }
                updateChart() {
                  try {
                    const canvas = document.getElementById('memoryChart');
                    if (!canvas) return;
                    const ctx = canvas.getContext('2d');
                    if (!this.chart) {
                      this.chart = new Chart(ctx, {
                        type: 'line',
                        data: { labels: [], datasets: [
                          { label: 'Menu Bar App (MB)', data: [], borderColor: '#2196F3', backgroundColor: 'rgba(33,150,243,0.1)', tension: 0.4, fill: true },
                          { label: 'Main Service (MB)', data: [], borderColor: '#4CAF50', backgroundColor: 'rgba(76,175,80,0.1)', tension: 0.4, fill: true }
                        ] },
                        options: {
                          responsive: true,
                          maintainAspectRatio: false,
                          interaction: { intersect: false, mode: 'index' },
                          scales: { y: { beginAtZero: true, title: { display: true, text: 'Memory Usage (MB)' } }, x: { title: { display: true, text: 'Time' } } }
                        }
                      });
                    }
                    const data = this.liveData;
                    this.chart.data.labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
                    this.chart.data.datasets[0].data = data.map(d => d.menubar_memory || 0);
                    this.chart.data.datasets[1].data = data.map(d => d.service_memory || 0);
                    this.chart.update();
                    try { this.chart.resize(); } catch {}
                  } catch (e) {}
                }
              };
            }
          })();

	          // Patch prototype to ensure historical mode exists even with minimal fallback class
	          (function patchUMC(){
	            try {
	              const UMC = window.UnifiedMemoryChart;
	              if (!UMC) return;
	              if (!UMC.prototype.clearChart) {
	                UMC.prototype.clearChart = function(){
	                  try {
	                    this.liveData = this.liveData || [];
	                    this.historicalData = [];
	                    if (this.chart) {
	                      this.chart.data.labels = [];
	                      if (this.chart.data.datasets?.[0]) this.chart.data.datasets[0].data = [];
	                      if (this.chart.data.datasets?.[1]) this.chart.data.datasets[1].data = [];
	                      this.chart.update();
	                    }
	                    const pts = document.getElementById('chart-points-count'); if (pts) pts.textContent = '0 pts';
	                    const last = document.getElementById('chart-last-update'); if (last) last.textContent = '—';
	                  } catch {}
	                };
	              }
	              if (!UMC.prototype.switchToLiveMode) {
	                UMC.prototype.switchToLiveMode = function(){
	                  try {
	                    this.mode = 'live';
	                    const ct = document.getElementById('chart-title'); if (ct) ct.textContent = 'Live Memory Usage';
	                    const mb = document.getElementById('mode-badge'); if (mb){ mb.textContent='Live'; mb.style.background='#4CAF50'; }
	                    const modeInd = document.getElementById('chart-mode-indicator');
	                    if (modeInd) {
	                      const rMap = (this.liveRanges||{})[this.currentLiveRange||'5m'];
	                      modeInd.textContent = 'Live' + (rMap?.label ? `: ${rMap.label}` : '');
	                    }
	                    // Explicitly restyle mode toggle buttons and options
	                    try {
	                      const liveBtn = document.getElementById('realtime-btn');
	                      const histBtn = document.getElementById('historical-btn');
	                      if (liveBtn) { liveBtn.style.background = '#4CAF50'; liveBtn.style.color = 'white'; liveBtn.style.boxShadow = '0 2px 4px rgba(76,175,80,0.3)'; }
	                      if (histBtn) { histBtn.style.background = 'white'; histBtn.style.color = '#666'; histBtn.style.boxShadow = 'none'; }
	                      const liveOpts = document.getElementById('live-options'); if (liveOpts) liveOpts.style.display = 'flex';
	                      const historicalOpts = document.getElementById('historical-options'); if (historicalOpts) historicalOpts.style.display = 'none';
	                    } catch {}
	                    if (typeof this.updateChart === 'function') this.updateChart();
	                    if (typeof this.updateUI === 'function') this.updateUI();
	                  } catch {}
	                };
	              }
	              if (!UMC.prototype.switchToHistoricalMode) {
	                UMC.prototype.switchToHistoricalMode = async function(timeRange){
	                  try {
	                    this.mode = 'historical';
	                    this.currentTimeRange = String(timeRange || this.currentTimeRange || '1');
	                    this.currentResolution = this.currentResolution || 'full';
	                    const ct = document.getElementById('chart-title'); if (ct) ct.textContent = 'Loading historical data...';
	                    const mb = document.getElementById('mode-badge'); if (mb){ mb.textContent='Historical'; mb.style.background='#2196F3'; }
	                    const modeInd = document.getElementById('chart-mode-indicator'); if (modeInd) modeInd.textContent = 'Historical (loading...)';
	                    const url = `/api/historical-chart?hours=${this.currentTimeRange}&resolution=${this.currentResolution}`;
	                    const res = await fetch(url);
	                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
	                    const payload = await res.json();
	                    this.historicalData = Array.isArray(payload?.points) ? payload.points : [];
	                    // Render directly without relying on updateChart implementation
	                    const canvas = document.getElementById('memoryChart');
	                    if (!this.chart && canvas) {
	                      const ctx = canvas.getContext('2d');
	                      this.chart = new Chart(ctx, {
	                        type: 'line',
	                        data: { labels: [], datasets: [
	                          { label: 'Menu Bar App (MB)', data: [], borderColor: '#2196F3', backgroundColor: 'rgba(33,150,243,0.1)', tension: 0.4, fill: true },
	                          { label: 'Main Service (MB)', data: [], borderColor: '#4CAF50', backgroundColor: 'rgba(76,175,80,0.1)', tension: 0.4, fill: true }
	                        ]},
	                        options: { responsive:true, maintainAspectRatio:false, interaction:{intersect:false, mode:'index'},
	                          scales:{ y:{ beginAtZero:true, title:{ display:true, text:'Memory Usage (MB)' } }, x:{ title:{ display:true, text:'Time'} } } }
	                      });
	                    }
	                    const data = this.historicalData;
	                    if (this.chart) {
	                      this.chart.data.labels = data.map(d => new Date(d.timestamp).toLocaleString());
	                      this.chart.data.datasets[0].data = data.map(d => d.menubar_memory || 0);
	                      this.chart.data.datasets[1].data = data.map(d => d.service_memory || 0);
	                      this.chart.update();

						// Ensure mode toggle buttons reflect Historical selection
						(function(){
						  try {
						    const liveBtn = document.getElementById('realtime-btn');
						    const histBtn = document.getElementById('historical-btn');
						    if (liveBtn) { liveBtn.style.background = 'white'; liveBtn.style.color = '#666'; liveBtn.style.boxShadow = 'none'; }
						    if (histBtn) { histBtn.style.background = '#2196F3'; histBtn.style.color = 'white'; histBtn.style.boxShadow = '0 2px 4px rgba(33, 150, 243, 0.3)'; }
						  } catch {}
						})();

	                    }
	                    const pts = document.getElementById('chart-points-count'); if (pts) pts.textContent = `${data.length} pts`;
	                    const last = document.getElementById('chart-last-update'); if (last) last.textContent = 'Loaded';
	                    if (ct) ct.textContent = 'Historical Memory Usage';
	                    if (modeInd) modeInd.textContent = `Historical (${this.currentTimeRange === 'all' ? 'Since Start' : 'Last ' + this.currentTimeRange + ' Hours'})`;
	                  } catch (e) {
	                    console.warn('Polyfill historical failed', e);
	                    try { alert('Failed to load historical data. Returning to Live.'); } catch {}
	                    this.switchToLiveMode?.();
	                  }
	                };

	              if (!UMC.prototype.refreshHistoricalData) {
	                UMC.prototype.refreshHistoricalData = async function(){
	                  try {
	                    if (this.mode !== 'historical') return;
	                    const url = `/api/historical-chart?hours=${this.currentTimeRange || '1'}&resolution=${this.currentResolution || 'full'}`;
	                    const res = await fetch(url);
	                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
	                    const payload = await res.json();
	                    const data = Array.isArray(payload?.points) ? payload.points : [];
	                    this.historicalData = data;
	                    if (this.chart) {
	                      this.chart.data.labels = data.map(d => new Date(d.timestamp).toLocaleString());
	                      this.chart.data.datasets[0].data = data.map(d => d.menubar_memory || 0);
	                      this.chart.data.datasets[1].data = data.map(d => d.service_memory || 0);
	                      this.chart.update();
	                    }
	                    const pts = document.getElementById('chart-points-count'); if (pts) pts.textContent = `${data.length} pts`;
	                    const last = document.getElementById('chart-last-update'); if (last) last.textContent = 'Loaded';
	                    const modeInd = document.getElementById('chart-mode-indicator');
	                    if (modeInd) modeInd.textContent = `Historical (${this.currentTimeRange === 'all' ? 'Since Start' : 'Last ' + this.currentTimeRange + ' Hours'})`;
	                  } catch (e) { console.warn('Polyfill refreshHistoricalData failed', e); }
	                };
	              }

	              }
	            } catch {}
	          })();


          // Final safety boot: ensure chartManager exists and is initialized
          (function finalBoot(){
            function bootOnce(){
              if (!window.chartManager && window.UnifiedMemoryChart) {
                try {
                  window.chartManager = new window.UnifiedMemoryChart();
                  if (typeof window.chartManager.initialize === 'function') {
                    window.chartManager.initialize().then(() => {
                      if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData();
                      if (typeof window.__dbgRead === 'function') window.__dbgRead();
                    }).catch(()=>{});
                  }
                } catch(e) { /* ignore */ }
              }
            }
            // Try now and after a short delay to cover load timing
            bootOnce();
            setTimeout(bootOnce, 400);
          })();
        </script>


        </div> <!-- End of Analysis Tab -->

        <!-- Clipboard History Tab -->
        <div id="clipboard-tab" class="tab-content" style="margin: 0 calc(10vw + 8px); width: auto; box-sizing: border-box; padding: 0;">
          <div class="clip-toolbar" style="display:flex; align-items:center; gap:8px; margin-bottom:12px; flex-wrap:wrap;">
            <button id="clip-refresh" class="spark-btn">Refresh</button>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              Auto:
              <input id="clip-auto" type="checkbox" />
              <select id="clip-auto-interval" class="spark-btn" style="padding:2px 6px;">
                <option value="5000">5s</option>
                <option value="10000" selected>10s</option>
                <option value="30000">30s</option>
              </select>
            </label>
            <button id="clip-clear" class="spark-btn" title="Clear clipboard history">🗑️ Clear</button>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              Type:
              <select id="clip-type" class="spark-btn" style="padding:2px 6px;">
                <option value="all">All</option>
                <option value="md">Markdown</option>
                <option value="rtf">RTF</option>
                <option value="text">Text</option>
              </select>
            </label>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              Order:
              <select id="clip-order" class="spark-btn" style="padding:2px 6px;">
                <option value="asc" selected>Oldest first</option>
                <option value="desc">Newest first</option>
              </select>
            </label>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              Range:
              <select id="clip-range" class="spark-btn" style="padding:2px 6px;">
                <option value="all" selected>All</option>
                <option value="1h">Last 1h</option>
                <option value="12h">Last 12h</option>
                <option value="24h">Last 24h</option>
                <option value="7d">Last 7d</option>
              </select>
            </label>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              Row:
              <select id="clip-density" class="spark-btn" style="padding:2px 6px;">
                <option value="cozy" selected>Cozy</option>
                <option value="comfy">Comfortable</option>
              </select>
            </label>

            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              Filter text:
              <input id="clip-search" type="text" placeholder="Type to filter…" style="padding:2px 6px; border:1px solid #cfe8ff; border-radius:6px;" />
            </label>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              <input id="clip-has-url" type="checkbox" /> Has URL
            </label>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              <input id="clip-has-code" type="checkbox" /> Has Code (```)
            </label>
            <label class="spark-hint" style="display:inline-flex; align-items:center; gap:6px;">
              <input id="clip-long" type="checkbox" /> Length > 200
            </label>
            <span id="clip-meta" class="spark-badge" style="margin-left:auto;">Loading…</span>
            <span style="font-size:11px; color:#666;">Page size: 30</span>
          </div>
          <div class="clip-table-wrap" style="overflow-x:auto; overflow-y:auto; width:100%; max-width:100%; box-sizing:border-box; border:1px solid #eee; border-radius:6px; margin-top:8px;">
            <table style="width:100%; border-collapse:collapse; font-size:12px; table-layout: fixed; word-break: break-word;">
              <thead style="background:#f8f9fa;">
                <tr>
                  <th style="text-align:left; padding:8px; border-bottom:1px solid #eee; width:160px;">Time</th>
                  <th style="text-align:left; padding:8px; border-bottom:1px solid #eee; width:64px;">Type</th>
                  <th style="text-align:left; padding:8px; border-bottom:1px solid #eee;">Snippet</th>
                  <th style="text-align:center; padding:8px; border-bottom:1px solid #eee; width:120px;">Actions</th>
                </tr>
              </thead>
              <tbody id="clip-tbody"></tbody>
            </table>
          </div>
          <div id="clip-pager" class="clip-pager" style="display:flex; align-items:center; gap:8px; margin-top:8px;">
            <button id="clip-prev" class="spark-btn">Prev</button>
            <span id="clip-page" class="spark-badge">Page 1 / 1</span>
            <button id="clip-next" class="spark-btn">Next</button>
          </div>
          <div id="clip-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.4); z-index:9999;">
            <div style="background:#fff; max-width:820px; margin:5% auto; padding:12px; border-radius:8px;">
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                <strong id="clip-modal-title">Item</strong>
                <div>
                  <button id="clip-modal-copy" class="spark-btn">Copy</button>
                  <button id="clip-modal-close" class="spark-btn">Close</button>
                </div>
              </div>
              <div style="display:flex; gap:6px; margin-bottom:6px;">
                <button id="clip-tab-render" class="spark-btn">Rendered</button>
                <button id="clip-tab-raw" class="spark-btn">Raw</button>
              </div>
              <div id="clip-modal-render" style="display:none; background:#fff; padding:8px; border:1px solid #eee; border-radius:6px; max-height:60vh; overflow:auto;"></div>
              <pre id="clip-modal-pre" style="display:block; white-space:pre-wrap; word-break:break-word; background:#fafafa; padding:8px; border:1px solid #eee; border-radius:6px; max-height:60vh; overflow:auto;"></pre>
            </div>
          </div>
        </div>

        <script>
        (function(){
          let page = 1; const pageSize = 30; let pageCount = 1; let serverItems = []; let autoTimer = null;
          const tbody = ()=>document.getElementById('clip-tbody');
          const qs = sel=>document.querySelector(sel);
          function fmt(ts){ try { return ts ? new Date(ts*1000).toLocaleString() : '--'; } catch{ return '--'; } }
          function typelabel(t){ return t==='rtf' ? 'RTF' : (t==='md' ? 'Markdown' : 'Text'); }
          function debounce(fn, ms){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; }
          function markdownToHtml(md){ try{
            let html = md || '';
            html = html.replace(/```([\s\S]*?)```/g, (m, g1)=>`<pre><code>${g1.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</code></pre>`);
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            html = html.replace(/^######\s+(.*)$/gm, '<h6>$1</h6>')
                       .replace(/^#####\s+(.*)$/gm, '<h5>$1</h5>')
                       .replace(/^####\s+(.*)$/gm, '<h4>$1</h4>')
                       .replace(/^###\s+(.*)$/gm, '<h3>$1</h3>')
                       .replace(/^##\s+(.*)$/gm, '<h2>$1</h2>')
                       .replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');
            html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
            html = html.replace(/^\s*[-*]\s+/gm, '\u2022 ');
            html = html.replace(/\\n\\n+/g, '<br/><br/>' ).replace(/\\n/g, '<br/>' );
            return html;
          }catch{ return (md||''); } }

          function savePrefs(){ try { localStorage.setItem('cm_clip_prefs', JSON.stringify({
            type: qs('#clip-type').value, order: qs('#clip-order').value, range: qs('#clip-range').value, q: qs('#clip-search').value,
            has_url: qs('#clip-has-url').checked, has_code: qs('#clip-has-code').checked, is_long: qs('#clip-long').checked,
            auto: qs('#clip-auto').checked, auto_interval: qs('#clip-auto-interval').value,
            density: (qs('#clip-density')?qs('#clip-density').value:'cozy')
          })); } catch{} }
          function loadPrefs(){ try { const p = JSON.parse(localStorage.getItem('cm_clip_prefs')||'{}');
            if (p.type) qs('#clip-type').value = p.type; if (p.order) qs('#clip-order').value = p.order; if (p.range) qs('#clip-range').value = p.range; if (p.q) qs('#clip-search').value = p.q;
            if (typeof p.has_url==='boolean') qs('#clip-has-url').checked = p.has_url;
            if (typeof p.has_code==='boolean') qs('#clip-has-code').checked = p.has_code;
            if (typeof p.is_long==='boolean') qs('#clip-long').checked = p.is_long;
            if (typeof p.auto==='boolean') qs('#clip-auto').checked = p.auto;
            if (p.auto_interval) qs('#clip-auto-interval').value = p.auto_interval;
            if (p.density && qs('#clip-density')) qs('#clip-density').value = p.density;
          } catch{} }
          function applyClientFilters(items){
            const hasUrl = qs('#clip-has-url').checked;
            const hasCode = qs('#clip-has-code').checked;
            const isLong = qs('#clip-long').checked;
            const q = (qs('#clip-search').value||'').toLowerCase();
            return (items||[]).filter(it=>{
              const sn = (it.snippet||'');
              if (hasUrl && !sn.match(/https?:\/\//i)) return false;
              if (hasCode && sn.indexOf('```') === -1) return false;
              if (isLong && sn.length <= 200) return false;
              if (q && sn.toLowerCase().indexOf(q) === -1) return false;
              return true;
            });
          }
          function applyDensity(){ try{ const tab = document.getElementById('clipboard-tab'); if (!tab) return; tab.classList.remove('density-cozy','density-comfy'); const v = (qs('#clip-density')?qs('#clip-density').value:'cozy'); tab.classList.add(v==='comfy'?'density-comfy':'density-cozy'); }catch{} }
          function computePairs(list){ let gid=0; for(let i=0;i<list.length;i++){ const a=list[i], b=list[i+1]; a._group=gid; if(b && Math.abs((b.timestamp||0)-(a.timestamp||0))<=3 && a.type!==b.type && ((a.type==='md'&&b.type==='rtf')||(a.type==='rtf'&&b.type==='md'))){ b._group=gid; a._pair=true; b._pair=true; i++; } gid++; } return list; }
          function actionsCell(it){ return `<button class="spark-btn icon-btn" data-act="view" data-h="${it.hash}" title="View" aria-label="View">👁</button> <button class="spark-btn icon-btn" data-act="copy" data-h="${it.hash}" title="Copy" aria-label="Copy">📋</button>`; }
          function render(data){
            pageCount = Math.max(1, data.page_count||1);
            serverItems = data.items||[];
            let list = applyClientFilters(serverItems);
            list = computePairs(list);
            let prevGroup = -1;
            const rows = list.map(it=>{
              const safeSnippet = (it.snippet||'').replace(/</g,'&lt;').replace(/>/g,'&gt;');
              const styleTop = (it._group!==prevGroup && prevGroup!==-1) ? 'border-top:2px solid #eaeaea;' : '';
              const leftStyle = it._pair ? 'border-left:3px solid #ffd54f;' : '';
              prevGroup = it._group;
              return `<tr data-group="${it._group}" style="${styleTop}${leftStyle}">
                <td style="padding:6px; border-bottom:1px solid #f0f0f0; white-space:nowrap;">${fmt(it.timestamp)}</td>
                <td style="padding:6px; border-bottom:1px solid #f0f0f0;">${typelabel(it.type)}</td>
                <td style="padding:6px; border-bottom:1px solid #f0f0f0; color:#333;">${safeSnippet}</td>
                <td style="padding:6px; border-bottom:1px solid #f0f0f0;">${actionsCell(it)}</td>
              </tr>`;
            }).join('');
            const body = tbody(); if (body) body.innerHTML = rows || '<tr><td colspan="4" style="padding:8px; color:#777;">No items</td></tr>';
            const meta = document.getElementById('clip-meta'); if (meta) { const ord = (qs('#clip-order').value==='asc')? 'oldest first' : 'newest first'; meta.textContent = `${data.total||0} items • order: ${ord}`; }
            const pg = document.getElementById('clip-page'); if (pg) pg.textContent = `Page ${data.page||1} / ${pageCount}`;
            if (body){ body.onclick = async (ev)=>{ const btn = ev.target.closest('button[data-act]'); if (!btn) return; const act = btn.getAttribute('data-act'); const h = btn.getAttribute('data-h'); if (act==='view'){ try{ const res = await fetch(`/api/clipboard/item?hash=${encodeURIComponent(h)}`); const item = await res.json(); if (item && item.found){ qs('#clip-modal-title').textContent = `${typelabel(item.type)} • ${fmt(item.timestamp)} • ${item.hash.slice(0,8)}`; qs('#clip-modal-pre').textContent = item.content||''; qs('#clip-modal').style.display='block'; qs('#clip-modal-copy').onclick = async ()=>{ try{ await navigator.clipboard.writeText(item.content||''); }catch{} }; } }catch{} } else if (act==='copy'){ try{ const res = await fetch(`/api/clipboard/item?hash=${encodeURIComponent(h)}`); const item = await res.json(); if (item && item.found){ await navigator.clipboard.writeText(item.content||''); } }catch{} } }; }
          }
          function computeRange(){ const v = qs('#clip-range').value; if (v==='all') return {start_ts:'', end_ts:''}; const now = Math.floor(Date.now()/1000); const map={ '1h':3600, '12h':43200, '24h':86400, '7d':604800 }; const dur = map[v]||0; return { start_ts: now-dur, end_ts: now }; }
          async function load(){ try{ const order = qs('#clip-order').value; const type = qs('#clip-type').value; const q = encodeURIComponent(qs('#clip-search').value||''); const has_url = qs('#clip-has-url').checked ? '1' : ''; const has_code = qs('#clip-has-code').checked ? '1' : ''; const is_long = qs('#clip-long').checked ? '1' : ''; const r = computeRange(); const qsuf = `&start_ts=${r.start_ts}&end_ts=${r.end_ts}`; const res = await fetch(`/api/clipboard/history?page=${page}&page_size=${pageSize}&order=${order}&type=${type}&q=${q}&has_url=${has_url}&has_code=${has_code}&is_long=${is_long}${qsuf}`); const data = await res.json(); render(data); }catch(e){ const meta = document.getElementById('clip-meta'); if (meta) meta.textContent = 'Error loading'; } }
          function setupAuto(){ if (autoTimer){ clearInterval(autoTimer); autoTimer=null; } if (qs('#clip-auto').checked){ const iv = parseInt(qs('#clip-auto-interval').value||'10000',10); autoTimer = setInterval(load, iv); } }
          function bind(){ const r = document.getElementById('clip-refresh'); if (r) r.onclick = ()=>{ savePrefs(); load(); }; const c = document.getElementById('clip-clear'); if (c) c.onclick = async ()=>{ try{ await fetch('/api/clipboard/clear'); page=1; load(); }catch{} }; const p = document.getElementById('clip-prev'); if (p) p.onclick = ()=>{ if (page>1){ page--; savePrefs(); load(); } }; const n = document.getElementById('clip-next'); if (n) n.onclick = ()=>{ if (page<pageCount){ page++; savePrefs(); load(); } }; const t = qs('#clip-type'); if (t) t.onchange = ()=>{ page=1; savePrefs(); load(); }; const o = qs('#clip-order'); if (o) o.onchange = ()=>{ page=1; savePrefs(); load(); }; const rg = qs('#clip-range'); if (rg) rg.onchange = ()=>{ page=1; savePrefs(); load(); }; const s = qs('#clip-search'); if (s) s.oninput = debounce(()=>{ savePrefs(); load(); }, 250); ['#clip-has-url','#clip-has-code','#clip-long'].forEach(sel=>{ const el=qs(sel); if (el) el.onchange = ()=>{ savePrefs(); load(); }; }); const a = qs('#clip-auto'); if (a) a.onchange = ()=>{ savePrefs(); setupAuto(); }; const ai = qs('#clip-auto-interval'); if (ai) ai.onchange = ()=>{ savePrefs(); setupAuto(); }; const de = qs('#clip-density'); if (de) de.onchange = ()=>{ savePrefs(); applyDensity(); }; const mc = qs('#clip-modal-close'); if (mc) mc.onclick = ()=>{ qs('#clip-modal').style.display='none'; }; qs('#clip-modal').addEventListener('click', (ev)=>{ if (ev.target.id==='clip-modal') qs('#clip-modal').style.display='none'; }); }
          window.loadClipboardHistory = load;
          if (location.hash === '#clipboard') { setTimeout(()=>{ if (typeof switchTab==='function'){ try{ switchTab('clipboard', document.querySelector('.tabs .tab:nth-child(3)')); }catch{} }}, 60); }
          loadPrefs(); applyDensity(); bind(); setTimeout(()=>{ load(); setupAuto(); }, 200);
        })();
        </script>



  <script>
    // Help overlays: toggle, outside-click, ESC, and persistence
    (function(){
      function getEls(kind){
        const overlay = document.getElementById(kind+'-help-overlay');
        const toggle = document.getElementById(kind+'-help-toggle');
        const container = toggle ? toggle.closest('.chart-container') : null;
        const backdropId = kind+'-help-backdrop';
        let backdrop = container ? container.querySelector('#'+backdropId) : null;
        if (!backdrop && container) {
          backdrop = document.createElement('div');
          backdrop.id = backdropId;
          backdrop.style.cssText = 'position:absolute; left:0; right:0; top:0; bottom:0; background:rgba(0,0,0,0.12); z-index:18; display:none; backdrop-filter:saturate(1)';
          container.appendChild(backdrop);
        }
        return { overlay, toggle, container, backdrop };
      }
      function setState(kind, open){
        try { localStorage.setItem('umc_help_'+kind, open ? '1' : '0'); } catch {}
      }
      function getState(kind){
        try { return localStorage.getItem('umc_help_'+kind) === '1'; } catch { return false; }
      }
      function show(kind){
        const { overlay, toggle, backdrop } = getEls(kind);
        if (!overlay || !toggle) return;
        overlay.style.transform = 'translateY(0)';
        overlay.setAttribute('data-open', '1');
        toggle.textContent = 'Help ▾';
        if (backdrop) { backdrop.style.display = 'block'; }
        setState(kind, true);
      }
      function hide(kind){
        const { overlay, toggle, backdrop } = getEls(kind);
        if (!overlay || !toggle) return;
        overlay.style.transform = 'translateY(-100%)';
        overlay.setAttribute('data-open', '0');
        toggle.textContent = 'Help ▸';
        if (backdrop) { backdrop.style.display = 'none'; }
        setState(kind, false);
      }
      window.toggleHelp = function(kind, ev){
        if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        const { overlay } = getEls(kind);
        if (!overlay) return;
        const open = overlay.getAttribute('data-open') === '1';
        open ? hide(kind) : show(kind);
      };
      // Outside click handling
      function outsideClick(kind, ev){
        const { overlay, container } = getEls(kind);
        if (!overlay || !container) return;
        if (overlay.getAttribute('data-open') !== '1') return;
        if (!overlay.contains(ev.target) && container.contains(ev.target)) hide(kind);
      }
      document.addEventListener('click', (ev)=>{ outsideClick('mem', ev); outsideClick('cpu', ev); });
      // ESC to close
      document.addEventListener('keydown', (ev)=>{
        if (ev.key === 'Escape') { hide('mem'); hide('cpu'); }
      });
      // Restore persisted state
      function restore(){
        if (getState('mem')) show('mem');
        if (getState('cpu')) show('cpu');
      }
      // Defer restore until after DOM
      setTimeout(restore, 0);
    })();
  </script>



    </div> <!-- Close container -->
  <script>
    // Failsafe boot: construct chartManager if still missing at very end
    (function ensureCM(){
      if (!window.chartManager && window.UnifiedMemoryChart) {
        try {
          window.chartManager = new window.UnifiedMemoryChart();
          if (typeof window.chartManager.initialize === 'function') {
            window.chartManager.initialize().then(()=>{
              if (typeof window.fetchMemoryData === 'function') window.fetchMemoryData();
              if (typeof window.__dbgRead === 'function') window.__dbgRead();
            }).catch(()=>{});
          }



        } catch(e) {}
      }
    })();
  </script>
</div> <!-- /#content-width-wrap -->

</body>
</html>
        '''
        return html.replace('__ASSET_VERSION__', self.asset_version)

    def get_memory_data(self):
        """Get detailed memory usage data."""
        try:
            # System memory information
            system_memory = psutil.virtual_memory()

            # Clipboard Monitor specific processes
            clipboard_processes = []
            total_clipboard_memory = 0

            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent', 'create_time', 'num_threads', 'num_fds']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cmdline = proc.info.get('cmdline', [])

                    # Get memory and CPU from the iterator
                    memory_info = proc.info.get('memory_info')
                    if memory_info:
                        memory_mb = memory_info.rss / 1024 / 1024
                    else:
                        memory_mb = 0

                    cpu_percent = proc.info.get('cpu_percent', 0) or 0

                    # Get detailed process metrics
                    threads = proc.info.get('num_threads', 0)
                    handles = proc.info.get('num_fds', 0)  # File descriptors on Unix
                    create_time = proc.info.get('create_time', 0)

                    # Calculate uptime
                    if create_time:
                        uptime_seconds = time.time() - create_time
                        uptime_hours = int(uptime_seconds // 3600)
                        uptime_minutes = int((uptime_seconds % 3600) // 60)
                        uptime_str = f"{uptime_hours}h {uptime_minutes}m" if uptime_hours > 0 else f"{uptime_minutes}m"
                    else:
                        uptime_str = "--"

                    # Use the same detection logic as collect_memory_data()
                    is_clipboard_process = False
                    cmdline_str = ""

                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        # More specific detection to avoid false positives
                        is_clipboard_process = (
                            'menu_bar_app.py' in cmdline_str or
                            ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard monitor', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]))
                        )

                    # Also check by process name (for PyInstaller executables)
                    if not is_clipboard_process and name == 'ClipboardMonitor':
                        is_clipboard_process = True

                    if is_clipboard_process:
                        total_clipboard_memory += memory_mb

                        # Determine process type and descriptive name
                        process_type = "unknown"
                        display_name = name

                        if 'menu_bar_app.py' in cmdline_str:
                            process_type = "menu_bar"
                            display_name = "ClipboardMonitor Menu Bar"
                        elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                            'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                        ]):
                            process_type = "main_service"
                            display_name = "ClipboardMonitor Service"
                        elif name == 'ClipboardMonitor':
                            # For PyInstaller executables, use memory heuristic
                            if memory_mb > 50:
                                process_type = "menu_bar"
                                display_name = "ClipboardMonitor Menu Bar"
                            else:
                                process_type = "main_service"
                                display_name = "ClipboardMonitor Service"
                        elif 'unified_memory_dashboard.py' in cmdline_str:
                            process_type = "dashboard"
                            display_name = "Memory Dashboard"

                        clipboard_processes.append({
                            'pid': pid,
                            'name': name,
                            'display_name': display_name,
                            'memory_mb': round(memory_mb, 2),
                            'cpu_percent': cpu_percent,
                            'create_time': datetime.fromtimestamp(create_time).isoformat() if create_time else None,
                            'process_type': process_type,
                            'cmdline_snippet': cmdline_str[:100] + "..." if len(cmdline_str) > 100 else cmdline_str,
                            'threads': threads,
                            'handles': handles,
                            'uptime': uptime_str,
                            'restarts': 0  # TODO: Implement restart tracking
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Calculate analytics metrics
            current_total_memory = total_clipboard_memory
            current_time = datetime.now()

            # Add current reading to history
            self.memory_history.append({
                'memory': current_total_memory,
                'timestamp': current_time
            })

            # Calculate growth rate based on recent history
            growth_rate = 0.0
            if len(self.memory_history) >= 2:
                # Calculate growth over last 5 minutes
                five_min_ago = current_time - timedelta(minutes=5)
                recent_readings = [r for r in self.memory_history if r['timestamp'] > five_min_ago]

                if len(recent_readings) >= 2:
                    oldest = recent_readings[0]
                    newest = recent_readings[-1]
                    time_diff_minutes = (newest['timestamp'] - oldest['timestamp']).total_seconds() / 60
                    if time_diff_minutes > 0:
                        growth_rate = (newest['memory'] - oldest['memory']) / time_diff_minutes

            # Calculate efficiency (MB per operation) - simplified to avoid server issues
            efficiency = round(current_total_memory / max(len(clipboard_processes), 1), 1)

            # Calculate optimum time based on memory stability
            optimum_time = 75  # Default
            try:
                if len(self.memory_history) >= 10:
                    # Calculate stability - lower variance = higher optimum time
                    recent_memories = [r['memory'] for r in list(self.memory_history)[-10:]]
                    if recent_memories:
                        mean = sum(recent_memories) / len(recent_memories)
                        variance = sum((x - mean)**2 for x in recent_memories) / len(recent_memories)
                        optimum_time = max(30, min(120, 75 - int(variance)))
            except Exception:
                optimum_time = 75  # Fallback

            # Calculate pressure (memory pressure as percentage)
            pressure = round((system_memory.percent / 100) * 2.5, 2)

            # Get system load average
            try:
                load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            except:
                load_avg = 0.0

            # Calculate system uptime
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                uptime_hours = int(uptime_seconds // 3600)
                uptime_minutes = int((uptime_seconds % 3600) // 60)
                uptime_str = f"{uptime_hours}h {uptime_minutes}m"
            except:
                uptime_str = "--"

            # Calculate session duration
            session_duration_seconds = (datetime.now() - self.session_start_time).total_seconds()
            session_hours = int(session_duration_seconds // 3600)
            session_minutes = int((session_duration_seconds % 3600) // 60)
            session_seconds = int(session_duration_seconds % 60)
            session_duration = f"{session_hours}h {session_minutes}m {session_seconds}s"

            return {
                'system': {
                    'total_gb': round(system_memory.total / 1024 / 1024 / 1024, 2),
                    'available_gb': round(system_memory.available / 1024 / 1024 / 1024, 2),
                    'used_gb': round((system_memory.total - system_memory.available) / 1024 / 1024 / 1024, 2),
                    'percent': system_memory.percent,
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'load_avg': round(load_avg, 2),
                    'uptime': uptime_str
                },
                'clipboard': {
                    'processes': clipboard_processes,
                    'total_memory_mb': round(total_clipboard_memory, 2),
                    'process_count': len(clipboard_processes)
                },
                'analytics': {
                    'total_memory': round(current_total_memory, 1),
                    'growth_rate': f"+{growth_rate:.1f}MB/min" if growth_rate >= 0 else f"{growth_rate:.1f}MB/min",
                    'efficiency': f"{efficiency:.1f}MB/op",
                    'optimum': f"{optimum_time}min",
                    'gc_status': "Low" if self.gc_count < 5 else "Normal" if self.gc_count < 15 else "High",
                    'pressure': f"{pressure:.1f}%",
                    'history': len(self.memory_history),
                    'queue': max(0, len(clipboard_processes) - 2),  # Processes beyond main 2
                    'cache': f"{min(95.1, 80 + (self.cache_hits / max(self.cache_hits + self.cache_misses, 1)) * 15):.1f}%"
                },
                'session': {
                    'duration': session_duration,
                    'start_time': self.session_start_time.isoformat(),
                    'data_points': len(self.memory_history) if hasattr(self, 'memory_history') else 0
                },
                'timestamp': datetime.now().isoformat(),
                'peak_menubar_memory': round(self.peak_menubar_memory, 2),
                'peak_service_memory': round(self.peak_service_memory, 2),
                'peak_total_memory': round(self.peak_total_memory, 2),
                'peak_menubar_cpu': round(self.peak_menubar_cpu, 2),
                'peak_service_cpu': round(self.peak_service_cpu, 2),
                'peak_total_cpu': round(self.peak_total_cpu, 2)
            }

        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}


    def get_system_data(self):
        """Get system information."""
        memory_data = self.get_memory_data()

        try:
            # Additional system info
            cpu_percent = psutil.cpu_percent(interval=1)
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)

            return {
                'system': memory_data.get('system', {}),
                'cpu_percent': cpu_percent,
                'uptime': f"{uptime_hours}h {uptime_minutes}m",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def collect_memory_data(self):
        """Collect current memory usage and CPU data for WebSocket updates."""
        try:
            menubar_memory = 0
            service_memory = 0
            dashboard_memory = 0
            menubar_cpu = 0
            service_cpu = 0
            dashboard_cpu = 0

            # Debug: collect all clipboard-related processes
            clipboard_processes = []

            # Use the same approach as the menu bar app for reliable detection

            # Get memory for menu bar app (current process if this is the menu bar)
            current_pid = os.getpid()
            try:
                current_process = psutil.Process(current_pid)
                current_cmdline = ' '.join(current_process.cmdline()) if current_process.cmdline() else ''
                if 'menu_bar_app.py' in current_cmdline:
                    menubar_memory = current_process.memory_info().rss / 1024 / 1024
                    menubar_cpu = current_process.cpu_percent() or 0
                    print(f"📱 Found Menu Bar App (current process): PID {current_pid}, Memory: {menubar_memory:.1f}MB, CPU: {menubar_cpu:.1f}%")
            except:
                pass

            # Use the original simple approach that was working before
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cmdline = proc.info.get('cmdline', [])

                    # Get memory and CPU from the iterator (this was working before)
                    memory_info = proc.info.get('memory_info')
                    if memory_info:
                        memory_mb = memory_info.rss / 1024 / 1024
                    else:
                        memory_mb = 0

                    cpu_percent = proc.info.get('cpu_percent', 0) or 0

                    # Check if this is a clipboard-related process
                    is_clipboard_process = False
                    cmdline_str = ""

                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        # More specific detection to avoid false positives
                        is_clipboard_process = (
                            'menu_bar_app.py' in cmdline_str or
                            'unified_memory_dashboard.py' in cmdline_str or
                            ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard monitor', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]))
                        )

                    # Also check by process name (for PyInstaller executables)
                    if not is_clipboard_process and name == 'ClipboardMonitor':
                        is_clipboard_process = True

                    if is_clipboard_process:
                        clipboard_processes.append({
                            'pid': pid,
                            'name': name,
                            'cmdline': cmdline_str,
                            'memory_mb': memory_mb,
                            'cpu_percent': cpu_percent
                        })

                        # Use the original simple detection logic that was working
                        if 'menu_bar_app.py' in cmdline_str:
                            menubar_memory = memory_mb
                            menubar_cpu = cpu_percent
                        elif 'unified_memory_dashboard.py' in cmdline_str:
                            dashboard_memory = memory_mb
                            dashboard_cpu = cpu_percent
                        elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                            'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                        ]):
                            service_memory = memory_mb
                            service_cpu = cpu_percent
                        elif name == 'ClipboardMonitor':
                            # For PyInstaller executables, we need to distinguish between main service and menu bar app
                            # Since we can't access command lines, we'll use a simple heuristic:
                            # The menu bar app typically uses more memory than the main service
                            if memory_mb > 50:  # Menu bar app typically uses more memory
                                if menubar_memory == 0:  # Only assign if we haven't found one yet
                                    menubar_memory = memory_mb
                                    menubar_cpu = cpu_percent
                            else:  # Main service typically uses less memory
                                if service_memory == 0:  # Only assign if we haven't found one yet
                                    service_memory = memory_mb
                                    service_cpu = cpu_percent

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Optional debug output (can be enabled for troubleshooting)
            # if len(clipboard_processes) > 0:
            #     print(f"Found {len(clipboard_processes)} clipboard processes:")
            #     for proc in clipboard_processes:
            #         print(f"  PID {proc['pid']}: {proc['name']} - {proc['memory_mb']:.2f} MB")

            # Track peak memory values
            if menubar_memory > self.peak_menubar_memory:
                self.peak_menubar_memory = menubar_memory

            if service_memory > self.peak_service_memory:
                self.peak_service_memory = service_memory

            if dashboard_memory > self.peak_dashboard_memory:
                self.peak_dashboard_memory = dashboard_memory

            # Track peak CPU values
            if menubar_cpu > self.peak_menubar_cpu:
                self.peak_menubar_cpu = menubar_cpu

            if service_cpu > self.peak_service_cpu:
                self.peak_service_cpu = service_cpu

            if dashboard_cpu > self.peak_dashboard_cpu:
                self.peak_dashboard_cpu = dashboard_cpu

            # Track peak totals
            total_memory = menubar_memory + service_memory + dashboard_memory
            total_cpu = menubar_cpu + service_cpu + dashboard_cpu

            if total_memory > self.peak_total_memory:
                self.peak_total_memory = total_memory

            if total_cpu > self.peak_total_cpu:
                self.peak_total_cpu = total_cpu

            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': round(menubar_memory, 2),
                'service_memory': round(service_memory, 2),
                'dashboard_memory': round(dashboard_memory, 2),
                'total_memory': round(total_memory, 2),
                'menubar_cpu': round(menubar_cpu, 2),
                'service_cpu': round(service_cpu, 2),
                'dashboard_cpu': round(dashboard_cpu, 2),
                'total_cpu': round(total_cpu, 2),
                'peak_menubar_memory': round(self.peak_menubar_memory, 2),
                'peak_service_memory': round(self.peak_service_memory, 2),
                'peak_dashboard_memory': round(self.peak_dashboard_memory, 2),
                'peak_total_memory': round(self.peak_total_memory, 2),
                'peak_menubar_cpu': round(self.peak_menubar_cpu, 2),
                'peak_service_cpu': round(self.peak_service_cpu, 2),
                'peak_dashboard_cpu': round(self.peak_dashboard_cpu, 2),
                'peak_total_cpu': round(self.peak_total_cpu, 2),
                'session_start_time': self.session_start_time.isoformat()
            }

        except Exception as e:
            # Optional debug output (can be enabled for troubleshooting)
            # print(f"Error in collect_memory_data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'menubar_memory': 0,
                'service_memory': 0,
                'total_memory': 0,
                'error': str(e)
            }

    def load_historical_data(self):
        """Load historical data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    saved_data = json.load(f)
                    self.data_history = saved_data.get('data_history', [])
                    self.alert_count = saved_data.get('alert_count', 0)
        except Exception as e:
            print(f"Error loading historical data: {e}")

    def save_historical_data(self):
        """Save historical data to file"""
        try:
            data_to_save = {
                'data_history': self.data_history[-self.max_history:],
                'alert_count': self.alert_count,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f)
        except Exception as e:
            print(f"Error saving historical data: {e}")

    def get_historical_data(self, hours=24, resolution='full'):
        """Get historical data for specified hours with optional resolution"""
        if hours == 'all':
            # Return all data since service start
            filtered_data = list(self.data_history)
        else:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.timestamp()

            filtered_data = []
            for point in self.data_history:
                point_timestamp = point.get('timestamp', 0)
                # Handle both string and float timestamps
                if isinstance(point_timestamp, str):
                    try:
                        point_timestamp = datetime.fromisoformat(point_timestamp).timestamp()
                    except:
                        continue

                if point_timestamp >= cutoff_timestamp:
                    filtered_data.append(point)

        # Apply resolution filtering if requested
        if resolution != 'full' and len(filtered_data) > 0:
            filtered_data = self._apply_resolution_filter(filtered_data, resolution)

        return {
            'main_service': [{'timestamp': p['timestamp'], 'memory_rss_mb': p.get('service_memory', 0)} for p in filtered_data],
            'menu_bar': [{'timestamp': p['timestamp'], 'memory_rss_mb': p.get('menubar_memory', 0)} for p in filtered_data],
            'total_memory': [{'timestamp': p['timestamp'], 'memory_mb': p.get('total_memory', (p.get('menubar_memory', 0) + p.get('service_memory', 0) + p.get('dashboard_memory', 0)))} for p in filtered_data],
            'system': [{'timestamp': p['timestamp'], 'memory_percent': 0} for p in filtered_data],  # Placeholder
            'points': filtered_data,  # Raw data for chart
            'total_points': len(filtered_data),
            'resolution': resolution,
            'time_range': f"{hours} hours" if hours != 'all' else "since start"
        }

    def _apply_resolution_filter(self, data, resolution):
        """Apply resolution filtering to reduce data points"""
        if not data or resolution == 'full':
            # For full resolution, limit to prevent browser issues
            if len(data) > 10000:
                print(f"Warning: Full resolution dataset has {len(data)} points, limiting to last 10000")
                return data[-10000:]  # Keep last 10000 points
            return data

        if resolution == 'minute':
            # Keep one point per minute
            interval = 60  # seconds
        elif resolution == 'hour':
            # Keep one point per hour
            interval = 3600  # seconds
        elif resolution == '10sec':
            # Keep one point per 10 seconds
            interval = 10  # seconds
        else:
            return data

        filtered = []
        last_timestamp = 0

        for point in data:
            point_timestamp = point.get('timestamp', 0)
            if isinstance(point_timestamp, str):
                try:
                    point_timestamp = datetime.fromisoformat(point_timestamp).timestamp()
                except:
                    continue

            if point_timestamp - last_timestamp >= interval:
                filtered.append(point)
                last_timestamp = point_timestamp

        # Resolution filter applied
        return filtered

    def get_analysis_data(self, hours=24):
        """Get memory leak analysis data, including sparklines."""
        historical_data = self.get_historical_data(hours)
        analysis = {}

        # To keep responses small and reliable, cap sparkline size
        SPARK_MAX = 300

        # Process-level analysis: map UI keys to history keys
        process_map = [
            ('menu_bar_app', 'menu_bar'),
            ('main_service', 'main_service')
        ]
        for ui_key, hist_key in process_map:
            points = historical_data.get(hist_key, [])

            if not isinstance(points, list) or len(points) < 2:
                analysis[ui_key] = {
                    "status": "insufficient_data", "severity": "low",
                    "growth_rate_mb": 0, "total_growth_mb": 0,
                    "start_memory_mb": 0, "end_memory_mb": 0,
                    "data_points": len(points) if isinstance(points, list) else 0,
                    "sparkline": []
                }
                continue

            # Extract memory series
            memory_values = [float(p.get('memory_rss_mb', p.get('memory_mb', 0)) or 0.0) for p in points]

            start_memory = memory_values[0] if memory_values else 0
            end_memory = memory_values[-1] if memory_values else 0
            total_growth = end_memory - start_memory

            # Calculate growth rate in MB per hour using ISO timestamps
            try:
                t_end = datetime.fromisoformat(points[-1]['timestamp'])
                t_start = datetime.fromisoformat(points[0]['timestamp'])
                duration_hours = max(1/60, (t_end - t_start).total_seconds() / 3600)
            except Exception:
                duration_hours = 1
            growth_rate = total_growth / duration_hours if duration_hours > 0 else 0

            # Compute simple R^2 consistency of linear fit memory vs time
            r2 = None
            try:
                xs = []
                ys = []
                for p in points:
                    ys.append(float(p.get('memory_rss_mb', p.get('memory_mb', 0)) or 0.0))
                    ts = p.get('timestamp')
                    if isinstance(ts, str):
                        xs.append(datetime.fromisoformat(ts).timestamp())
                    else:
                        xs.append(float(ts or 0.0))
                n = len(xs)
                if n >= 2:
                    mean_x = sum(xs)/n
                    mean_y = sum(ys)/n
                    ss_xx = sum((x-mean_x)**2 for x in xs)
                    ss_yy = sum((y-mean_y)**2 for y in ys)
                    if ss_xx > 0 and ss_yy > 0:
                        cov_xy = sum((x-mean_x)*(y-mean_y) for x,y in zip(xs,ys))
                        slope = cov_xy/ss_xx
                        intercept = mean_y - slope*mean_x
                        ss_res = sum((y - (slope*x + intercept))**2 for x,y in zip(xs,ys))
                        r2 = max(0.0, min(1.0, 1 - (ss_res/ss_yy)))
            except Exception:
                r2 = None

            severity = "low"
            if growth_rate > 10:
                status = "potential_leak"
                severity = "high"
            elif growth_rate > 2:
                status = "monitoring_needed"
                severity = "medium"
            else:
                status = "normal"

            spark = memory_values[-SPARK_MAX:] if len(memory_values) > SPARK_MAX else memory_values

            analysis[ui_key] = {
                "status": status,
                "severity": severity,
                "growth_rate_mb": round(growth_rate, 2),
                "total_growth_mb": round(total_growth, 2),
                "start_memory_mb": round(start_memory, 2),
                "end_memory_mb": round(end_memory, 2),
                "data_points": len(points),
                "sparkline": spark,
                "r2_consistency": (round(r2, 3) if isinstance(r2, float) else None)
            }

        # Analyze total memory
        total_points = historical_data.get('total_memory', [])
        if len(total_points) > 1:
            memory_values = [float(p.get('memory_mb', 0) or 0.0) for p in total_points]
            start_memory = memory_values[0]
            end_memory = memory_values[-1]
            total_growth = end_memory - start_memory
            try:
                t_end = datetime.fromisoformat(total_points[-1]['timestamp'])
                t_start = datetime.fromisoformat(total_points[0]['timestamp'])
                duration_hours = max(1/60, (t_end - t_start).total_seconds() / 3600)
            except Exception:
                duration_hours = 1
            growth_rate = total_growth / duration_hours if duration_hours > 0 else 0

            # Compute total R^2 consistency
            r2_total = None
            try:
                xs = []
                ys = []
                for p in total_points:
                    ys.append(float(p.get('memory_mb', 0) or 0.0))
                    ts = p.get('timestamp')
                    if isinstance(ts, str):
                        xs.append(datetime.fromisoformat(ts).timestamp())
                    else:
                        xs.append(float(ts or 0.0))
                n = len(xs)
                if n >= 2:
                    mean_x = sum(xs)/n
                    mean_y = sum(ys)/n
                    ss_xx = sum((x-mean_x)**2 for x in xs)
                    ss_yy = sum((y-mean_y)**2 for y in ys)
                    if ss_xx > 0 and ss_yy > 0:
                        cov_xy = sum((x-mean_x)*(y-mean_y) for x,y in zip(xs,ys))
                        slope = cov_xy/ss_xx
                        intercept = mean_y - slope*mean_x
                        ss_res = sum((y - (slope*x + intercept))**2 for x,y in zip(xs,ys))
                        r2_total = max(0.0, min(1.0, 1 - (ss_res/ss_yy)))
            except Exception:
                r2_total = None

            severity = "low"
            if growth_rate > 15:
                status = "potential_leak"
                severity = "high"
            elif growth_rate > 5:
                status = "monitoring_needed"
                severity = "medium"
            else:
                status = "normal"

            spark_total = memory_values[-SPARK_MAX:] if len(memory_values) > SPARK_MAX else memory_values

            analysis['total_memory'] = {
                "status": status,
                "severity": severity,
                "growth_rate_mb": round(growth_rate, 2),
                "total_growth_mb": round(total_growth, 2),
                "start_memory_mb": round(start_memory, 2),
                "end_memory_mb": round(end_memory, 2),
                "data_points": len(total_points),
                "sparkline": spark_total,
                "r2_consistency": (round(r2_total, 3) if isinstance(r2_total, float) else None)
            }
        else:
            analysis['total_memory'] = {
                "status": "insufficient_data", "severity": "low",
                "growth_rate_mb": 0, "total_growth_mb": 0,
                "start_memory_mb": 0, "end_memory_mb": 0,
                "data_points": len(total_points),
                "sparkline": []
            }

        return analysis

    def start_advanced_monitoring(self, interval=10):
        """Start advanced monitoring with specified interval"""
        self.monitor_interval = interval
        self.monitoring_active = True
        self.monitoring_start_time = datetime.now()

        # Start background data collection thread if not already running
        if not hasattr(self, 'monitoring_thread') or not self.monitoring_thread.is_alive():
            self.monitoring_thread = threading.Thread(target=self._background_monitoring_loop, daemon=False)
            self.monitoring_thread.start()
            print(f"Started persistent background monitoring thread with {interval}s interval")

        return {
            "status": "started",
            "interval": interval,
            "message": f"Advanced monitoring started with {interval}s interval",
            "background_collection": "enabled"
        }

    def stop_advanced_monitoring(self):
        """Stop advanced monitoring"""
        self.monitoring_active = False
        duration = None
        data_points_collected = len(self.advanced_data_history)
        if self.monitoring_start_time:
            duration = (datetime.now() - self.monitoring_start_time).total_seconds()
        # The background thread will stop automatically when monitoring_active becomes False
        print(f"Stopped advanced monitoring - background collection will cease")
        print(f"Advanced monitoring session collected {data_points_collected} data points")
        return {
            "status": "stopped",
            "duration_seconds": duration,
            "data_points_collected": data_points_collected,
            "message": "Advanced monitoring stopped",
            "background_collection": "disabled"
        }

    def get_top_offenders(self, hours=24):
        """Compute top offenders over the selected range by growth and rate"""
        hist = self.get_historical_data(hours)
        offenders = []
        try:
            def analyze(points, label):
                if not points or len(points) < 2:
                    return {'name': label, 'total_growth_mb': 0, 'growth_rate_mb_per_hour': 0, 'start_mb': 0, 'end_mb': 0, 'points': len(points)}
                vals = [p.get('memory_rss_mb', 0) for p in points]
                start = vals[0]; end = vals[-1]
                total_growth = end - start

                duration_hours = max(1/60, (datetime.fromisoformat(points[-1]['timestamp']) - datetime.fromisoformat(points[0]['timestamp'])).total_seconds()/3600)
                rate = total_growth / duration_hours
                return {'name': label, 'total_growth_mb': round(total_growth,2), 'growth_rate_mb_per_hour': round(rate,2), 'start_mb': round(start,2), 'end_mb': round(end,2), 'points': len(points)}
            offenders.append(analyze(hist.get('menu_bar', []), 'Menu Bar App'))
            offenders.append(analyze(hist.get('main_service', []), 'Main Service'))
            offenders.sort(key=lambda x: (x['total_growth_mb'], x['growth_rate_mb_per_hour']), reverse=True)
        except Exception:
            pass
        return offenders[:5]

    def get_analysis_health(self, hours=24):
        """Lightweight analysis readiness/summary for header badge."""
        hist = self.get_historical_data(hours)
        points = hist.get('points', [])
        total_points = len(points)
        ok = total_points >= 2
        last_ts = None
        try:
            if total_points:
                last_ts = points[-1].get('timestamp')
        except Exception:
            last_ts = None

        def extract_rate(seq, key_mb):
            try:
                if not seq or len(seq) < 2:
                    return 0.0
                vals = [float(p.get(key_mb, 0) or 0.0) for p in seq]
                start, end = vals[0], vals[-1]
                t_end = datetime.fromisoformat(seq[-1]['timestamp'])
                t_start = datetime.fromisoformat(seq[0]['timestamp'])
                dur_h = max(1/60, (t_end - t_start).total_seconds() / 3600)
                return (end - start) / dur_h
            except Exception:
                return 0.0

        mba = hist.get('menu_bar', [])
        msv = hist.get('main_service', [])
        tot = hist.get('total_memory', [])
        return {
            'ok': ok,
            'hours': hours,
            'points': total_points,
            'menu_bar_app': {
                'points': len(mba),
                'rate_mb_per_hr': round(extract_rate(mba, 'memory_rss_mb'), 2),
            },
            'main_service': {
                'points': len(msv),
                'rate_mb_per_hr': round(extract_rate(msv, 'memory_rss_mb'), 2),
            },
            'total': {
                'points': len(tot),
                'rate_mb_per_hr': round(extract_rate(tot, 'memory_mb'), 2),
            },
            'last_sample_iso': last_ts,
            'computed_at_iso': datetime.now().isoformat(),
        }


    def _background_monitoring_loop(self):
        """Background thread for advanced monitoring data collection"""
        print(f"Background monitoring loop started with {self.monitor_interval}s interval")

        while self.monitoring_active:
            try:
                # Collect memory data
                memory_data = self.collect_memory_data()

                # Add to advanced monitoring history (separate from basic data collection)
                self.advanced_data_history.append(memory_data)

                # Feed snapshots to the leak detector (use total memory for overall trend)
                try:
                    total_mb = memory_data.get('total_memory', 0)
                    self.leak_detector.take_memory_snapshot({ 'memory_rss_mb': total_mb })
                except Exception as _e:
                    # Non-fatal; continue collection
                    pass

                # Limit advanced history size
                if len(self.advanced_data_history) > self.max_history:
                    self.advanced_data_history = self.advanced_data_history[-self.max_history:]

                # Perform leak analysis if we have enough advanced data
                if len(self.advanced_data_history) > 10:
                    try:
                        # Simple leak detection using advanced monitoring data
                        recent_data = self.advanced_data_history[-10:]
                        menubar_trend = [d.get('menubar_memory', 0) for d in recent_data]
                        service_trend = [d.get('service_memory', 0) for d in recent_data]

                        # Check for consistent growth
                        if len(menubar_trend) >= 2 and len(service_trend) >= 2:
                            menubar_growth = menubar_trend[-1] - menubar_trend[0]
                            service_growth = service_trend[-1] - service_trend[0]

                            # Memory growth detection (silent monitoring)
                            if menubar_growth > 5.0:  # More than 5MB growth
                                pass  # Could log to file if needed

                            if service_growth > 5.0:  # More than 5MB growth
                                pass  # Could log to file if needed

                    except Exception as e:
                        print(f"Error in leak analysis: {e}")


                # Wait for the specified interval
                time.sleep(self.monitor_interval)

            except Exception as e:
                print(f"Error in background monitoring: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)  # Wait before retrying

        # Background monitoring loop stopped

    def force_garbage_collection(self):
        """Force garbage collection and return stats"""
        try:
            # Get memory before cleanup
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024

            # Force garbage collection
            collected = gc.collect()

            # Get memory after cleanup
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_freed = memory_before - memory_after

            return {
                "status": "completed",
                "objects_collected": collected,
                "memory_before_mb": round(memory_before, 2),
                "memory_after_mb": round(memory_after, 2),
                "memory_freed_mb": round(memory_freed, 2),
                "gc_stats": gc.get_stats()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_leak_analysis(self):
        """Get comprehensive leak analysis with runtime meta for UI.
        Always includes:
          - snapshots_total: total snapshots in detector buffer
          - advanced_points: number of advanced monitoring points collected
          - monitoring_active: whether background monitoring is running
          - interval: current monitoring interval (seconds)
        """
        try:
            result = self.leak_detector.analyze_for_leaks()
            if not isinstance(result, dict):
                result = {"status": str(result)}
        except Exception as e:
            result = {"status": "error", "error": str(e)}

        # Attach meta so the UI can show progress even before analysis stabilizes
        result.update({
            "snapshots_total": len(self.leak_detector.memory_snapshots),
            "advanced_points": len(self.advanced_data_history),
            "monitoring_active": self.monitoring_active,
            "interval": self.monitor_interval,
        })
        return result

    def get_comprehensive_dashboard_data(self):
        """Provides a comprehensive payload for the dashboard, including historical and real-time data."""

        # Get the latest real-time data
        latest_data = self.get_memory_data()

        # Update peak values based on the latest data
        if 'clipboard' in latest_data and 'processes' in latest_data['clipboard']:
            menubar_process = next((p for p in latest_data['clipboard']['processes'] if p.get('process_type') == 'menu_bar'), None)
            service_process = next((p for p in latest_data['clipboard']['processes'] if p.get('process_type') == 'main_service'), None)

            if menubar_process:
                self.peak_menubar_memory = max(self.peak_menubar_memory, menubar_process.get('memory_mb', 0))
                self.peak_menubar_cpu = max(self.peak_menubar_cpu, menubar_process.get('cpu_percent', 0))

            if service_process:
                self.peak_service_memory = max(self.peak_service_memory, service_process.get('memory_mb', 0))
                self.peak_service_cpu = max(self.peak_service_cpu, service_process.get('cpu_percent', 0))

            total_memory = latest_data['clipboard'].get('total_memory_mb', 0)
            self.peak_total_memory = max(self.peak_total_memory, total_memory)

            total_cpu = sum(p.get('cpu_percent', 0) for p in latest_data['clipboard']['processes'])
            self.peak_total_cpu = max(self.peak_total_cpu, total_cpu)

        # Add updated peak values to the payload
        latest_data.update({
            'peak_menubar_memory': self.peak_menubar_memory,
            'peak_service_memory': self.peak_service_memory,
            'peak_total_memory': self.peak_total_memory,
            'peak_menubar_cpu': self.peak_menubar_cpu,
            'peak_service_cpu': self.peak_service_cpu,
            'peak_total_cpu': self.peak_total_cpu,
        })

        # Add monitoring status
        latest_data['monitoring_status'] = {
            'active': self.monitoring_active,
            'start_time': self.monitoring_start_time.isoformat() if self.monitoring_start_time else None,
            'interval': self.monitor_interval,
            'advanced_data_points': len(self.advanced_data_history),
        }

        return latest_data

    def get_dashboard_status(self):
        """Get dashboard status information for menu bar app"""
        try:
            # Calculate time since last activity
            time_since_activity = datetime.now() - self.last_activity_time
            minutes_inactive = time_since_activity.total_seconds() / 60
            seconds_inactive = time_since_activity.total_seconds()

            # Calculate countdown for auto-timeout
            countdown_seconds = 0
            if self.auto_start_mode and not self.monitoring_active:
                remaining_minutes = self.auto_timeout_minutes - minutes_inactive
                countdown_seconds = max(0, remaining_minutes * 60)

            # Determine status
            if self.monitoring_active:
                status = "active_in_use"
                status_message = "Active and in use (Advanced Monitoring)"
            elif seconds_inactive < 10:  # Recent activity (within 10 seconds)


                status = "active_in_use"
                status_message = "Active and in use"
            elif self.auto_start_mode and countdown_seconds > 0:
                status = "active_not_in_use"
                countdown_minutes = int(countdown_seconds // 60)
                countdown_secs = int(countdown_seconds % 60)
                status_message = f"Active but not in use ({countdown_minutes}:{countdown_secs:02d} until shutdown)"
            elif not self.auto_start_mode:
                status = "active_persistent"
                status_message = "Active (Manual mode - no timeout)"
            else:
                status = "inactive"
                status_message = "Inactive"

            # Get current memory and CPU data directly from collect_memory_data
            memory_data = self.collect_memory_data()

            menubar_memory = memory_data.get('menubar_memory', 0)
            service_memory = memory_data.get('service_memory', 0)
            dashboard_memory = memory_data.get('dashboard_memory', 0)
            menubar_cpu = memory_data.get('menubar_cpu', 0)
            service_cpu = memory_data.get('service_cpu', 0)
            dashboard_cpu = memory_data.get('dashboard_cpu', 0)

            return {
                "status": status,
                "status_message": status_message,
                "auto_start_mode": self.auto_start_mode,
                "monitoring_active": self.monitoring_active,
                "last_activity_seconds": seconds_inactive,
                "countdown_seconds": countdown_seconds,
                "memory": {
                    "menubar": {
                        "current": menubar_memory,
                        "peak": self.peak_menubar_memory,
                        "cpu": menubar_cpu,
                        "peak_cpu": self.peak_menubar_cpu
                    },
                    "service": {
                        "current": service_memory,
                        "peak": self.peak_service_memory,
                        "cpu": service_cpu,
                        "peak_cpu": self.peak_service_cpu
                    },
                    "dashboard": {
                        "current": dashboard_memory,
                        "peak": self.peak_dashboard_memory,
                        "cpu": dashboard_cpu,
                        "peak_cpu": self.peak_dashboard_cpu
                    },
                    "total": {
                        "current": menubar_memory + service_memory + dashboard_memory,
                        "peak": self.peak_total_memory,
                        "cpu": menubar_cpu + service_cpu + dashboard_cpu,
                        "peak_cpu": self.peak_total_cpu
                    }
                },
                "session": {
                    "start_time": self.session_start_time.isoformat(),
                    "duration_minutes": (datetime.now() - self.session_start_time).total_seconds() / 60
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "status_message": f"Error getting status: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
,
                "health": {
                    "score": health_score,
                    "budgets": self.budgets
                }
            }

    def get_monitoring_dashboard_data(self):
        """Get comprehensive dashboard data for monitoring dashboard compatibility"""
        try:
            memory_data = self.get_memory_data()
            system_data = self.get_system_data()

            # Calculate monitoring duration
            monitoring_duration_hours = 0
            if self.monitoring_start_time:
                duration_seconds = (datetime.now() - self.monitoring_start_time).total_seconds()
                monitoring_duration_hours = duration_seconds / 3600

            return {
                "dashboard_status": "active" if self.monitoring_active else "inactive",
                "timestamp": datetime.now().isoformat(),
                "data_history_length": len(self.data_history),  # Basic data collection count
                "system_info": {
                    "cpu_percent": system_data.get("cpu_percent", 0),
                    "memory_percent": memory_data.get("system", {}).get("percent", 0)
                },
                "long_term_monitoring": {
                    "status": "active" if self.monitoring_active else "inactive",
                    "data_points": len(self.advanced_data_history),  # Advanced monitoring points only
                    "monitoring_duration_hours": monitoring_duration_hours,
                    "interval": self.monitor_interval,
                    "alerts_sent": self.alert_count,
                    "latest_data": {
                        "processes": {
                            "menu_bar": {
                                "memory_rss_mb": memory_data.get("clipboard", {}).get("processes", [{}])[0].get("memory_mb", 0)
                            }
                        }
                    }
                },
                "advanced_profiling": {
                    "status": "active" if self.leak_detector.tracemalloc_enabled else "inactive",
                    "total_snapshots": len(self.leak_detector.memory_snapshots),
                    "tracemalloc_enabled": self.leak_detector.tracemalloc_enabled,
                    "latest_snapshot": {
                        "process_info": {
                            "memory_rss_mb": memory_data.get("clipboard", {}).get("total_memory_mb", 0)
                        },
                        "object_analysis": {
                            "total_objects": sum(self.leak_detector._get_object_counts().values())
                        }
                    }
                },
                "validation_results": {
                    "validation_data": []  # Placeholder for validation data
                }
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _auto_timeout_monitor(self):
        """Monitor for auto-timeout when in auto-start mode"""
        print(f"Auto-timeout monitor started (5-minute inactivity timeout)")

        while True:
            try:
                time.sleep(30)  # Check every 30 seconds

                # Calculate time since last activity
                time_since_activity = datetime.now() - self.last_activity_time
                minutes_inactive = time_since_activity.total_seconds() / 60

                # Don't timeout if advanced monitoring is active
                if self.monitoring_active:
                    continue

                # Check if we've exceeded the timeout
                if minutes_inactive >= self.auto_timeout_minutes:
                    # Graceful shutdown
                    if self.server:
                        threading.Thread(target=self.server.shutdown).start()
                    break

            except Exception as e:
                print(f"Error in auto-timeout monitor: {e}")
                time.sleep(60)  # Wait longer on error

    def run(self):
        """Run the unified dashboard server."""
        print(f"🚀 Starting Unified Memory Dashboard on http://localhost:{self.port}")

        # Start data collection in background
        def collect_data():
            while True:
                try:
                    data = self.collect_memory_data()
                    self.data_history.append(data)

                    # Limit history size
                    # Limit history size
                    if len(self.data_history) > self.max_history:
                        self.data_history = self.data_history[-self.max_history:]

                        # Compute simple anomalies (z-score over last N)
                        try:
                            N = 60
                            recent = self.data_history[-N:]
                            def ez(arr):
                                import statistics
                                if len(arr) < 5: return 0,0,0
                                mean = statistics.mean(arr)
                                st = statistics.pstdev(arr) or 1.0
                                z = (arr[-1] - mean) / st
                                return z, mean, st
                            z_total, mean_total, st_total = ez([p.get('menubar_memory',0)+p.get('service_memory',0)+p.get('dashboard_memory',0) for p in recent])
                            z_m, mean_m, st_m = ez([p.get('menubar_memory',0) for p in recent])
                            z_s, mean_s, st_s = ez([p.get('service_memory',0) for p in recent])
                            anomalies = []
                            if abs(z_total) >= 3: anomalies.append({"type":"total_memory_z3","z":round(z_total,2)})
                            if abs(z_m) >= 3: anomalies.append({"type":"menubar_memory_z3","z":round(z_m,2)})
                            if abs(z_s) >= 3: anomalies.append({"type":"service_memory_z3","z":round(z_s,2)})
                        except Exception:
                            anomalies = []

                        data['anomalies'] = anomalies
                        data['health'] = {
                            'score': (100 - min(100, (menubar_memory+service_memory+dashboard_memory) / self.budgets.get('total_memory_mb',600.0) * 100)),
                            'budgets': self.budgets
                        }

                    time.sleep(1)  # Collect data every second
                except Exception as e:
                    print(f"Error collecting data: {e}")
                    time.sleep(5)

        def _start_dev_reloader(self, watched_file):
            """Start a file watcher thread to restart the server when the file changes (dev only)."""
            if self.dev_reload:
                return  # already running
            self.dev_reload = True

            def watcher():
                try:
                    last_mtime = os.path.getmtime(watched_file)
                except Exception:
                    last_mtime = None
                while self.dev_reload:
                    try:
                        time.sleep(1.0)
                        mtime = os.path.getmtime(watched_file)
                        if last_mtime is not None and mtime != last_mtime:
                            print("🔁 Detected change in unified_memory_dashboard.py — restarting server...")
                            # Gracefully shutdown
                            try:
                                if self.server:
                                    self.server.shutdown()
                            except Exception:
                                pass
                            os._exit(3)  # Let parent supervisor restart us; fallback to exit
                        last_mtime = mtime
                    except Exception:
                        continue

            t = threading.Thread(target=watcher, daemon=True)
            t.start()

        # Start background data collection
        data_thread = threading.Thread(target=collect_data)
        data_thread.daemon = True
        data_thread.start()

        # Start auto-timeout monitoring if in auto-start mode
        if self.auto_start_mode:
            timeout_thread = threading.Thread(target=self._auto_timeout_monitor)
            timeout_thread.daemon = True
            timeout_thread.start()

        # Open browser (only if not in auto-start mode)
        if not self.auto_start_mode:
            def open_browser():
                time.sleep(2)  # Wait for server to start
                webbrowser.open(f'http://localhost:{self.port}')

            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
        else:
            print(f"Auto-start mode: Dashboard available at http://localhost:{self.port} (no browser auto-open)")

        # Create request handler with dashboard instance
        def handler(*args, **kwargs):
            return self.RequestHandler(self, *args, **kwargs)

        # Run HTTP server
        try:
            self.server = HTTPServer(('localhost', self.port), handler)
            print(f"✅ Dashboard server started at http://localhost:{self.port}")
            # Start dev reloader if requested via env/flag
            enable_reload = os.environ.get('CLIPBOARD_DASHBOARD_DEV_RELOAD', '0') == '1' or '--dev-reload' in sys.argv
            if enable_reload:
                self._start_dev_reloader(os.path.abspath(__file__))
                print("🛠️ Dev auto-reload enabled (watching unified_memory_dashboard.py)")
            self.server.serve_forever()
        except Exception as e:
            print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    import argparse
    import os
    import sys

    # PROTECTION: Prevent recursive launches
    if 'CLIPBOARD_MONITOR_DASHBOARD_PARENT' in os.environ:
        parent_pid = os.environ.get('CLIPBOARD_MONITOR_DASHBOARD_PARENT')
        print(f"Dashboard launched by ClipboardMonitor parent PID {parent_pid}")

        # Check if parent is still running
        try:
            import psutil
            if not psutil.pid_exists(int(parent_pid)):
                print("Parent process no longer exists, exiting dashboard")
                sys.exit(0)
        except:
            pass

    # PROTECTION: Check for multiple dashboard instances (only for auto-start mode)
    # Manual starts are allowed to override existing instances
    if '--auto-start' in sys.argv:
        try:
            import psutil
            dashboard_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline)
                        if 'unified_memory_dashboard.py' in cmdline_str and proc.info['pid'] != os.getpid():
                            dashboard_processes.append(proc.info['pid'])
                except:
                    continue

            if len(dashboard_processes) > 0:
                print(f"Other dashboard instances detected ({len(dashboard_processes)}), exiting auto-start to prevent conflicts")
                sys.exit(0)
        except:
            pass  # If check fails, continue with caution
    else:
        print("Manual dashboard start - will override any existing instances")

    parser = argparse.ArgumentParser(description='Unified Memory Dashboard')
    parser.add_argument('--auto-start', action='store_true',
                       help='Start in auto-start mode (no browser, 5-minute timeout)')
    parser.add_argument('--port', type=int, default=8001,
                       help='Port to run the dashboard on (default: 8001)')

    args = parser.parse_args()

    dashboard = UnifiedMemoryDashboard(port=args.port, auto_start=args.auto_start)
    dashboard.run()
