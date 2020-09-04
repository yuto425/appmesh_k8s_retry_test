bind = '0.0.0.0:5000'

workers = 10
worker_class = "sync"
worker_connections = 1000
timeout = 4000
keepalive = 2

daemon = False

loglevel = "debug"
access_log_format = (
    '%({X-Forwarded-For}i)s %(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s"'
)

graceful_timeout = 3600
