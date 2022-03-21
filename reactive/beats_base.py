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


def cache_data(service, host_instance):
    """Use unit database to cache connected hosts until beat is available."""
    if service == "kafka":
        units = host_instance.kafkas()
    else:
        units = host_instance.list_unit_data()

    cache = kv()
    hosts = []
    address_key = "private_address" if service == "logstash" else "host"
    for unit in units:
        host_string = "{0}:{1}".format(unit[address_key], unit["port"])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set("beat.{}".format(service), hosts)
    set_state("beat.render")


def cache_remove_data(service):
    """Remove cache no longer needed now that logstash relation is gone."""
    cache = kv()
    cache.unset("beat.{}".format(service))
    set_state("beat.render")


@when("logstash.available")
def cache_logstash_data(logstash):
    """Handle when logstash is related."""
    cache_data("logstash", logstash)


@when_not("logstash.available")
def cache_remove_logstash_data():
    """Remove cache no longer needed now that logstash relation is gone."""
    cache_remove_data("logstash")


@when("elasticsearch.available")
def cache_elasticsearch_data(elasticsearch):
    """Handle when elasticsearch is related."""
    cache_data("elasticsearch", elasticsearch)


@when_not("elasticsearch.available")
def cache_remove_elasticsearch_data():
    """Remove cache no longer needed now that elasticsearch relation is gone."""
    cache_remove_data("elasticsearch")


@when("kafka.ready")
def cache_kafka_data(kafka):
    """Handle when Kafka is related."""
    cache_data("kafka", kafka)


@when_not("kafka.ready")
def cache_remove_kafka_data():
    """Handle when Kafka is departed."""
    cache_remove_data("kafka")
