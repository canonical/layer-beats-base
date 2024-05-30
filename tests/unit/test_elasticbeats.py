# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
import sys
from unittest import TestCase, mock
from unittest.mock import Mock

# A few layers only exists in the built charm; mock them out before
# the elasticbeats imports since those depend on these layers.
layer_mock = Mock()
sys.modules["charms.apt"] = layer_mock
sys.modules["charms.layer.status"] = layer_mock

from elasticbeats import (  # noqa: E402
    enable_beat_on_boot,
    get_package_candidate,
    render_without_context,
)


class TestElasticBeats(TestCase):
    """Tests our Elastic Beat library."""

    def setUp(self):
        mkdir_patcher = mock.patch("elasticbeats.mkdir")
        render_patcher = mock.patch("elasticbeats.render")
        mkdir_patcher.start()
        render_patcher.start()
        self.addCleanup(mkdir_patcher.stop)
        self.addCleanup(render_patcher.stop)

    @mock.patch("elasticbeats.get_package_version")
    @mock.patch("elasticbeats.subprocess.Popen")
    def test_get_package_candidate(self, mock_sub, mock_pkg_ver):
        """Verify apt repo package queries."""
        policy_proc = mock.Mock()
        grep_proc = mock.Mock()

        # simulate a missing repo pkg
        grep_attrs = {"communicate.return_value": (b"", "stderr")}
        grep_proc.configure_mock(**grep_attrs)

        # test a missing repo pkg (None returned)
        mock_sub.return_value = policy_proc
        mock_sub.return_value = grep_proc
        mock_pkg_ver.return_value = ""
        self.assertEqual(None, get_package_candidate("foo"))

        # reset our grep args to simulate the repo pkg being found
        grep_attrs = {"communicate.return_value": (b"Candidate: 1.2.3", "stderr")}
        grep_proc.configure_mock(**grep_attrs)

        # test a missing installed pkg (new version is returned)
        mock_sub.return_value = policy_proc
        mock_sub.return_value = grep_proc
        mock_pkg_ver.return_value = ""
        self.assertEqual("1.2.3", get_package_candidate("foo"))

        # test repo and installed pkg versions are the same (None returned)
        mock_sub.return_value = policy_proc
        mock_sub.return_value = grep_proc
        mock_pkg_ver.return_value = "1.2.3"
        self.assertEqual(None, get_package_candidate("foo"))

        # test repo pkg is newer than installed pkg (new version is returned)
        mock_sub.return_value = policy_proc
        mock_sub.return_value = grep_proc
        mock_pkg_ver.return_value = "0"
        self.assertEqual("1.2.3", get_package_candidate("foo"))

    @mock.patch("elasticbeats.remove_beat_on_boot")
    @mock.patch("elasticbeats.service_resume")
    def test_enable_beats_on_boot(self, resume_mock, remove_beat_on_boot_mock):
        service_name = "filebeat.service"
        enable_beat_on_boot(service_name)

        resume_mock.assert_called_once_with(service_name)
        remove_beat_on_boot_mock.assert_called_once_with(service_name)

    @mock.patch("elasticbeats.kv")
    @mock.patch("elasticbeats.path")
    @mock.patch("elasticbeats.config")
    @mock.patch("elasticbeats.model_info_cache")
    @mock.patch("elasticbeats.principal_unit_cache")
    @mock.patch("elasticbeats.write_file")
    def test_render_without_context(
        self,
        mock_write_file,
        mock_principal_unit_cache,
        mock_model_info_cache,
        mock_config,
        mock_path,
        mock_kv,
    ):
        test_kv = {
            "model_name": "test_model",
            "model_uuid": "xxxx-xxxx",
            "principal_name": "ubuntu/0",
            "beat.logstash": "logstash",
            "beat.elasticsearch": "elasticsearch",
            "beat.kafka": "kafka",
        }
        mock_kv.return_value = test_kv
        mock_config.return_value = {"logstash_hosts": "logstash", "kafka_hosts": "kafka"}
        render_without_context(mock.Mock(), mock.Mock())
        mock_write_file.assert_called_once()
