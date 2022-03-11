# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Base reactive file for beats charms."""
from charmhelpers.core.unitdata import kv
from charms.layer import status
from charms.reactive import set_state, when, when_not


@when("config.changed")
def config_changed():
    """Handle config changes."""
    set_state("beat.render")


@when_not(
    "logstash.available",
    "elasticsearch.available",
    "kafka.ready",
    "config.set.logstash_hosts",
    "config.set.kafka_hosts",
)
def waiting_messaging():
    """Set status when waiting on relations."""
    status.waiting("Waiting for: elasticsearch, logstash or kafka.")


@when("logstash.available")
def cache_logstash_data(logstash):
    """Use unit database to cache connected hosts until beat is available."""
    units = logstash.list_unit_data()
    cache = kv()
    if cache.get("beat.logstash"):
        hosts = cache.get("beat.logstash")
    else:
        hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit["private_address"], unit["port"])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set("beat.logstash", hosts)
    set_state("beat.render")


@when_not("logstash.available")
def cache_remove_logstash_data():
    """Remove cache no longer needed now that logstash relation is gone."""
    cache = kv()
    cache.unset("beat.logstash")
    set_state("beat.render")


@when("elasticsearch.available")
def cache_elasticsearch_data(elasticsearch):
    """Use unit database to cache connected hosts until beat is available."""
    units = elasticsearch.list_unit_data()
    cache = kv()
    hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit["host"], unit["port"])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set("beat.elasticsearch", hosts)
    set_state("beat.render")


@when_not("elasticsearch.available")
def cache_remove_elasticsearch_data():
    """Remove cache no longer needed now that elasticsearch relation is gone."""
    cache = kv()
    cache.unset("beat.elasticsearch")
    set_state("beat.render")


@when("kafka.ready")
def cache_kafka_data(kafka):
    """Handle when Kafka is related."""
    units = kafka.kafkas()
    cache = kv()
    hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit["host"], unit["port"])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set("beat.kafka", hosts)
    set_state("beat.render")


@when_not("kafka.ready")
def cache_remove_kafka_data():
    """Handle when Kafka is departed."""
    cache = kv()
    cache.unset("beat.kafka")
    set_state("beat.render")
