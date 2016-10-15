# a Ansible REST API

# Run
Start redis server:
```
$ redis-server
```
Start celery worker:
```
$ celery -A main.celery worker
```

Start API server:
```
$ python run.py
```

