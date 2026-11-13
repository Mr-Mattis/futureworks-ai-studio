#!/usr/bin/env python3
"""Offline terminal-result validation. No network, execution, or file mutation."""
import argparse
import hashlib
import importlib.util
import json
import math
import re
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST_DIR = Path('/home/mattis983/futureworks-studio/futureworks-ai-studio/contracts/production-manifest/v1.0.0')


def load_json(path):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('Duplicate JSON key: ' + k)
            out[k] = v
        return out
    def reject(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs, parse_constant=reject)


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        return False
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return True


def validate(result, manifest_path=None, manifest_dir=DEFAULT_MANIFEST_DIR):
    schema = load_json(ROOT / 'agent_result.schema.json')
    Draft202012Validator.check_schema(schema)
    errors = [f'{"/".join(map(str, e.absolute_path)) or "root"}: {e.message}'
              for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(result)]
    if not finite(result):
        errors.append('JSON numbers must be finite')
    if errors:
        return sorted(errors)
    registry = {a['key']: a for a in load_json(ROOT / 'agent-registry.json')}
    agent = result['agent']
    if agent['instance_id'] != registry[agent['role']]['id']:
        errors.append('Agent instance_id does not match the inspected role registry')
    execution = result['execution']
    try:
        timestamps = [execution[k] for k in ('started_at', 'finished_at')]
        if any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', t) for t in timestamps):
            raise ValueError('Expected RFC3339 date-time with timezone')
        start, end = (datetime.fromisoformat(t.replace('Z', '+00:00')) for t in timestamps)
    except ValueError as exc:
        return errors + ['Invalid execution timestamp: ' + str(exc)]
    if end < start:
        errors.append('finished_at precedes started_at')
    findings = result['validation']['findings']
    if result['validation']['status'] == 'failed' and not any(f['severity'] == 'error' for f in findings):
        errors.append('Failed validation requires an error finding')
    if result['validation']['status'] == 'not_run' and findings:
        errors.append('Unperformed validation cannot contain findings')
    if result['scope'] == 'studio':
        if manifest_path is not None:
            errors.append('Studio scope cannot silently ignore a supplied manifest')
        return errors
    if manifest_path is None:
        return errors + ['Episode results require the exact input manifest file']
    try:
        manifest_dir = Path(manifest_dir)
        # Pin existing P01.01 code and schema; never fetch a remote schema.
        deps = load_json(ROOT / 'manifest-dependency.json')
        for name, expected in deps['sha256'].items():
            if hashlib.sha256((manifest_dir / name).read_bytes()).hexdigest() != expected:
                return errors + ['P01.01 dependency checksum mismatch: ' + name]
        manifest = load_json(manifest_path)
        ms = load_json(manifest_dir / 'production_manifest.schema.json')
        Draft202012Validator.check_schema(ms)
        spec = importlib.util.spec_from_file_location('p0101_manifest_validator', manifest_dir / 'validate_manifest.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            manifest_errors = module.validate(ms, manifest)
        except (KeyError, TypeError, ValueError) as exc:
            manifest_errors = ['P01.01 validator could not accept manifest: ' + str(exc)]
        if manifest_errors:
            return errors + ['Input manifest: ' + e for e in manifest_errors]
        ref = result['input_manifest']
        for key in ('schema_version', 'project_id', 'revision'):
            if ref[key] != manifest[key]:
                errors.append('Input manifest mismatch: ' + key)
        if ref['sha256'] != hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest():
            errors.append('Input manifest checksum mismatch (hash exact file bytes)')
        scene_ids = {s['scene_id'] for s in manifest['scenes']}
        def references(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    if k == 'scene_id' and v is not None and (not isinstance(v, str) or v not in scene_ids):
                        errors.append('Unknown input scene_id: ' + str(v))
                    if k == 'project_id' and v != manifest['project_id']:
                        errors.append('Output project_id does not match input manifest')
                    references(v)
            elif isinstance(value, list):
                for item in value:
                    references(item)
        references(result['output'])
        references(findings)
    except (OSError, ValueError) as exc:
        errors.append('Cannot validate manifest dependency: ' + str(exc))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result')
    parser.add_argument('--manifest')
    parser.add_argument('--manifest-dir', type=Path, default=DEFAULT_MANIFEST_DIR)
    args = parser.parse_args()
    try:
        errors = validate(load_json(args.result), args.manifest, args.manifest_dir)
    except (OSError, ValueError) as exc:
        print('ERROR:', exc)
        return 2
    if errors:
        print('FAIL:', args.result)
        for error in errors:
            print(' -', error)
        return 1
    print('PASS:', args.result)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
