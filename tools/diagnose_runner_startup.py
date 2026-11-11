#!/usr/bin/env python3
"""Offline, fail-closed GitHub Actions runner-start evidence classification.

Only inspect explicitly provided public-safe job/run JSON. Does not call GitHub,
change source-approval gates, or assert that phone/Wear builds passed.
"""
import argparse
import json
from pathlib import Path


def classify_job(job):
    if not isinstance(job, dict):
        raise ValueError('job must be an object')
    conclusion = job.get('conclusion')
    steps = job.get('steps')
    if conclusion == 'skipped':
        status = 'SKIPPED'
    elif not isinstance(steps, list) or not steps:
        status = 'NO_STEP_EVIDENCE'
    elif conclusion == 'failure':
        status = 'STEP_EVIDENCE_FAILURE'
    elif conclusion == 'success':
        status = 'STEPS_OBSERVED_NOT_BUILD_PROOF'
    else:
        status = 'INCONCLUSIVE'
    return {'name': str(job.get('name') or '(unnamed)'),
            'conclusion': conclusion if isinstance(conclusion, str) else 'unknown',
            'classification': status, 'observed_steps': len(steps) if isinstance(steps, list) else 0}


def diagnose(run, jobs, log_error=''):
    if not isinstance(run, dict) or not isinstance(jobs, dict) or not isinstance(jobs.get('jobs'), list):
        raise ValueError('run must be an object and jobs must contain a jobs array')
    found = [classify_job(job) for job in jobs['jobs']]
    return {'run_id': run.get('id'), 'run_conclusion': run.get('conclusion', 'unknown'),
            'head_sha': run.get('head_sha'), 'jobs': found,
            'job_count': len(found),
            'log_evidence': 'UNAVAILABLE_BLOB_NOT_FOUND' if 'BlobNotFound' in log_error else 'NOT_ASSESSED',
            'phone': {'verified_ci_gates': 0, 'total_ci_gates': 3, 'status': 'UNVERIFIED'},
            'wear': {'verified_ci_gates': 0, 'total_ci_gates': 3, 'status': 'UNVERIFIED'},
            'product_build_result': 'NOT_VERIFIED',
            'root_cause': 'UNDETERMINED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path, help='sanitized workflow run JSON')
    parser.add_argument('--jobs', required=True, type=Path, help='sanitized jobs response JSON')
    parser.add_argument('--log-error', default='', help='optional log retrieval error code')
    args = parser.parse_args()
    result = diagnose(json.loads(args.run.read_text(encoding='utf-8')),
                      json.loads(args.jobs.read_text(encoding='utf-8')), args.log_error)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
