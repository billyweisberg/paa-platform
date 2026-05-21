from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.automation.run_delivery_architect_component_spec_proof import (
    AssignmentValidationError,
    ParsedAssignment,
    ProofStageResult,
    build_result_packet,
    parse_assignment,
)


class DeliveryArchitectProofRunnerTests(unittest.TestCase):
    def test_parse_assignment_rejects_wrong_assignment_type(self) -> None:
        payload = {
            "message_id": "m1",
            "schema_type": "techlead_assignment_packet",
            "schema_version": "1.0.0",
            "project": "paa-platform",
            "from_role": "techlead",
            "to_role": "delivery-architect",
            "created_at": "2026-05-20T00:00:00Z",
            "correlation_id": "c1",
            "github_context": {},
            "authority_context": {},
            "payload": {
                "assignment_type": "wrong",
                "issue": {},
                "branch": {},
                "target_component": {"component_name": "WorkflowLifecycleService"},
                "target_authority_doc": {"path": __file__, "doc_id": "x", "doc_type": "component-spec"},
                "authority_docs": [__file__],
                "expected_materializer": {"script_path": __file__, "mode": "doc_driven_materialize_from_spec", "reconciliation_scope": []},
                "expected_proof_commands": ["echo ok"],
                "deliverable_requirements": {},
                "source_assignment_context": {},
            },
        }
        with self.assertRaises(AssignmentValidationError):
            parse_assignment(payload)

    def test_build_result_packet_assign_worker_on_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            spec = base / "spec.md"
            materializer = base / "mat.py"
            authority = base / "authority.md"
            spec.write_text("x")
            materializer.write_text("x")
            authority.write_text("x")
            assignment = parse_assignment(
                {
                    "message_id": "m1",
                    "schema_type": "techlead_assignment_packet",
                    "schema_version": "1.0.0",
                    "project": "paa-platform",
                    "from_role": "techlead",
                    "to_role": "delivery-architect",
                    "created_at": "2026-05-20T00:00:00Z",
                    "correlation_id": "c1",
                    "github_context": {},
                    "authority_context": {},
                    "payload": {
                        "assignment_type": "component_spec_materialization_proof",
                        "issue": {"number": 1},
                        "branch": {"canonical_branch": "issue-1", "role_branch": "issue-1-delivery"},
                        "target_component": {"component_name": "WorkflowLifecycleService", "component_kind": "service", "alignment_state": "aligned", "target_repo": "paa-platform"},
                        "target_authority_doc": {"path": str(spec), "doc_id": "doc1", "doc_type": "component-spec"},
                        "authority_docs": [str(authority)],
                        "expected_materializer": {"script_path": str(materializer), "mode": "doc_driven_materialize_from_spec", "reconciliation_scope": ["components"]},
                        "expected_proof_commands": ["echo ok"],
                        "deliverable_requirements": {},
                        "source_assignment_context": {},
                    },
                }
            )
            proof_results = {
                "governed_doc_lint": ProofStageResult("pass", "cmd1", (), (), ()),
                "materializer_run": ProofStageResult("pass", "cmd2", (), (), ()),
                "model_code_consistency": ProofStageResult("pass", "cmd3", (), (), ()),
                "spec_model_consistency": ProofStageResult("pass", "cmd4", (), (), ()),
            }
            packet = build_result_packet(assignment, proof_results=proof_results, spec_model_payload=None, materializer_notes=(), dry_run=False)
            self.assertEqual(packet["schema_type"], "delivery_review_packet")
            self.assertEqual(packet["payload"]["result_type"], "proof_pass_ready_for_dev")
            self.assertEqual(packet["payload"]["techlead_action_recommended"], "assign_worker")


if __name__ == "__main__":
    unittest.main()
