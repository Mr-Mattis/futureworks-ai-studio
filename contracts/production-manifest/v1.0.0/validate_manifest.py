#!/usr/bin/env python3
"""Future Works production manifest validator (schema + deterministic invariants).

Reads JSON only. Does not connect to providers, change state, or execute production jobs.
Usage: python validate_manifest.py production_manifest.schema.json example.valid.json
"""
import json
import pathlib
import sys
from collections import Counter
from jsonschema import Draft202012Validator


def validate(schema, manifest):
    errors = []
    errors.extend(f'{"/".join(map(str,e.absolute_path)) or "root"}: {e.message}'
                  for e in Draft202012Validator(schema).iter_errors(manifest))
    if errors:
        return sorted(errors)
    scenes=manifest['scenes']
    ids=[s['scene_id'] for s in scenes]
    dupe=[k for k,n in Counter(ids).items() if n>1]
    if dupe:errors.append('Duplicate scene IDs: '+', '.join(dupe))
    orders=[s['order'] for s in scenes]
    if orders!=list(range(1,len(scenes)+1)):
        errors.append('Scenes must be ordered consecutively from 1 without gaps')
    duration=sum(s['duration_seconds'] for s in scenes)
    if duration!=manifest['target_duration_seconds']:
        errors.append(f'Scene duration sum {duration} differs from target {manifest["target_duration_seconds"]}')
    asset_ids=[x['asset_id'] for x in manifest['asset_references']]
    if len(asset_ids)!=len(set(asset_ids)):errors.append('Duplicate asset IDs')
    unknown=set(x for s in scenes for x in s['asset_references'])-set(asset_ids)
    if unknown:errors.append('Unknown scene asset references: '+', '.join(sorted(unknown)))
    for a in manifest['asset_references']:
        if a['scene_id'] is not None and a['scene_id'] not in ids:
            errors.append('Asset '+a['asset_id']+' refers to unknown scene '+a['scene_id'])
        if a['status'] in ('generated','verified') and not a['file_uri']:
            errors.append('Generated/verified asset missing file_uri: '+a['asset_id'])
        if a['status']=='verified' and not a['sha256']:
            errors.append('Verified asset missing SHA-256: '+a['asset_id'])
    for s in scenes:
        for feature, needed in s['media_requirements'].items():
            if needed and not manifest['generation_plan'][feature]['enabled']:
                errors.append(f'{s["scene_id"]} requires {feature} but provider is disabled')
        if s['media_requirements']['avatar'] and not (s.get('avatar_script') or '').strip():
            errors.append(f'{s["scene_id"]} requires avatar but has no avatar_script')
    ap=manifest['approval_state']
    if ap['status']=='approved':
        if ap['approved_revision']!=manifest['revision']:
            errors.append('Approval must target this exact manifest revision')
        if not ap['approval_record_id']:
            errors.append('Approved manifest needs external approval_record_id')
    elif ap['approved_revision'] is not None or ap['approved_by'] is not None or ap['approval_record_id'] is not None:
        errors.append('Nonapproved manifest cannot carry a completed approval reference')
    if manifest['content_type'] in ('REAL_BUILD','HYBRID') and not manifest.get('source_evidence_ids'):
        errors.append('REAL_BUILD and HYBRID require recorded source evidence IDs')
    return errors


def main():
    if len(sys.argv)!=3:
        print('Usage: python validate_manifest.py SCHEMA.json MANIFEST.json',file=sys.stderr)
        return 2
    try:
        schema=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
        manifest=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        errors=validate(schema,manifest)
    except (OSError,ValueError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        return 2
    if errors:
        print('FAIL: '+pathlib.Path(sys.argv[2]).name)
        for err in errors:print(' - '+err)
        return 1
    print('PASS: '+pathlib.Path(sys.argv[2]).name)
    return 0

if __name__=='__main__':sys.exit(main())
