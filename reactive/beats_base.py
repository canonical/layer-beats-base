from charms.layer import status
from charmhelpers.core.unitdata import kv

from charms.reactive import (
    when,
    when_not,
    set_state,
)


@when("config.changed")
def config_changed():
    set_state("beat.render")


@when_not("logstash.available",
          "elasticsearch.available",
          "kafka.ready",
          "config.set.logstash_hosts",
          "config.set.kafka_hosts")
def waiting_messaging():
    status.waiting("Waiting for: elasticsearch, logstash or kafka.")


def cache_data(host_name, host_instance):
    if host_name == "kafka":
        units = host_instance.kafkas()
    else:
        units = host_instance.list_unit_data()

    cache = kv()
    hosts = []
    address_key = "private_address" if host_name == "logstash" else "host"
    for unit in units:
        host_string = "{0}:{1}".format(unit[address_key],
                                       unit["port"])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set("beat.{}".format(host_name), hosts)
    set_state("beat.render")


def cache_remove_data(host_name):
    cache = kv()
    cache.unset("beat.{}".format(host_name))
    set_state("beat.render")


@when("logstash.available")
def cache_logstash_data(logstash):
    cache_data("logstash", logstash)


@when_not("logstash.available")
def cache_remove_logstash_data():
    cache_remove_data("logstash")


@when("elasticsearch.available")
def cache_elasticsearch_data(elasticsearch):
    cache_data("elasticsearch", elasticsearch)


@when_not("elasticsearch.available")
def cache_remove_elasticsearch_data():
    cache_remove_data("elasticsearch")


@when("kafka.ready")
def cache_kafka_data(kafka):
    cache_data("kafka", kafka)


@when_not("kafka.ready")
def cache_remove_kafka_data():
    cache_remove_data("kafka")
