"""P05.05 expiring-result preservation, NO provider task creation.

Only a URL from an already-authenticated, externally owner-authorized task
receipt may be downloaded. This module never asks Runway to generate media.
Designed for mock transport testing now and separately gated deployment later.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

from engine import Rejected, MAX_BYTES, sha, RunwayWire, REPO

ALLOWED_OUTPUT_DOMAINS = ("cloudfront.net", "runwayml.com")
MIN_OUTPUT_BYTES = 32


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Rejected("Redirects from signed video URLs require independent revalidation")


def validate_ephemeral_url(url):
    if not isinstance(url,str) or len(url) > 8192:
        raise Rejected("Malformed temporary media URL")
    p=urlsplit(url)
    if p.scheme != "https" or p.username or p.password or p.port not in (None,443):
        raise Rejected("Only HTTPS signed media allowed")
    host=(p.hostname or "").lower()
    if not host or not any(host == suffix or host.endswith("."+suffix)
                           for suffix in ALLOWED_OUTPUT_DOMAINS):
        raise Rejected("Output host is outside the reviewed provider domain set")
    if host in ("cloudfront.net","runwayml.com"):
        raise Rejected("Bare provider domain not a media endpoint")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise Rejected("Raw IP media destinations forbidden")
    if not p.path or p.fragment:
        raise Rejected("Missing signed media path or unexpected fragment")
    return url


def fetch_video_bytes(url, *, transport=None):
    """No automatic retries: signed URLs may expire and redirects are forbidden."""
    validate_ephemeral_url(url)
    if transport is not None:
        result=transport(url)
        if not isinstance(result, bytes) or len(result) > MAX_BYTES:
            raise Rejected("Mock transport returned invalid or oversized data")
        return result
    opener=build_opener(HTTPHandler(),HTTPSHandler(),NoRedirect())
    req=Request(url,headers={"User-Agent":"FutureWorks-Development-Asset-Preservation/1"})
    try:
        with opener.open(req,timeout=45) as response:
            if response.status != 200:
                raise Rejected("Temporary URL did not return HTTP 200")
            content_type=response.headers.get("Content-Type","")
            if "video/" not in content_type and "application/octet-stream" not in content_type:
                raise Rejected("Provider response is not video media")
            data=response.read(MAX_BYTES+1)
    except (HTTPError,URLError,TimeoutError) as exc:
        raise Rejected("Media download failed; task requires reconciliation") from exc
    if len(data)>MAX_BYTES:
        raise Rejected("Output exceeds configured size cap")
    return data


def ffprobe_clip(filepath, *, runner=subprocess.run):
    result=runner(["/usr/bin/ffprobe","-v","error","-show_entries",
                   "format=duration:stream=codec_type,codec_name,width,height",
                   "-of","json",str(filepath)],
                  capture_output=True,text=True,timeout=20)
    if result.returncode:
        raise Rejected("Media is not decodable by ffprobe")
    try:
        info=json.loads(result.stdout)
        duration=float(info["format"]["duration"])
        tracks=[s for s in info.get("streams",[]) if s.get("codec_type")=="video"]
    except (KeyError,ValueError,TypeError) as exc:
        raise Rejected("Media metadata is invalid") from exc
    if not (2<=duration<=31) or len(tracks)!=1:
        raise Rejected("Unexpected duration or track count")
    width,height=tracks[0].get("width",0),tracks[0].get("height",0)
    if not (320<=width<=4096 and 240<=height<=4096):
        raise Rejected("Video dimensions outside accepted range")
    return {"duration_seconds":duration,"codec":tracks[0]["codec_name"],
            "width":width,"height":height}


def archive_provider_result(task_receipt, task_id, output_path, *, transport=None,
                            verifier=ffprobe_clip):
    """Preserve exactly one verified SUCCEEDED provider task output, never an arbitrary URL.

    The caller must have obtained task_receipt via the authenticated task
    retrieval API; verification here checks identity and result shape.
    """
    status,url=RunwayWire.parse_status(task_receipt,task_id)
    if status!="SUCCEEDED" or url is None:
        raise Rejected("Only a successful, identity-matched task can be archived")
    dest=Path(output_path).resolve()
    if (dest.suffix.lower() != ".mp4" or
            dest.is_relative_to(Path("/data")) or dest.is_relative_to(REPO)):
        raise Rejected("Destination must be a dedicated non-production .mp4")
    if dest.exists():
        raise Rejected("Never replace an existing indexed clip")
    dest.parent.mkdir(parents=True,exist_ok=True)
    blob=fetch_video_bytes(url,transport=transport)
    if len(blob)<MIN_OUTPUT_BYTES or blob[4:8]!=b"ftyp":
        raise Rejected("Downloaded bytes not an MP4")
    with tempfile.NamedTemporaryFile(prefix=".fwai-",suffix=".part",
                                     dir=dest.parent,delete=False) as tmp:
        temporary=Path(tmp.name)
        tmp.write(blob)
    try:
        details=verifier(temporary)
        temporary.replace(dest)
    finally:
        temporary.unlink(missing_ok=True)
    return {"file":str(dest),"sha256":sha(blob),"bytes":len(blob),
            "verified_media":details,"source":"authenticated_runway_task_receipt",
            "publication_approved":False}
