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
                       {'jobs': [{'name': 'Synthetic', 'conclusion': 'success', 'steps': [{'name': 'test'}]}]})
        self.assertEqual(out['jobs'][0]['classification'], 'STEPS_OBSERVED_NOT_BUILD_PROOF')
        self.assertEqual(out['product_build_result'], 'NOT_VERIFIED')
        self.assertEqual(out['phone']['verified_ci_gates'], 0)
        self.assertEqual(out['wear']['verified_ci_gates'], 0)

    def test_blob_not_found_is_missing_log_not_confirmed_infra_cause(self):
        out = diagnose({'id': 9, 'conclusion': 'failure'},
                       {'jobs': [{'name': 'probe', 'conclusion': 'failure', 'steps': []}]},
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

    def test_input_schema_rejected(self):
        with self.assertRaises(ValueError):
            diagnose({}, {'jobs': 'not-array'})
        with self.assertRaises(ValueError):
            classify_job('not-a-job')


if __name__ == '__main__':
    unittest.main()
