#!/usr/bin/env python3
"""Synthetic only. Test missing-step evidence without manufacturing CI PASS."""
import unittest
from pathlib import Path
from diagnose_runner_startup import classify_job, diagnose


class RunnerEvidenceTests(unittest.TestCase):
    def test_failed_empty_steps_never_proves_code_failure(self):
        result = classify_job({'name': 'verify', 'conclusion': 'failure', 'steps': []})
        self.assertEqual(result['classification'], 'NO_STEP_EVIDENCE')

    def test_failed_null_steps_never_proves_code_failure(self):
        self.assertEqual(classify_job({'conclusion': 'failure', 'steps': None})['classification'],
                         'NO_STEP_EVIDENCE')

    def test_skipped_job_is_not_runner_failure(self):
        self.assertEqual(classify_job({'conclusion': 'skipped', 'steps': None})['classification'],
                         'SKIPPED')

    def test_actual_failed_step_is_distinguished(self):
        x = classify_job({'conclusion': 'failure', 'steps': [{'name': 'Compile', 'conclusion': 'failure'}]})
        self.assertEqual((x['classification'], x['observed_steps']), ('STEP_EVIDENCE_FAILURE', 1))

    def test_successful_synthetic_steps_are_not_build_pass(self):
        out = diagnose({'id': 12, 'conclusion': 'success'},
                       {'jobs': [{'id': 1201, 'name': 'Synthetic', 'run_id': 12, 'conclusion': 'success', 'steps': [{'name': 'test'}]}]})
        self.assertEqual(out['jobs'][0]['classification'], 'STEPS_OBSERVED_NOT_BUILD_PROOF')
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')
        self.assertEqual(out['phone']['verified_ci_gates'], 0)
        self.assertEqual(out['wear']['verified_ci_gates'], 0)
        self.assertEqual(out['run_binding'], 'VERIFIED_JOB_RUN_ID')

    def test_blob_not_found_is_missing_log_not_confirmed_infra_cause(self):
        out = diagnose({'id': 9, 'conclusion': 'failure'},
                       {'jobs': [{'id': 901, 'name': 'probe', 'run_id': 9, 'conclusion': 'failure', 'steps': []}]},
                       'HTTP 404 BlobNotFound')
        self.assertEqual(out['log_evidence'], 'UNAVAILABLE_BLOB_NOT_FOUND')
        self.assertEqual(out['root_cause'], 'UNDETERMINED')
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')

    def test_powershell_dashboard_has_distinct_fail_closed_phone_wear_bars(self):
        script = Path(__file__).with_name('Show-EClock-CI.ps1').read_text(encoding='utf-8')
        self.assertIn("Show-GateBar 'Telefon'", script)
        self.assertIn("Show-GateBar 'Wear OS'", script)
        self.assertIn("$verified -ne 0", script)
        self.assertIn("$e.product_build_result -ne 'NOT_VERIFIED'", script)
        self.assertIn('-ForegroundColor', script)
        self.assertIn("$e.run_binding -eq 'NO_JOB_EVIDENCE'", script)
        self.assertIn("$e.job_count -ne 0", script)
        self.assertIn("NOT ASSESSED (no jobs observed)", script)
        self.assertIn('RUN ID MATCH', script)
        self.assertIn('Job ID AUDIT', script)
        self.assertIn('Duplicate job ID', script)
        self.assertIn('$job.job_id', script)

    def test_cross_run_success_job_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'run_id'):
            diagnose({'id': 100, 'conclusion': 'failure'},
                     {'jobs': [{'id': 1001, 'run_id': 101, 'name': 'other-run', 'conclusion': 'success',
                                'steps': [{'name': 'unrelated'}]}]})

    def test_missing_job_run_id_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'run_id'):
            diagnose({'id': 100}, {'jobs': [{'id': 1002, 'name': 'unknown', 'conclusion': 'failure', 'steps': []}]})

    def test_string_and_boolean_job_run_ids_fail_closed(self):
        for wrong in ('100', True, None):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'run_id'):
                diagnose({'id': 100}, {'jobs': [{'id': 1003, 'run_id': wrong, 'conclusion': 'failure', 'steps': []}]})

    def test_invalid_workflow_run_id_fails_closed(self):
        for wrong in (None, '100', True, -1):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'run ID'):
                diagnose({'id': wrong}, {'jobs': []})

    def test_matching_multiple_jobs_retains_evidence_only_status(self):
        out = diagnose({'id': 100, 'conclusion': 'failure'},
                       {'jobs': [{'id': 1004, 'run_id': 100, 'name': 'probe', 'conclusion': 'failure', 'steps': None},
                                 {'id': 1005, 'run_id': 100, 'name': 'verify', 'conclusion': 'skipped', 'steps': None}]})
        self.assertEqual(out['run_binding'], 'VERIFIED_JOB_RUN_ID')
        self.assertEqual([j['classification'] for j in out['jobs']],
                         ['NO_STEP_EVIDENCE', 'SKIPPED'])
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')

    def test_queued_run_without_jobs_is_not_identity_verified(self):
        out = diagnose({'id': 43095684765, 'status': 'queued', 'conclusion': None},
                       {'jobs': []})
        self.assertEqual(out['run_status'], 'queued')
        self.assertEqual(out['job_count'], 0)
        self.assertEqual(out['run_binding'], 'NO_JOB_EVIDENCE')
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')
        self.assertEqual(out['phone']['verified_ci_gates'], 0)
        self.assertEqual(out['wear']['verified_ci_gates'], 0)

    def test_completed_run_without_jobs_is_not_identity_verified(self):
        out = diagnose({'id': 73, 'status': 'completed', 'conclusion': 'failure'},
                       {'jobs': []}, 'HTTP 404 BlobNotFound')
        self.assertEqual(out['run_binding'], 'NO_JOB_EVIDENCE')
        self.assertEqual(out['root_cause'], 'UNDETERMINED')
        self.assertEqual(out['log_evidence'], 'UNAVAILABLE_BLOB_NOT_FOUND')

    def test_nonempty_matching_jobs_remain_verified(self):
        out = diagnose({'id': 74, 'status': 'in_progress'},
                       {'jobs': [{'id': 7401, 'run_id': 74, 'name': 'setup', 'steps': [], 'conclusion': None}]})
        self.assertEqual(out['run_binding'], 'VERIFIED_JOB_RUN_ID')
        self.assertEqual(out['job_count'], 1)
        self.assertEqual(out['run_status'], 'in_progress')
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')

    def test_duplicate_job_ids_fail_closed_even_if_job_names_differ(self):
        jobs = {'jobs': [
            {'id': 712, 'run_id': 70, 'name': 'probe', 'conclusion': 'success', 'steps': [{'name': 'setup'}]},
            {'id': 712, 'run_id': 70, 'name': 'verify', 'conclusion': 'failure', 'steps': []},
        ]}
        with self.assertRaisesRegex(ValueError, 'duplicate job id'):
            diagnose({'id': 70, 'status': 'completed'}, jobs)

    def test_missing_and_bad_job_ids_fail_closed(self):
        for bad_id in (None, True, '710', 0, -10, 7.5):
            with self.subTest(bad_id=bad_id), self.assertRaisesRegex(ValueError, 'job id'):
                diagnose({'id': 70}, {'jobs': [{'id': bad_id, 'run_id': 70, 'steps': []}]})
        with self.assertRaisesRegex(ValueError, 'job id'):
            diagnose({'id': 70}, {'jobs': [{'run_id': 70, 'steps': []}]})

    def test_distinct_job_ids_same_name_are_valid_but_not_build_pass(self):
        out = diagnose({'id': 70, 'status': 'completed', 'conclusion': 'success'},
                       {'jobs': [
                           {'id': 711, 'run_id': 70, 'name': 'verify', 'conclusion': 'success', 'steps': []},
                           {'id': 712, 'run_id': 70, 'name': 'verify', 'conclusion': 'skipped', 'steps': None},
                       ]})
        self.assertEqual([j['job_id'] for j in out['jobs']], [711, 712])
        self.assertEqual(out['run_binding'], 'VERIFIED_JOB_RUN_ID')
        self.assertEqual(out['job_count'], 2)
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')

    def test_no_job_evidence_stays_unchanged_after_identity_hardening(self):
        out = diagnose({'id': 70, 'status': 'queued', 'conclusion': None}, {'jobs': []})
        self.assertEqual(out['run_binding'], 'NO_JOB_EVIDENCE')
        self.assertEqual(out['job_count'], 0)
        self.assertEqual(out['phone']['verified_ci_gates'], 0)
        self.assertEqual(out['wear']['verified_ci_gates'], 0)

    def test_input_schema_rejected(self):
        with self.assertRaises(ValueError):
            diagnose({}, {'jobs': 'not-array'})
        with self.assertRaises(ValueError):
            classify_job('not-a-job')


if __name__ == '__main__':
    unittest.main()
