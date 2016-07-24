# a Ansible REST API

# Method
## List playbooks
> GET `/`

## List playbook detail
> GET '/<playbook>'
> GET '/<playbook>/detail'

## Invoke playbook
> POST '/<playbook>'
> params
> - forks
> - limits
> - private_key
> - ssh user
> - ssh password
> - tags
> - hosts
> - method
> RESPONSE {name: <playbook>, id: <task_id>}

## Get task status
> GET '/<task_id>'
> RESPONSE {id: <task_id>, state: <task_state>, result: <task_result>}

# Run
Start redis server:
```
$ redis-server
```
Start celery worker:
```
$ python -A main.celery worker
```

Start API server:
```
$ python run.py
```

