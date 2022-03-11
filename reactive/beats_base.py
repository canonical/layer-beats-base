from charms.layer import status
from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import set_state
from charmhelpers.core.unitdata import kv


@when('config.changed')
def config_changed():
    set_state('beat.render')


@when_not('logstash.available',
          'elasticsearch.available',
          'kafka.ready',
          'config.set.logstash_hosts',
          'config.set.kafka_hosts')
def waiting_messaging():
    status.waiting('Waiting for: elasticsearch, logstash or kafka.')


@when('logstash.available')
def cache_logstash_data(logstash):
    units = logstash.list_unit_data()
    cache = kv()
    if cache.get('beat.logstash'):
        hosts = cache.get('beat.logstash')
    else:
        hosts = []
    removed_hosts = hosts.copy()
    for unit in units:
        host_string = "{0}:{1}".format(unit['private_address'],
                                       unit['port'])
        if host_string not in hosts:
            hosts.append(host_string)
        else:
            removed_hosts.remove(host_string)
    if len(removed_hosts) != 0:
        for host in removed_hosts:
            hosts.remove(host)

    cache.set('beat.logstash', hosts)
    set_state('beat.render')


@when_not('logstash.available')
def cache_remove_logstash_data():
    cache = kv()
    cache.unset('beat.logstash')
    set_state('beat.render')


@when('elasticsearch.available')
def cache_elasticsearch_data(elasticsearch):
    units = elasticsearch.list_unit_data()
    cache = kv()
    hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit['host'],
                                       unit['port'])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set('beat.elasticsearch', hosts)
    set_state('beat.render')


@when_not('elasticsearch.available')
def cache_remove_elasticsearch_data():
    cache = kv()
    cache.unset('beat.elasticsearch')
    set_state('beat.render')


@when('kafka.ready')
def cache_kafka_data(kafka):
    units = kafka.kafkas()
    cache = kv()
    hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit['host'],
                                       unit['port'])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set('beat.kafka', hosts)
    set_state('beat.render')


@when_not('kafka.ready')
def cache_remove_kafka_data():
    cache = kv()
    cache.unset('beat.kafka')
    set_state('beat.render')
