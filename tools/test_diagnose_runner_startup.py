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
                       {'jobs': [{'name': 'Synthetic', 'run_id': 12, 'conclusion': 'success', 'steps': [{'name': 'test'}]}]})
        self.assertEqual(out['jobs'][0]['classification'], 'STEPS_OBSERVED_NOT_BUILD_PROOF')
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')
        self.assertEqual(out['phone']['verified_ci_gates'], 0)
        self.assertEqual(out['wear']['verified_ci_gates'], 0)
        self.assertEqual(out['run_binding'], 'VERIFIED_JOB_RUN_ID')

    def test_blob_not_found_is_missing_log_not_confirmed_infra_cause(self):
        out = diagnose({'id': 9, 'conclusion': 'failure'},
                       {'jobs': [{'name': 'probe', 'run_id': 9, 'conclusion': 'failure', 'steps': []}]},
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
        self.assertIn("$e.run_binding -ne 'VERIFIED_JOB_RUN_ID'", script)
        self.assertIn('RUN ID MATCH', script)

    def test_cross_run_success_job_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'run_id'):
            diagnose({'id': 100, 'conclusion': 'failure'},
                     {'jobs': [{'run_id': 101, 'name': 'other-run', 'conclusion': 'success',
                                'steps': [{'name': 'unrelated'}]}]})

    def test_missing_job_run_id_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'run_id'):
            diagnose({'id': 100}, {'jobs': [{'name': 'unknown', 'conclusion': 'failure', 'steps': []}]})

    def test_string_and_boolean_job_run_ids_fail_closed(self):
        for wrong in ('100', True, None):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'run_id'):
                diagnose({'id': 100}, {'jobs': [{'run_id': wrong, 'conclusion': 'failure', 'steps': []}]})

    def test_invalid_workflow_run_id_fails_closed(self):
        for wrong in (None, '100', True, -1):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'run ID'):
                diagnose({'id': wrong}, {'jobs': []})

    def test_matching_multiple_jobs_retains_evidence_only_status(self):
        out = diagnose({'id': 100, 'conclusion': 'failure'},
                       {'jobs': [{'run_id': 100, 'name': 'probe', 'conclusion': 'failure', 'steps': None},
                                 {'run_id': 100, 'name': 'verify', 'conclusion': 'skipped', 'steps': None}]})
        self.assertEqual(out['run_binding'], 'VERIFIED_JOB_RUN_ID')
        self.assertEqual([j['classification'] for j in out['jobs']],
                         ['NO_STEP_EVIDENCE', 'SKIPPED'])
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')

    def test_input_schema_rejected(self):
        with self.assertRaises(ValueError):
            diagnose({}, {'jobs': 'not-array'})
        with self.assertRaises(ValueError):
            classify_job('not-a-job')


if __name__ == '__main__':
    unittest.main()
