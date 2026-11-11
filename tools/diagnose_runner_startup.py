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
    return {'job_id': job.get('id'), 'name': str(job.get('name') or '(unnamed)'),
            'conclusion': conclusion if isinstance(conclusion, str) else 'unknown',
            'classification': status, 'observed_steps': len(steps) if isinstance(steps, list) else 0}


def diagnose(run, jobs, log_error=''):
    if not isinstance(run, dict) or not isinstance(jobs, dict) or not isinstance(jobs.get('jobs'), list):
        raise ValueError('run must be an object and jobs must contain a jobs array')
    # A job list from another workflow run could silently contaminate evidence.
    # GitHub's jobs API includes run_id for each job. Reject missing or mismatched
    # bindings rather than interpreting unrelated jobs as evidence for this run.
    run_id = run.get('id')
    if type(run_id) is not int or run_id <= 0:
        raise ValueError('workflow run ID must be a positive integer')
    seen_job_ids = set()
    for job in jobs['jobs']:
        if not isinstance(job, dict) or type(job.get('run_id')) is not int or job['run_id'] != run_id:
            raise ValueError('job run_id missing or different from workflow run ID')
        job_id = job.get('id')
        if type(job_id) is not int or job_id <= 0:
            raise ValueError('job id must be a positive integer')
        if job_id in seen_job_ids:
            raise ValueError('duplicate job id in workflow run evidence')
        seen_job_ids.add(job_id)
    found = [classify_job(job) for job in jobs['jobs']]
    # No jobs means no identity pairs exist to verify (vacuous truth is not evidence).
    binding = 'VERIFIED_JOB_RUN_ID' if found else 'NO_JOB_EVIDENCE'
    return {'run_id': run_id, 'run_binding': binding,
            'run_status': run.get('status', 'unknown'),
            'run_conclusion': run.get('conclusion', 'unknown'),
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
