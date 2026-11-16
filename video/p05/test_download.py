"""P05 output preservation negative cases. Strictly offline."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from download import (Rejected,archive_provider_result,fetch_video_bytes,
                      validate_ephemeral_url,ffprobe_clip)
from test_engine import mock_mp4


class DownloadTests(unittest.TestCase):
    URL="https://files.example.cloudfront.net/final.mp4?_jwt=dummy_signed_value"
    def setUp(self):
        x=tempfile.TemporaryDirectory()
        self.addCleanup(x.cleanup)
        self.folder=Path(x.name)
    def test_valid_reviewed_ephemeral_https_domain(self):
        self.assertEqual(validate_ephemeral_url(self.URL),self.URL)
    def test_forbid_ssrf_and_unapproved_hosts(self):
        for url in ("http://files.example.cloudfront.net/x.mp4",
                    "https://127.0.0.1/private",
                    "https://169.254.169.254/credentials",
                    "https://cloudfront.net/x.mp4",
                    "https://cloudfront.net.evil.test/x.mp4",
                    "https://evil.com/video.mp4",
                    "https://username:password@files.example.cloudfront.net/x.mp4",
                    "https://files.example.cloudfront.net:8080/x.mp4",
                    "https://files.example.cloudfront.net/x.mp4#fragment"):
            with self.subTest(url=url),self.assertRaises(Rejected):
                validate_ephemeral_url(url)
    def test_mock_injected_fetch_never_issues_network_call(self):
        mock=Mock(return_value=mock_mp4())
        self.assertEqual(fetch_video_bytes(self.URL,transport=mock),mock_mp4())
        mock.assert_called_once_with(self.URL)
    def test_oversized_or_nonbytes_rejected(self):
        with self.assertRaises(Rejected):
            fetch_video_bytes(self.URL,transport=lambda _: "notbytes")
    def test_archive_atomic_and_immutable(self):
        mp4=mock_mp4()
        dest=self.folder/"three-scene-01.mp4"
        out=archive_provider_result(self.URL,dest,transport=lambda _:mp4,
             verifier=lambda _:{"codec":"h264","duration_seconds":5,
                                "width":1280,"height":720})
        self.assertEqual(out["sha256"],hashlib.sha256(mp4).hexdigest())
        self.assertEqual(dest.read_bytes(),mp4)
        self.assertFalse(out["publication_approved"])
        with self.assertRaises(Rejected):
            archive_provider_result(self.URL,dest,transport=lambda _:mp4,
                 verifier=lambda _:{"duration_seconds":5})
    def test_invalid_media_not_archived(self):
        dest=self.folder/"bad.mp4"
        with self.assertRaises(Rejected):
            archive_provider_result(self.URL,dest,transport=lambda _:b"not an mp4",
                verifier=lambda _:{"duration_seconds":5})
        self.assertFalse(dest.exists())
    def test_ffprobe_failure_blocks_acceptance(self):
        failed=subprocess.CompletedProcess(args=[],returncode=1,stdout="",stderr="")
        with self.assertRaises(Rejected):
            ffprobe_clip(self.folder/"not-video.mp4",runner=lambda *a,**k:failed)
    def test_ffprobe_duration_bounds(self):
        runner=lambda *a,**kw:subprocess.CompletedProcess(
            args=[],returncode=0,stderr="",stdout=json.dumps({
                "format":{"duration":"9999.0"},
                "streams":[{"codec_type":"video","codec_name":"h264",
                            "width":1280,"height":720}]}))
        with self.assertRaises(Rejected):
            ffprobe_clip(self.folder/"video.mp4",runner=runner)

if __name__=="__main__":
    unittest.main(verbosity=2)
