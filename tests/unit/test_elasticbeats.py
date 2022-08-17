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

from elasticbeats import get_package_candidate  # noqa: E402


class TestElasticBeats(TestCase):
    """Tests our Elastic Beat library."""

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
