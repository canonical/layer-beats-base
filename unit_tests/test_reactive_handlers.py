import sys

from charms.reactive import is_state, remove_state
from unittest import TestCase, mock
from unittest.mock import Mock, call

# charms.layer.status only exists in the built charm; mock it out before
# the beats_base imports since those depend on c.l.s.*.
layer_mock = Mock()
sys.modules["charms.layer"] = layer_mock
sys.modules["charms.layer.status"] = layer_mock

from beats_base import (
    config_changed,
    waiting_messaging,
    cache_data,
    cache_remove_data,
    cache_logstash_data,
    cache_remove_logstash_data,
    cache_elasticsearch_data,
    cache_remove_elasticsearch_data,
    cache_kafka_data,
    cache_remove_kafka_data,
)  # noqa: E402


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

        kv_calls = []
        logstash = EndpointLogstash()
        mock_kv().get.return_value = []
        remove_state("beat.render")
        cache_data("logstash", logstash)
        self.assertTrue(is_state("beat.render"))
        kv_calls = [call(), call(), call().set("beat.logstash", ["1.1.1.1:88"])]
        self.assertEqual(mock_kv.mock_calls, kv_calls)

        mock_kv().get.return_value = ["1.1.1.1:88", "2.2.2.2:88"]
        remove_state("beat.render")
        cache_data("logstash", logstash)
        self.assertTrue(is_state("beat.render"))
        kv_calls = kv_calls + [call(), call(),
                               call().set("beat.logstash", ["1.1.1.1:88"])]
        self.assertEqual(mock_kv.mock_calls, kv_calls)

        elasticsearch = EndpointElasticsearch()
        mock_kv().get.return_value = []
        remove_state("beat.render")
        cache_data("elasticsearch", elasticsearch)
        self.assertTrue(is_state("beat.render"))
        kv_calls = kv_calls + [call(), call(),
                               call().set("beat.elasticsearch", ["1.1.1.1:88"])]
        self.assertEqual(mock_kv.mock_calls, kv_calls)

        kafka = EndpointKafkas()
        mock_kv().get.return_value = []
        remove_state("beat.render")
        cache_data("kafka", kafka)
        self.assertTrue(is_state("beat.render"))
        kv_calls = kv_calls + [call(), call(),
                               call().set("beat.kafka", ["1.1.1.1:88"])]
        self.assertEqual(mock_kv.mock_calls, kv_calls)

    @mock.patch("beats_base.kv")
    def test_cache_remove_data(self, mock_kv):
        """Verify hosts are removed the render flag is set."""
        logstash_kv_calls = [call(), call().unset("beat.logstash")]
        remove_state("beat.render")
        cache_remove_data("logstash")
        self.assertTrue(mock_kv.mock_calls == logstash_kv_calls)
        self.assertTrue(is_state("beat.render"))

        elasticsearch_kv_calls = logstash_kv_calls +\
            [call(), call().unset("beat.elasticsearch")]
        remove_state("beat.render")
        cache_remove_data("elasticsearch")
        self.assertTrue(mock_kv.mock_calls == elasticsearch_kv_calls)
        self.assertTrue(is_state("beat.render"))

        kafka_kv_calls = elasticsearch_kv_calls +\
            [call(), call().unset("beat.kafka")]
        remove_state("beat.render")
        cache_remove_data("kafka")
        self.assertTrue(mock_kv.mock_calls == kafka_kv_calls)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_logstash_data(self, mock_kv):
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
        remove_state("beat.render")
        cache_remove_logstash_data()
        # self.assert_called_once_with("logstash")
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_elasticsearch_data(self, mock_kv):
        class EndpointElasticsearch(dict):
            def __init__(self, *args, **kw):
                super(EndpointElasticsearch, self).__init__(*args, **kw)

            def list_unit_data(self):
                return [{"host": None, "port": None}]

        elasticsearch = EndpointElasticsearch()
        remove_state("beat.render")
        cache_elasticsearch_data(elasticsearch)
        # self.assert_called_once_with("elasticsearch", elasticsearch)
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_remove_elasticsearch_data(self, mock_kv):
        remove_state("beat.render")
        cache_remove_elasticsearch_data()
        # self.assert_called_once_with("elasticsearch")
        self.assertTrue(is_state("beat.render"))

    @mock.patch("beats_base.kv")
    def test_cache_kafka_data(self, mock_kv):
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
        remove_state("beat.render")
        cache_remove_kafka_data()
        self.assertTrue(is_state("beat.render"))
