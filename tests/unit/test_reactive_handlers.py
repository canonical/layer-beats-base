# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
import sys
from unittest import TestCase, mock
from unittest.mock import Mock, call

from charms.reactive import is_state, remove_state

# charms.layer.status only exists in the built charm; mock it out before
# the beats_base imports since those depend on c.l.s.*.
layer_mock = Mock()
sys.modules["charms.layer"] = layer_mock
sys.modules["charms.layer.status"] = layer_mock

from beats_base import cache_elasticsearch_data  # noqa: E402
from beats_base import (  # noqa: E402
    cache_kafka_data,
    cache_logstash_data,
    cache_remove_elasticsearch_data,
    cache_remove_kafka_data,
    cache_remove_logstash_data,
    config_changed,
    waiting_messaging,
)


class TestHandlers(TestCase):
    """Tests our handlers."""

    def test_config_chanaged(self):
        """Verify config_changed sets appropriate states."""
        remove_state("beat.render")
        config_changed()
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.status.waiting")
    def test_waiting_messaging(self, mock_waiting):
        """Verify status is waiting when not connected."""
        waiting_messaging()
        self.assertTrue(mock_waiting.called)

    @mock.patch("beats_base.kv")
    def test_cache_logstash_data(self, mock_kv):
        """Verify logstash hosts and the render flag are set."""

        class Endpoint(dict):
            def __init__(self, *args, **kw):
                super(Endpoint, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"private_address": None, "port": None}]

        logstash = Endpoint()
        remove_state("beat.render")
        cache_logstash_data(logstash)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_logstash_data(self, mock_kv):
        """Verify logstash hosts are removed the render flag is set."""
        kv_calls = [call(), call().unset("beat.logstash")]

        remove_state("beat.render")
        cache_remove_logstash_data()
        self.assertTrue(mock_kv.mock_calls == kv_calls)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_elasticsearch_data(self, mock_kv):
        """Verify ES hosts and the render flag are set."""

        class Endpoint(dict):
            def __init__(self, *args, **kw):
                super(Endpoint, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"host": None, "port": None}]

        es = Endpoint()

        remove_state("beat.render")
        cache_elasticsearch_data(es)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_elasticsearch_data(self, mock_kv):
        """Verify ES hosts are removed the render flag is set."""
        kv_calls = [call(), call().unset("beat.elasticsearch")]

        remove_state("beat.render")
        cache_remove_elasticsearch_data()
        self.assertTrue(mock_kv.mock_calls == kv_calls)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_kafka_data(self, mock_kv):
        """Verify Kafka hosts and the render flag are set."""

        class Endpoint(dict):
            def __init__(self, *args, **kw):
                super(Endpoint, self).__init__(*args, **kw)

            def kafkas(self):
                return [{"host": None, "port": None}]

        kafka = Endpoint()
        remove_state("beat.render")
        cache_kafka_data(kafka)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_kafka_data(self, mock_kv):
        """Verify Kafka hosts are removed the render flag is set."""
        kv_calls = [call(), call().unset("beat.kafka")]

        remove_state("beat.render")
        cache_remove_kafka_data()
        self.assertTrue(mock_kv.mock_calls == kv_calls)
        self.assertTrue(is_state("beat.render"))
