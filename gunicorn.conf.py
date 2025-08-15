# Gunicorn Configuration for Crypto AI Trader
# Production deployment ayarları

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "crypto-ai-trader"

# Daemon mode (background process)
daemon = False

# PID file
pidfile = "/tmp/crypto-ai-trader.pid"

# User/group to run as (optional)
# user = "www-data"
# group = "www-data"

# Preload application for better performance
preload_app = True

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

