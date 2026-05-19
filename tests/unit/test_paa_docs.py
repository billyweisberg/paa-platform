from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.docs import paa_docs


VALID_DOC = """Title: Workflow Lifecycle Service Component Spec
Doc-ID: paa-workflow-lifecycle-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-17
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: WorkflowLifecycleService
Domain: workflow-lifecycle
Keywords: workflow, lifecycle, service
Depends-On: 2026-05-17-workflow-lifecycle-service-pre-spec.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-01
Summary: Defines the workflow lifecycle service boundary.

# Workflow Lifecycle Service Component Spec
"""

SECOND_DOC = """Title: Workflow Lifecycle Service Pre Spec
Doc-ID: paa-workflow-lifecycle-service-pre-spec
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-17
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: WorkflowLifecycleService
Domain: workflow-lifecycle
Keywords: workflow, lifecycle, prespec
Depends-On:
Supersedes:
Superseded-By:
Canonical: false
Review-After: 2026-06-01
Summary: Narrows the service before the full component spec.

# Workflow Lifecycle Service Pre Spec
"""

INVALID_DOC = """Title: Broken Header Example
Doc-ID bad-doc
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Canonical: true
Summary: Demonstrates a malformed header line.

# Broken
"""


class PaaDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "docs/2_Design").mkdir(parents=True)
        (self.root / "docs/3_Plan").mkdir(parents=True)
        (self.root / "docs/7_Monitor").mkdir(parents=True)
        (self.root / "docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md").write_text(VALID_DOC)
        (self.root / "docs/2_Design/2026-05-17-workflow-lifecycle-service-pre-spec.md").write_text(SECOND_DOC)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_parse_header_normalizes_lists_and_boolean(self) -> None:
        record, findings = paa_docs.parse_header(
            self.root / "docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md",
            self.root,
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["doc_id"], "paa-workflow-lifecycle-service-component-spec")
        self.assertEqual(record["keywords"], ["workflow", "lifecycle", "service"])
        self.assertTrue(record["canonical"])
        self.assertEqual([], [finding for finding in findings if finding.severity == "error"])

    def test_build_index_reports_legacy_docs(self) -> None:
        (self.root / "docs/3_Plan/2026-05-18-legacy-note.md").write_text("# Legacy\n")
        records, findings = paa_docs.build_index(self.root)
        legacy = [record for record in records if record.get("header_status") == "legacy_missing_header"]
        self.assertEqual(1, len(legacy))
        self.assertTrue(any(finding.code == "legacy_missing_header" for finding in findings))

    def test_lint_detects_invalid_header(self) -> None:
        (self.root / "docs/2_Design/2026-05-18-bad.md").write_text(INVALID_DOC)
        records, findings = paa_docs.build_index(self.root)
        self.assertTrue(any(record.get("header_status") == "invalid_header" for record in records))
        self.assertTrue(any(finding.severity == "error" for finding in findings))

    def test_current_prefers_canonical_active_doc(self) -> None:
        records, _ = paa_docs.build_index(self.root)
        args = SimpleNamespace(
            include_legacy=False,
            doc_id=None,
            title_contains=None,
            doc_type=None,
            status=None,
            stage=None,
            component="WorkflowLifecycleService",
            domain=None,
            keyword=None,
            path_prefix=None,
            canonical=None,
        )
        current = paa_docs.current_records(records, args)
        self.assertEqual(1, len(current))
        self.assertEqual(
            "paa-workflow-lifecycle-service-component-spec",
            current[0].get("doc_id"),
        )

    def test_related_returns_same_component_docs(self) -> None:
        records, _ = paa_docs.build_index(self.root)
        payload = paa_docs.related_payload(
            records,
            SimpleNamespace(doc_id="paa-workflow-lifecycle-service-component-spec", path=None),
        )
        same_component_ids = [record.get("doc_id") for record in payload["same_component"]]
        self.assertIn("paa-workflow-lifecycle-service-pre-spec", same_component_ids)

    def test_filter_records_by_keyword(self) -> None:
        records, _ = paa_docs.build_index(self.root)
        args = SimpleNamespace(
            include_legacy=False,
            doc_id=None,
            title_contains=None,
            doc_type=None,
            status=None,
            stage=None,
            component=None,
            domain=None,
            keyword="workflow",
            path_prefix=None,
            canonical=None,
        )
        filtered = paa_docs.filter_records(records, args)
        self.assertEqual(2, len(filtered))

    def test_index_output_is_json_serializable(self) -> None:
        records, _ = paa_docs.build_index(self.root)
        json.dumps(records)

    def test_filter_findings_can_limit_to_governed_prefix(self) -> None:
        findings = [
            paa_docs.Finding("info", "legacy_missing_header", "docs/2_Design/legacy.md", "legacy"),
            paa_docs.Finding("warning", "unresolved_reference", "docs/2_Design/governed.md", "warning"),
        ]
        filtered = paa_docs.filter_findings(findings, ["docs/2_Design/governed"], include_legacy=False)
        self.assertEqual(1, len(filtered))
        self.assertEqual("unresolved_reference", filtered[0].code)

    def test_new_doc_writes_header_and_body(self) -> None:
        target = self.root / "docs/3_Plan/2026-05-18-example-plan.md"
        args = SimpleNamespace(
            path=target,
            title="Example Plan",
            doc_id="paa-example-plan",
            doc_type="plan",
            status="draft",
            stage="plan",
            created="2026-05-18",
            last_edited="2026-05-18",
            author="Billy Weisberg",
            repo="paa-platform",
            component="",
            domain="example-domain",
            keywords=["example", "plan"],
            depends_on=[],
            supersedes=[],
            superseded_by=[],
            canonical=None,
            review_after="2026-06-15",
            owners=[],
            expires="",
            issue="",
            pr="",
            authority_source="",
            implementation_status="",
            summary="Creates a governed example plan.",
            body="# Example Plan\n",
            root=self.root,
            force=False,
        )
        paa_docs.command_new_doc(args)
        text = target.read_text()
        self.assertIn("Title: Example Plan", text)
        self.assertIn("Doc-ID: paa-example-plan", text)
        self.assertIn("# Example Plan", text)

    def test_set_header_preserves_existing_body(self) -> None:
        target = self.root / "docs/3_Plan/2026-05-18-legacy-plan.md"
        target.write_text("# Legacy Plan\n\nBody text.\n")
        args = SimpleNamespace(
            path=target,
            title="Legacy Plan",
            doc_id="paa-legacy-plan",
            doc_type="plan",
            status="active",
            stage="plan",
            created="2026-05-18",
            last_edited="2026-05-18",
            author="Billy Weisberg",
            repo="paa-platform",
            component="",
            domain="legacy-domain",
            keywords=["legacy"],
            depends_on=[],
            supersedes=[],
            superseded_by=[],
            canonical=True,
            review_after="2026-06-15",
            owners=[],
            expires="",
            issue="",
            pr="",
            authority_source="",
            implementation_status="",
            summary="Adds a header to a legacy document.",
            body=None,
            root=self.root,
        )
        paa_docs.command_set_header(args)
        text = target.read_text()
        self.assertIn("Title: Legacy Plan", text)
        self.assertIn("Canonical: true", text)
        self.assertTrue(text.strip().endswith("Body text."))

    def test_current_operate_includes_monitor_docs(self) -> None:
        monitor_doc = """Title: TechLead Traceability Reporting
Doc-ID: paa-techlead-traceability-reporting
Doc-Type: runbook
Status: active
Lifecycle-Stage: operate
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: TechLeadTraceabilityReporting
Domain: traceability-reporting
Keywords: techlead, traceability, reporting
Depends-On:
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-15
Summary: Defines the operate-stage traceability reporting surface.

# TechLead Traceability Reporting
"""
        (self.root / "docs/7_Monitor/2026-05-03-techlead-traceability-reporting.md").write_text(monitor_doc)
        records, _ = paa_docs.build_index(self.root)
        args = SimpleNamespace(
            include_legacy=False,
            doc_id=None,
            title_contains=None,
            doc_type=None,
            status=None,
            stage="operate",
            component=None,
            domain=None,
            keyword=None,
            path_prefix=None,
            canonical=None,
        )
        current = paa_docs.current_records(records, args)
        self.assertEqual(1, len(current))
        self.assertEqual("paa-techlead-traceability-reporting", current[0].get("doc_id"))

    def test_current_reference_includes_terminology_docs(self) -> None:
        glossary_doc = """Title: PAA Engineering Terminology Glossary
Doc-ID: paa-engineering-terminology-glossary
Doc-Type: glossary
Status: active
Lifecycle-Stage: reference
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: PaaEngineeringTerminology
Domain: terminology
Keywords: paa, terminology, glossary
Depends-On:
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-15
Summary: Defines the reference-stage terminology surface.

# PAA Engineering Terminology Glossary
"""
        (self.root / "docs/terminology").mkdir(parents=True, exist_ok=True)
        (self.root / "docs/terminology/paa-engineering-terminology-glossary.md").write_text(glossary_doc)
        records, _ = paa_docs.build_index(self.root)
        args = SimpleNamespace(
            include_legacy=False,
            doc_id=None,
            title_contains=None,
            doc_type=None,
            status=None,
            stage="reference",
            component=None,
            domain=None,
            keyword=None,
            path_prefix=None,
            canonical=None,
        )
        current = paa_docs.current_records(records, args)
        self.assertEqual(1, len(current))
        self.assertEqual("paa-engineering-terminology-glossary", current[0].get("doc_id"))

    def test_language_lint_flags_banned_vague_phrase(self) -> None:
        target = self.root / "docs/2_Design/2026-05-18-vague.md"
        target.write_text(
            """Title: Vague Language Note
Doc-ID: paa-vague-language-note
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Canonical: false
Summary: Contains a banned vague phrase.

The system handles review routing.
""",
        )
        records, _ = paa_docs.build_index(self.root)
        findings = paa_docs.validate_language_governance(records, self.root)
        self.assertTrue(any(f.code == "banned_vague_phrase" for f in findings))

    def test_language_lint_flags_missing_status_scope(self) -> None:
        target = self.root / "docs/2_Design/2026-05-18-status.md"
        target.write_text(
            """Title: Status Note
Doc-ID: paa-status-note
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Canonical: false
Summary: Contains an under-scoped status word.

Implemented.
""",
        )
        records, _ = paa_docs.build_index(self.root)
        findings = paa_docs.validate_language_governance(records, self.root)
        self.assertTrue(any(f.code == "missing_status_scope" for f in findings))

    def test_language_lint_flags_missing_path_classification(self) -> None:
        target = self.root / "docs/2_Design/2026-05-18-path-claim.md"
        target.write_text(
            """Title: Path Claim Note
Doc-ID: paa-path-claim-note
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Canonical: false
Summary: Contains a path claim without classification.

`packages/paa-consumer/src/paa_consumer/techlead.py` orchestrates review routing.
""",
        )
        records, _ = paa_docs.build_index(self.root)
        findings = paa_docs.validate_language_governance(records, self.root)
        self.assertTrue(any(f.code == "missing_path_classification" for f in findings))

    def test_language_lint_ignores_backticked_banned_phrase_examples(self) -> None:
        target = self.root / "docs/terminology/2026-05-19-rules.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            """Title: Rules Note
Doc-ID: paa-rules-note
Doc-Type: policy
Status: active
Lifecycle-Stage: reference
Created: 2026-05-19
Last-Edited: 2026-05-19
Author: Billy Weisberg
Repo: paa-platform
Canonical: false
Summary: Contains a quoted banned phrase example.

- `the system handles`
""",
        )
        records, _ = paa_docs.build_index(self.root)
        findings = paa_docs.validate_language_governance(records, self.root)
        self.assertFalse(any(f.code == "banned_vague_phrase" for f in findings))

    def test_language_lint_allows_scoped_status_sentence(self) -> None:
        target = self.root / "docs/2_Design/2026-05-18-scoped-status.md"
        target.write_text(
            """Title: Scoped Status Note
Doc-ID: paa-scoped-status-note
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Canonical: false
Summary: Uses a scoped status sentence.

Worker-result transition application is implemented for one runtime path.
""",
        )
        records, _ = paa_docs.build_index(self.root)
        findings = paa_docs.validate_language_governance(records, self.root)
        self.assertFalse(any(f.code == "missing_status_scope" for f in findings))


if __name__ == "__main__":
    unittest.main()
