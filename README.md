# Beats Base

> [!NOTE]
> This charm is under maintenance mode. Only critical bug will be handled.

This is a middle layer to include the common functions among the Elastic Beats
products. Such as delivery via apt and common template parsing routines.


## States

`beat.render` - When this state is set, you will need to re-render template
data. This state occurs when a unit has received changes from a related
application such as `elasticsearch` or `logstash`

## lib/elasticbeats.py

This python module is an abstraction to aid in deployment of beats following
common practices in charming and conventions with the beats stack.

- `render_without_context` - This renders a provided jinja template using the
charms configuration and relation data as context objects.

- `enable_beat_on_boot` - This enables an init.d style job

- `remove_beat_on_boot` - This removes symlinks for an init.d style job

- `push_beat_index` - Reads from a .json file in /etc/*mybeat*/mybeat.template.json

- `get_package_candidate` - Checks the configured apt repo for an available
candidate version.

## Writing Your Own Beat

Consuming beats-base as your base-layer when charming a beat makes this an
exercise in fill in the blanks. With some project meta, and handling the
`beat.render` state will make this a quick path of integration.

Provide the following as a getting started guide, along with a jinja template
of the beats configuration and you're done with the first step to charming up
an elastic beat!

Thank You :)

`layer.yaml`

```yaml
includes:
  - beats-base
```

`metadata.yaml`

```
name: mybeat
summary: Deploys mybeat
maintainer: you <you@yourcorp.tld>
description: |
  What does your beat do? Specifics count.
series:
  - xenial

```

`reactive/mybeat.py`

```python
from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import when_any
from charms.reactive import set_state
from charms.reactive import remove_state

from charmhelpers.core.hookenv import status_set
from charmhelpers.core.host import service_restart

from elasticbeats import render_without_context
from elasticbeats import enable_beat_on_boot
from elasticbeats import push_beat_index


@when_not('mybeat.installed')
def install_mybeat():
    # do something useful here to install your beat

@when('beat.render')
@when_any('elasticsearch.available', 'logstash.available')
def render_mybeat_template():
    render_without_context('packetbeat.yml', '/etc/mybeat/mybeat.yml')
    remove_state('beat.render')
    service_restart('mybeat')
    status_set('active', 'mybeat ready')


@when('mybeat.installed')
@when_not('mybeat.autostarted')
def enlist_beat():
    enable_beat_on_boot('mybeat')
    set_state('mybeat.autostarted')


@when('elasticsearch.available')
@when_not('mybeat.index.pushed')
def push_mybeat_index(elasticsearch):
    hosts = elasticsearch.list_unit_data()
    for host in hosts:
        host_string = "{}:{}".format(host['host'], host['port'])
    push_beat_index(host_string, 'mybeat')
    set_state('mybeat.index.pushed')

```
