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
    cache_data,
    cache_kafka_data,
    cache_logstash_data,
    cache_remove_data,
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
    def test_cache_data(self, mock_kv):
        """Verify hosts and the render flag are set."""

        class EndpointLogstash(dict):
            def __init__(self, *args, **kw):
                super(EndpointLogstash, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"private_address": "1.1.1.1", "port": "88"}]

        class EndpointElasticsearch(dict):
            def __init__(self, *args, **kw):
                super(EndpointElasticsearch, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"host": "1.1.1.1", "port": "88"}]

        class EndpointKafkas(dict):
            def __init__(self, *args, **kw):
                super(EndpointKafkas, self).__init__(*args, **kw)

            def kafkas(self):
                return [{"host": "1.1.1.1", "port": "88"}]

        mock_cache = mock_kv.return_value
        mock_cache.get.return_value = []

        logstash = EndpointLogstash()
        remove_state("beat.render")
        cache_data("logstash", logstash)
        self.assertTrue(is_state("beat.render"))
        mock_kv.assert_called_once()
        mock_cache.set.assert_called_once_with("beat.logstash", ["1.1.1.1:88"])
        mock_kv.assert_called_once()
        mock_cache.set.reset_mock()
        mock_kv.reset_mock()

        mock_cache.get.return_value = ["1.1.1.1:88", "2.2.2.2:88"]
        remove_state("beat.render")
        cache_data("logstash", logstash)
        self.assertTrue(is_state("beat.render"))
        mock_kv.assert_called_once()
        mock_cache.set.assert_called_once_with("beat.logstash", ["1.1.1.1:88"])
        mock_cache.set.reset_mock()
        mock_kv.reset_mock()

        elasticsearch = EndpointElasticsearch()
        mock_cache.get.return_value = []
        remove_state("beat.render")
        cache_data("elasticsearch", elasticsearch)
        self.assertTrue(is_state("beat.render"))
        mock_cache.set.assert_called_once_with("beat.elasticsearch", ["1.1.1.1:88"])
        mock_cache.set.reset_mock()
        mock_kv.reset_mock()

        kafka = EndpointKafkas()
        mock_cache.get.return_value = []
        remove_state("beat.render")
        cache_data("kafka", kafka)
        self.assertTrue(is_state("beat.render"))
        mock_cache.set.assert_called_once_with("beat.kafka", ["1.1.1.1:88"])
        mock_cache.set.reset_mock()
        mock_kv.reset_mock()

    @mock.patch("beats_base.kv")
    def test_cache_remove_data(self, mock_kv):
        """Verify hosts are removed the render flag is set."""
        logstash_kv_calls = [call(), call().unset("beat.logstash")]
        remove_state("beat.render")
        cache_remove_data("logstash")
        self.assertTrue(mock_kv.mock_calls == logstash_kv_calls)
        self.assertTrue(is_state("beat.render"))

        elasticsearch_kv_calls = logstash_kv_calls + [call(), call().unset("beat.elasticsearch")]
        remove_state("beat.render")
        cache_remove_data("elasticsearch")
        self.assertTrue(mock_kv.mock_calls == elasticsearch_kv_calls)
        self.assertTrue(is_state("beat.render"))

        kafka_kv_calls = elasticsearch_kv_calls + [call(), call().unset("beat.kafka")]
        remove_state("beat.render")
        cache_remove_data("kafka")
        self.assertTrue(mock_kv.mock_calls == kafka_kv_calls)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_logstash_data(self, mock_kv):
        """Verify logstash hosts and the render flag are set."""

        class EndpointLogstash(dict):
            def __init__(self, *args, **kw):
                super(EndpointLogstash, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"private_address": None, "port": None}]

        logstash = EndpointLogstash()
        cache_logstash_data(logstash)
        # self.assert_called_once_with("logstash", logstash)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_logstash_data(self, mock_kv):
        """Verify logstash hosts are removed the render flag is set."""
        remove_state("beat.render")
        cache_remove_logstash_data()
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_elasticsearch_data(self, mock_kv):
        """Verify ES hosts and the render flag are set."""

        class EndpointElasticsearch(dict):
            def __init__(self, *args, **kw):
                super(EndpointElasticsearch, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"host": None, "port": None}]

        elasticsearch = EndpointElasticsearch()
        remove_state("beat.render")
        cache_elasticsearch_data(elasticsearch)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_elasticsearch_data(self, mock_kv):
        """Verify ES hosts are removed the render flag is set."""
        remove_state("beat.render")
        cache_remove_elasticsearch_data()
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_kafka_data(self, mock_kv):
        """Verify Kafka hosts and the render flag are set."""

        class EndpointKafkas(dict):
            def __init__(self, *args, **kw):
                super(EndpointKafkas, self).__init__(*args, **kw)

            def kafkas(self):
                return [{"host": None, "port": None}]

        kafka = EndpointKafkas()
        remove_state("beat.render")
        cache_kafka_data(kafka)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_kafka_data(self, mock_kv):
        """Verify Kafka hosts are removed the render flag is set."""
        remove_state("beat.render")
        cache_remove_kafka_data()
        self.assertTrue(is_state("beat.render"))
