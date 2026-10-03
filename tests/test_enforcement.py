"""New fictional contracts test abstention, provenance, and modular behavior."""

import copy
import unittest

from contract_check.core import ingest
from contract_check.enforcement import assess, validate_request, validate_assessment
from contract_check.enforcement.authorities import verify_manifest
from contract_check.enforcement.issues import request_template
from contract_check.enforcement.providers.local_llm import LocalLLMProvider
from contract_check.enforcement.report import render_assessment


def sample(text, quote, issue):
    project = ingest(text)
    block = next(b for b in project["blocks"] if quote in b["text"])
    review = {"source_sha256": project["source_sha256"], "project_version": 0,
              "context": {"contract_type": "fictional", "represented_party": "Buyer", "objective": "unknown", "jurisdiction": "Missouri"},
              "findings": [{"id": "F-1", "lens": "legal", "status": "proposed",
                            "evidence": [{"block_id": block["id"], "quote": quote}],
                            "affected_blocks": [block["id"]], "issue": issue,
                            "consequence": "unknown", "proposal": "Review", "uncertainty": "unknown",
                            "decision_needed": "Review with counsel"}]}
    return project, review


class EnforcementTests(unittest.TestCase):
    def test_unseen_arbitration_question_abstains_without_facts_and_law(self):
        project, review = sample("Disputes shall be arbitrated in Missouri unless the parties agree otherwise.\n", "unless the parties agree otherwise", "What is the effect of a later oral exchange?")
        request = request_template(project, review)
        self.assertEqual(validate_request(project, review, request)["question_count"], 1)
        result = assess(project, review, request)
        self.assertEqual(result["assessments"][0]["status"], "insufficient_information")
        self.assertIn("verified_authority", result["assessments"][0]["missing"])
        self.assertIsNone(result["assessments"][0]["outcome_probability"])
        self.assertIn("No legal outcome probability", render_assessment(result))

    def test_unseen_delivery_condition_with_supplied_excerpt_still_needs_lawyer(self):
        project, review = sample("Buyer shall pay after Seller delivers the equipment and a signed acceptance certificate.\n", "after Seller delivers the equipment", "Has the payment condition occurred?")
        request = request_template(project, review)
        q = request["questions"][0]
        q.update(issue_type="condition", enforcing_party="Seller", resisting_party="Buyer",
                 asserted_duty="Payment after delivery", requested_remedy="Payment", forum="Missouri state court",
                 posture="Pre-suit", event_date="2026-01-01",
                 facts=[{"statement": "Seller asserts delivery", "state": "disputed", "source": "Seller statement"}],
                 authority_ids=["A-1"])
        manifest = {"schema": 1, "authorities": [{"id": "A-1", "title": "Fictional test authority", "jurisdiction": "Missouri",
                    "court_or_body": "Test fixture", "decision_date": "2020-01-01", "precedential_status": "fictional",
                    "source_url": "https://example.invalid/fixture", "full_text": "For this fixture, delivery is disputed.",
                    "excerpt": "delivery is disputed", "reviewer_verified": True,
                    "reviewed_by": "Fixture reviewer", "reviewed_at": "2026-01-01", "review_note": "Fictional source checked for this test"}]}
        result = assess(project, review, request, manifest)
        self.assertEqual(result["assessments"][0]["status"], "review_pending")
        self.assertEqual(result["assessments"][0]["lawyer_review"], "pending")
        self.assertEqual(result["assessments"][0]["authorities"][0]["verification"], "excerpt_in_supplied_text")

    def test_stale_source_and_fabricated_quote_fail(self):
        project, review = sample("A fee is due upon receipt.\n", "upon receipt", "Timing")
        request = request_template(project, review)
        bad = copy.deepcopy(request)
        bad["source_sha256"] = "wrong"
        with self.assertRaises(ValueError):
            assess(project, review, bad)
        bad = copy.deepcopy(request)
        bad["questions"][0]["evidence"][0]["quote"] = "upon approval"
        with self.assertRaises(ValueError):
            assess(project, review, bad)

    def test_authority_quote_and_endpoint_must_be_verified(self):
        with self.assertRaises(ValueError):
            verify_manifest({"schema": 1, "authorities": [{"id": "x", "title": "x", "jurisdiction": "x", "court_or_body": "x", "decision_date": "x", "precedential_status": "x", "source_url": "x", "full_text": "actual", "excerpt": "invented"}]})
        with self.assertRaises(ValueError):
            LocalLLMProvider("https://remote.example/v1/chat/completions", "model")

    def test_untrusted_model_text_not_rendered_and_tampering_rejected(self):
        project, review = sample("Payment is due on delivery.\n", "on delivery", "Payment timing")
        request = request_template(project, review)
        class HostileProvider:
            name = "hostile-fixture"
            def propose(self, question, authorities):
                return {"supporting": "This clause is unquestionably enforceable under invented law.",
                        "opposing": "None", "unknowns": []}
        q = request["questions"][0]
        q.update(enforcing_party="Seller", resisting_party="Buyer", asserted_duty="Payment", requested_remedy="Payment",
                 forum="Missouri state court", posture="Pre-suit", event_date="2026-01-01",
                 facts=[{"statement": "Delivery occurred", "state": "disputed", "source": "Buyer statement"}], authority_ids=["A-1"])
        manifest = {"schema": 1, "authorities": [{"id": "A-1", "title": "Fictional fixture", "jurisdiction": "MO", "court_or_body": "Test",
                    "decision_date": "2020-01-01", "precedential_status": "fictional", "source_url": "https://example.invalid/fixture",
                    "full_text": "Fictional fixture passage.", "excerpt": "fixture passage", "reviewer_verified": True,
                    "reviewed_by": "Fixture reviewer", "reviewed_at": "2026-01-01", "review_note": "Test only"}]}
        result = assess(project, review, request, manifest, HostileProvider())
        self.assertIn("unquestionably", result["assessments"][0]["provider_draft_unreviewed"]["supporting"])
        self.assertNotIn("unquestionably", render_assessment(result))
        forged = copy.deepcopy(result)
        forged["assessments"][0]["missing"] = []
        forged["assessments"][0]["status"] = "insufficient_information"
        with self.assertRaisesRegex(ValueError, "gates"):
            validate_assessment(project, review, request, forged, manifest)

    def test_finding_link_requires_related_evidence(self):
        project, review = sample("Delivery is due Monday.\n\nPayment is due Tuesday.\n", "Delivery is due Monday", "Delivery timing")
        request = request_template(project, review)
        unrelated = next(b for b in project["blocks"] if "Payment" in b["text"])
        request["questions"][0]["evidence"] = [{"block_id": unrelated["id"], "quote": "Payment is due Tuesday"}]
        with self.assertRaisesRegex(ValueError, "connect"):
            validate_request(project, review, request)


if __name__ == "__main__":
    unittest.main()
