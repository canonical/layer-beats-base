# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Library for interacting with elasticbeats."""

import subprocess
from os import getenv, path

from charmhelpers.core.hookenv import config, juju_version, log, principal_unit
from charmhelpers.core.host import service_pause, service_resume
from charmhelpers.core.unitdata import kv
from charms.apt import get_package_version
from charms.templating.jinja2 import render


def render_without_context(source, target):
    """Render beat template from global state context."""
    cache = kv()
    context = dict(config())
    connected = False

    # Add deployment attributes
    model_info_cache()
    principal_unit_cache()
    context["juju_model_name"] = cache.get("model_name")
    context["juju_model_uuid"] = cache.get("model_uuid")
    context["juju_principal_unit"] = cache.get("principal_name")

    logstash_hosts = cache.get("beat.logstash")
    elasticsearch_hosts = cache.get("beat.elasticsearch")
    kafka_hosts = cache.get("beat.kafka")

    if logstash_hosts:
        connected = True
    context.update({"logstash": logstash_hosts})
    if context["logstash_hosts"]:
        connected = True
    if elasticsearch_hosts:
        connected = True
    context.update({"elasticsearch": elasticsearch_hosts})
    if kafka_hosts:
        connected = True
    context.update({"kafka": kafka_hosts})
    if context["kafka_hosts"]:
        connected = True

    # detect various container attributes
    if path.isdir("/var/log/containers"):
        context.update({"has_containers": True})
    if path.isdir("/var/lib/docker/containers"):
        context.update({"has_docker": True})
    if context.get("kube_logs", False) and path.isfile("/root/.kube/config"):
        context.update({"has_k8s": True})

    if "protocols" in context.keys():
        context.update({"protocols": parse_protocols()})

    # Transform some config options into proper lists if they aren't already.
    # Do this only for non-empty values for proper jinja templating.
    for key in ("fields", "logpath"):
        if key in context.keys() and context[key] and not isinstance(context[key], list):
            context[key] = context[key].split(" ")

    render(source, target, context)
    return connected


def model_info_cache():
    """Cache the model info for this deployment.

    This info will not change over the lifetime of the deployment, so we
    only need to set it once.
    """
    cache = kv()
    if not (cache.get("model_name") and cache.get("model_uuid")):
        juju_major_version = int(juju_version().split(".")[0])

        juju_info = {}
        if juju_major_version >= 2:
            juju_info["model_name"] = getenv("JUJU_MODEL_NAME")
            juju_info["model_uuid"] = getenv("JUJU_MODEL_UUID")
        else:
            juju_info["model_name"] = getenv("JUJU_ENV_NAME")
            juju_info["model_uuid"] = getenv("JUJU_ENV_UUID")

        cache.update(juju_info)


def principal_unit_cache():
    """Cache the principal unit that a beat is related to.

    This info will not change over the lifetime of the deployment, so we
    only need to set it once.
    """
    cache = kv()
    if not cache.get("principal_name"):
        principal_name = principal_unit()
        if principal_name:
            cache.set("principal_name", principal_name)


def enable_beat_on_boot(service):
    """Enable the beat to start automaticaly during boot."""
    # Remove any existing links first
    remove_beat_on_boot(service)
    service_resume(service)


def remove_beat_on_boot(service):
    """Remove the beat init service symlinks."""
    service_pause(service)


def push_beat_index(elasticsearch, service, fatal=True):
    """Push a beat index to Elasticsearch.

    :param: str elasticsearch: host string for ES, <ip>:<port>
    :param: str service: index name
    :param: bool fatal: True to raise exception on failure; False to log it
    :returns: bool: True if succesfull; False otherwise
    """
    cmd = [
        "curl",
        "-XPUT",
        "http://{0}/_template/{1}".format(elasticsearch, service),
        "-d@/etc/{0}/{0}.template.json".format(service),
    ]  # noqa

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        if fatal:
            raise
        else:
            log("Failed to push index to Elasticsearch: {}".format(e))
            return False
    else:
        return True


def parse_protocols():
    """Parses the `protocols` config."""
    protocols = config("protocols")
    bag = {}
    for protocol in protocols.split(" "):
        proto, port = protocol.strip().split(":")
        if proto in bag:
            bag[proto].append(int(port))
        else:
            bag.update({proto: []})
            bag[proto].append(int(port))
    return bag


def get_package_candidate(pkg):
    """Get package version from repo.

    returns the package version from the repo if different than the version
    that is currently installed.

    :param: str pkg: package name as known by apt
    :returns: str ver_str: version of new repo package, or None
    """
    # NB: we cannot use the charmhelpers.fetch.apt_cache nor the
    # apt module from the python3-apt deb as they are only available
    # as system packages. Charms with use_system_packages=False in
    # layer.yaml would fail. Subprocess apt-cache policy instead.
    policy_cmd = ["apt-cache", "policy", pkg]
    grep_cmd = ["grep", "Candidate:"]
    p1 = subprocess.Popen(policy_cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(grep_cmd, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    policy_output = p2.communicate()[0].strip().decode()
    p1.wait()

    # policy_output will look like this:
    #  Candidate: 5.6.9
    try:
        new_ver = policy_output.split(":", 1)[1].strip()
    except IndexError:
        return None
    else:
        cur_ver = get_package_version(pkg, full_version=True)
        return new_ver if new_ver != cur_ver else None
