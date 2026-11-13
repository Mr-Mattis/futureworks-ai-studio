"""FutureWorks Studio V1: single-worker production API using only Python stdlib + FFmpeg.

Designed for a local, trusted Docker network. Never publish port 8000.
Jobs are persisted as JSON. Running jobs on abrupt restart are marked
'needs_review' (not retried) to avoid double-billing paid providers.
"""
from __future__ import annotations
import datetime as dt
import json
import logging
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request
import zipfile

ROOT = Path('/data/output')
ASSETS = Path('/data/assets')
JOB_QUEUE: queue.Queue[str] = queue.Queue()
LOCK = threading.Lock()
FPS = 24
SCENE_RATE_USD = 0.12  # Runway gen4.5, 12 credits/sec x $0.01/credit (2026-11)
LOG = logging.getLogger('futureworks')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run(*args):
    cmd = [str(a) for a in args]
    LOG.info('ffmpeg/ffprobe: %s', ' '.join(cmd[:6]))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-2000:])
    return p.stdout.strip()


def duration(path: Path) -> float:
    return float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', path))


def api_json(url, payload=None, headers=None, timeout=90):
    hdr = {'Content-Type': 'application/json', **(headers or {})}
    b = None if payload is None else json.dumps(payload).encode()
    req = request.Request(url, data=b, headers=hdr,
                          method='GET' if payload is None else 'POST')
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except error.HTTPError as exc:
        details = exc.read(1500).decode(errors='replace')
        raise RuntimeError(f'{url}: HTTP {exc.code}: {details}') from exc


def api_bytes(url, payload, headers=None, timeout=120):
    req = request.Request(url, data=json.dumps(payload).encode(),
                          headers={'Content-Type': 'application/json', **(headers or {})},
                          method='POST')
    try:
        with request.urlopen(req, timeout=timeout) as res:
            return res.read()
    except error.HTTPError as exc:
        raise RuntimeError(f'HTTP {exc.code}: {exc.read(1500).decode(errors="replace")}') from exc


def download(url, path):
    # URLs come from provider APIs, not user supplied in the job body.
    if not str(url).startswith('https://'):
        raise ValueError('Provider returned a non-HTTPS download URL')
    req = request.Request(url, headers={'User-Agent': 'FutureWorks/1.0'})
    with request.urlopen(req, timeout=120) as source, open(path, 'wb') as output:
        shutil.copyfileobj(source, output)
    if path.stat().st_size == 0:
        raise RuntimeError('Empty asset downloaded')


def path_for(job_id):
    if not re.fullmatch(r'[a-f0-9]{12}', job_id):
        raise ValueError('Invalid job ID')
    return ROOT / job_id


def store(job):
    path = path_for(job['id']) / 'job.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, indent=2), encoding='utf-8')


def load(job_id):
    p = path_for(job_id) / 'job.json'
    if not p.exists():
        raise FileNotFoundError(job_id)
    return json.loads(p.read_text(encoding='utf-8'))


def set_stage(job, stage):
    job['stage'] = stage
    job['updated_at'] = now()
    store(job)


def make_dry_plan(job):
    label = job['prompt'].strip().rstrip('.')
    scenes = []
    for idx in range(job['scene_count']):
        scenes.append({
            'title': f'Concept scene {idx + 1}',
            'visual_prompt': f'{label}. Cinematic realistic engineering studio. Shot {idx+1}. No text overlays.',
            'narration': f'Concept preview, scene {idx + 1}. This footage is a simulation.'
        })
    return {'title': label[:110], 'avatar_intro': 'Welcome to FutureWorks. Today we explore an original build concept.',
            'scenes': scenes, 'disclosure': 'AI-generated concept demonstration; not a physical build.'}


def make_live_plan(job):
    key = os.getenv('OPENAI_API_KEY', '')
    if not key:
        raise RuntimeError('OPENAI_API_KEY is required for live scripts')
    prompt = ('Return ONLY a JSON object with keys: title, avatar_intro, scenes, disclosure. '
              f'Provide EXACTLY {job["scene_count"]} scenes, each having title, visual_prompt, narration. '
              'Each narration must be 8-12 spoken words for a five-second scene. '
              'Use photorealistic cinematic visuals; never claim simulated builds were physically constructed. '
              'Avoid trademarked characters and brands. This is a clearly labeled AI concept. '
              f'Video brief: {job["prompt"]}')
    data = api_json('https://api.openai.com/v1/chat/completions', {
        'model': os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'),
        'messages': [{'role': 'system', 'content': 'You are a precise storyboard editor. Reply in valid JSON.'},
                     {'role': 'user', 'content': prompt}],
        'response_format': {'type': 'json_object'}, 'temperature': 0.6,
    }, {'Authorization': f'Bearer {key}'})
    parsed = json.loads(data['choices'][0]['message']['content'])
    if len(parsed.get('scenes', [])) != job['scene_count']:
        raise RuntimeError('Unexpected number of scenes from script model')
    for item in parsed['scenes']:
        if not all(item.get(k) for k in ('title', 'visual_prompt', 'narration')):
            raise RuntimeError('Incomplete script scene')
    return parsed


def create_dry_video(dst: Path, title: str, seconds: int):
    """Creates a real playable placeholder, no credits/credentials needed."""
    txt = dst.with_suffix('.txt')
    txt.write_text(title[:75].replace('\n', ' '), encoding='utf-8')
    # No UI labels to distort; render a clearly fake placeholder.
    vf = (f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
          f"textfile={txt}:fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2")
    run('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi',
        '-i', f'color=c=0x14213b:s=1280x720:r={FPS}', '-t', seconds,
        '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p', '-r', FPS, dst)
    txt.unlink(missing_ok=True)


def make_silence(path: Path, secs: int):
    run('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi',
        '-i', 'anullsrc=r=48000:cl=stereo', '-t', secs,
        '-c:a', 'pcm_s16le', path)


def speak(text, dst: Path):
    key = os.getenv('ELEVENLABS_API_KEY', '')
    voice = os.getenv('ELEVENLABS_VOICE_ID', '')
    if not key or not voice:
        raise RuntimeError('ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID required')
    audio = api_bytes(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}',
                      {'text': text, 'model_id': 'eleven_multilingual_v2'},
                      {'xi-api-key': key})
    dst.write_bytes(audio)


def runway_video(prompt, seconds, dst):
    secret = os.getenv('RUNWAYML_API_SECRET', '')
    if not secret:
        raise RuntimeError('RUNWAYML_API_SECRET required')
    headers = {'Authorization': f'Bearer {secret}', 'X-Runway-Version': '2024-11-06'}
    task = api_json('https://api.dev.runwayml.com/v1/text_to_video',
        {'model': 'gen4.5', 'promptText': prompt[:1000], 'ratio': '1280:720', 'duration': seconds},
        headers)
    tid = task['id']
    LOG.info('Runway task: %s', tid)
    for _ in range(180):
        time.sleep(10)
        data = api_json(f'https://api.dev.runwayml.com/v1/tasks/{tid}', headers=headers)
        if data.get('status') == 'SUCCEEDED':
            download(data['output'][0], dst)
            return
        if data.get('status') in ('FAILED', 'CANCELED'):
            raise RuntimeError(f'Runway failed: {data}')
    raise TimeoutError('Runway job exceeded 30 minutes; inspect provider task before retry')


def heygen_avatar(script, dst):
    key = os.getenv('HEYGEN_API_KEY', '')
    avatar = os.getenv('HEYGEN_AVATAR_ID', '')
    voice = os.getenv('HEYGEN_VOICE_ID', '')
    if not all((key, avatar, voice)):
        raise RuntimeError('HEYGEN_API_KEY, HEYGEN_AVATAR_ID, HEYGEN_VOICE_ID are required')
    headers = {'x-api-key': key}
    task = api_json('https://api.heygen.com/v3/videos', {
        'type': 'avatar', 'avatar_id': avatar, 'script': script,
        'voice_id': voice, 'title': 'FutureWorks Introduction',
        'resolution': '1080p', 'aspect_ratio': '16:9',
    }, headers)
    task_id = task['data']['video_id']
    LOG.info('HeyGen task: %s', task_id)
    for _ in range(180):
        time.sleep(10)
        data = api_json(f'https://api.heygen.com/v3/videos/{task_id}', headers=headers)['data']
        if data.get('status') == 'completed':
            download(data['video_url'], dst)
            return
        if data.get('status') == 'failed':
            raise RuntimeError(f'HeyGen failed: {data.get("failure_message")}')
    raise TimeoutError('HeyGen job exceeded 30 minutes; inspect provider task before retry')


def normalize_video(src, dst, seconds):
    # Freeze the last video frame if narration runs past the generated clip.
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', src,
        '-vf', f'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={seconds+1}',
        '-t', f'{seconds:.3f}', '-an', '-c:v', 'libx264', '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p', '-r', FPS, dst)


def normalize_audio(src, dst, seconds):
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', src,
        '-af', 'apad', '-t', f'{seconds:.3f}', '-ar', '48000', '-ac', '2',
        '-c:a', 'pcm_s16le', dst)


def make_segment(video, audio, out, seconds):
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', audio,
        '-t', f'{seconds:.3f}', '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
        '-r', FPS, '-c:a', 'aac', '-ar', '48000', '-ac', '2', out)


def ot_time(frames):
    return {'OTIO_SCHEMA': 'RationalTime.1', 'value': int(frames), 'rate': float(FPS)}


def ot_range(frames):
    return {'OTIO_SCHEMA': 'TimeRange.1', 'start_time': ot_time(0), 'duration': ot_time(frames)}


def ot_clip(name, path, frames):
    return {'OTIO_SCHEMA': 'Clip.1', 'name': name, 'metadata': {},
            'source_range': ot_range(frames), 'effects': [], 'markers': [],
            'media_reference': {'OTIO_SCHEMA': 'ExternalReference.1',
                                'name': path.name, 'target_url': f'media/{path.name}',
                                'available_range': ot_range(frames), 'metadata': {}}}


def ot_track(kind, clips):
    return {'OTIO_SCHEMA': 'Track.1', 'name': f'{kind} 1', 'kind': kind,
            'source_range': None, 'effects': [], 'markers': [], 'metadata': {}, 'children': clips}


def export_otioz(rows, target):
    # All media are already exactly the same timeline duration. One clip per scene.
    videos, audios = [], []
    for r in rows:
        frames = round(r['seconds'] * FPS)
        videos.append(ot_clip(r['name'], r['video'], frames))
        audios.append(ot_clip(r['name'] + ' narration', r['audio'], frames))
    obj = {'OTIO_SCHEMA': 'Timeline.1', 'name': 'FutureWorks rough cut',
           'metadata': {}, 'global_start_time': ot_time(0),
           'tracks': {'OTIO_SCHEMA': 'Stack.1', 'name': 'Tracks', 'metadata': {},
                      'source_range': None, 'effects': [], 'markers': [],
                      'children': [ot_track('Video', videos), ot_track('Audio', audios)]}}
    otio_file = target.with_suffix('.otio')
    otio_file.write_text(json.dumps(obj, indent=2), encoding='utf-8')
    with zipfile.ZipFile(target, 'w') as z:
        z.writestr('version.txt', '1.0.0', compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('content.otio', json.dumps(obj), compress_type=zipfile.ZIP_DEFLATED)
        for row in rows:
            for name in ('video', 'audio'):
                path = row[name]
                z.write(path, f'media/{path.name}', compress_type=zipfile.ZIP_STORED)
    return otio_file


def job_pipeline(job):
    folder = path_for(job['id'])
    folder.mkdir(parents=True, exist_ok=True)
    for sub in ['01_Script', '02_Avatar', '03_Scenes', '04_Audio',
                '05_Editing', '06_Rough_Cut', '07_Metadata']:
        (folder / sub).mkdir(exist_ok=True)
    live = job['mode'] == 'live'
    if live:
        if os.getenv('ENABLE_PAID_GENERATION', '').lower() != 'true':
            raise RuntimeError('Paid generation disabled. Set ENABLE_PAID_GENERATION=true in .env.')
        estimate = job['scene_count'] * job['scene_duration'] * SCENE_RATE_USD
        if estimate > job['runway_budget_usd']:
            raise RuntimeError(f'Estimated Runway spend ${estimate:.2f} exceeds cap ${job["runway_budget_usd"]:.2f}.')
        required = ('OPENAI_API_KEY', 'RUNWAYML_API_SECRET', 'HEYGEN_API_KEY',
                    'HEYGEN_AVATAR_ID', 'HEYGEN_VOICE_ID',
                    'ELEVENLABS_API_KEY', 'ELEVENLABS_VOICE_ID')
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise RuntimeError(f'Missing paid provider configuration: {", ".join(missing)}')
    set_stage(job, 'writing_script')
    script = make_live_plan(job) if live else make_dry_plan(job)
    (folder / '01_Script' / 'storyboard.json').write_text(json.dumps(script, indent=2), encoding='utf-8')
    rows = []
    # Generate the avatar intro independently from scene footage.
    set_stage(job, 'generating_avatar')
    avatar_raw = folder / '02_Avatar' / 'avatar_raw.mp4'
    if live:
        heygen_avatar(script['avatar_intro'], avatar_raw)
    else:
        create_dry_video(avatar_raw, 'AVATAR PLACEHOLDER - NOT YOUR LIKENESS', 5)
    intro_audio_raw = folder / '04_Audio' / 'intro_source.wav'
    if live:
        run('ffmpeg', '-y', '-loglevel', 'error', '-i', avatar_raw,
            '-vn', '-c:a', 'pcm_s16le', intro_audio_raw)
    else:
        make_silence(intro_audio_raw, 5)
    intro_seconds = max(1, math.ceil(duration(avatar_raw) * FPS) / FPS)
    intro_video = folder / '05_Editing' / 'video_00.mp4'
    intro_audio = folder / '05_Editing' / 'audio_00.wav'
    normalize_video(avatar_raw, intro_video, intro_seconds)
    normalize_audio(intro_audio_raw, intro_audio, intro_seconds)
    rows.append({'name': '00 - Avatar intro', 'video': intro_video, 'audio': intro_audio,
                 'seconds': intro_seconds})
    for index, scene in enumerate(script['scenes'], start=1):
        set_stage(job, f'generating_scene_{index}_of_{len(script["scenes"])}')
        raw = folder / '03_Scenes' / f'scene_{index:02d}_source.mp4'
        if live:
            runway_video(scene['visual_prompt'], job['scene_duration'], raw)
        else:
            create_dry_video(raw, f'SCENE {index}: {scene["title"]}', job['scene_duration'])
        set_stage(job, f'generating_voice_{index}')
        source_audio = folder / '04_Audio' / f'scene_{index:02d}.mp3'
        if live:
            speak(scene['narration'], source_audio)
        else:
            source_audio = folder / '04_Audio' / f'scene_{index:02d}.wav'
            make_silence(source_audio, job['scene_duration'])
        # Extend video with last-frame freeze if voice lasts longer.
        secs = math.ceil(max(job['scene_duration'], duration(source_audio) + (0.2 if live else 0)) * FPS) / FPS
        out_video = folder / '05_Editing' / f'video_{index:02d}.mp4'
        out_audio = folder / '05_Editing' / f'audio_{index:02d}.wav'
        normalize_video(raw, out_video, secs)
        normalize_audio(source_audio, out_audio, secs)
        rows.append({'name': f'{index:02d} - {scene["title"]}', 'video': out_video,
                     'audio': out_audio, 'seconds': secs})
    set_stage(job, 'assembling')
    segments = []
    for idx, row in enumerate(rows):
        path = folder / '06_Rough_Cut' / f'segment_{idx:02d}.mp4'
        make_segment(row['video'], row['audio'], path, row['seconds'])
        segments.append(path)
    listing = folder / '06_Rough_Cut' / 'concat.txt'
    listing.write_text(''.join(f"file '{p.name}'\n" for p in segments), encoding='utf-8')
    master = folder / '06_Rough_Cut' / 'rough_cut.mp4'
    run('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
        '-i', listing, '-c', 'copy', master)
    bundle = folder / '05_Editing' / 'FutureWorks_Edit.otioz'
    raw_otio = export_otioz(rows, bundle)
    metadata = {'title': script['title'], 'description': f"AI concept demonstration. {script['disclosure']}",
                'ai_disclosure_required_review': True, 'ready_for_upload': False}
    (folder / '07_Metadata' / 'youtube_draft.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    job['outputs'] = {'rough_cut': str(master), 'edit_bundle': str(bundle),
                      'otio_source': str(raw_otio), 'project_folder': str(folder)}
    job['status'] = 'completed'
    set_stage(job, 'ready_for_manual_edit')


def worker_loop():
    while True:
        job_id = JOB_QUEUE.get()
        try:
            job = load(job_id)
            if job['status'] != 'queued':
                continue
            job['status'] = 'running'
            set_stage(job, 'starting')
            try:
                job_pipeline(job)
            except Exception as exc:
                LOG.exception('Job %s failed', job_id)
                job['status'] = 'failed'
                job['error'] = str(exc)
                set_stage(job, 'failed')
        finally:
            JOB_QUEUE.task_done()


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        raw = json.dumps(data).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/health':
            return self.reply(200, {'ok': True})
        match = re.fullmatch(r'/jobs/([a-f0-9]{12})', self.path)
        if match:
            try:
                return self.reply(200, load(match.group(1)))
            except FileNotFoundError:
                return self.reply(404, {'error': 'Unknown job ID'})
        return self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path != '/jobs':
            return self.reply(404, {'error': 'Not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not (1 <= size <= 20000):
                return self.reply(413, {'error': 'Body must be 1-20000 bytes'})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('Expected JSON object')
            prompt = str(body.get('prompt', '')).strip()
            if not 8 <= len(prompt) <= 2000:
                raise ValueError('prompt must be 8-2000 characters')
            mode = str(body.get('mode', 'dry_run'))
            if mode not in ('dry_run', 'live'):
                raise ValueError('mode must be dry_run or live')
            scenes = int(body.get('scene_count', 2))
            seconds = int(body.get('scene_duration', 5))
            budget = float(body.get('runway_budget_usd', 3.0))
            if not (1 <= scenes <= 4 and seconds in (5, 10) and 0 <= budget <= 25):
                raise ValueError('scene_count 1-4; scene_duration 5 or 10; budget 0-25')
            if mode == 'live' and os.getenv('ENABLE_PAID_GENERATION', '').lower() != 'true':
                raise ValueError('Live calls disabled by server configuration')
            jid = uuid.uuid4().hex[:12]
            job = {'id': jid, 'prompt': prompt, 'mode': mode,
                   'scene_count': scenes, 'scene_duration': seconds,
                   'runway_budget_usd': budget, 'status': 'queued', 'stage': 'queued',
                   'created_at': now(), 'updated_at': now(), 'outputs': {}}
            with LOCK:
                store(job)
                JOB_QUEUE.put(jid)
            return self.reply(202, {'id': jid, 'status': 'queued',
                                    'status_path': f'/jobs/{jid}'})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.reply(400, {'error': str(exc)})


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for file in ROOT.glob('*/job.json'):
        try:
            job = json.loads(file.read_text())
            if job['status'] == 'running':
                job['status'] = 'needs_review'
                job['stage'] = 'interrupted_without_auto_retry'
                store(job)
            elif job['status'] == 'queued':
                JOB_QUEUE.put(job['id'])
        except Exception:
            LOG.exception('Could not recover job file %s', file)
    threading.Thread(target=worker_loop, daemon=True).start()
    server = ThreadingHTTPServer(('0.0.0.0', 8000), Handler)
    LOG.info('Listening internally on :8000')
    server.serve_forever()


if __name__ == '__main__':
    main()
