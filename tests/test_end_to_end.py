"""Synthetic services agreement; tests the whole decision and revision path."""
import unittest
from contract_check import ingest, apply, render, check
from contract_check.audit import audit
from contract_check.inventory import inventory
from contract_check.presentation import decision_cards, revision_report
from contract_check.review import choice_template, validate_choices, validate_review


class EndToEndTest(unittest.TestCase):
    def test_threshold_mismatch_through_approved_report(self):
        source = '1. Bonus\n\nVendor earns a $500 bonus when sales exceed $100,000.\n\n2. Notices\n\nNotice must be delivered to Customer.'
        project = ingest(source)
        self.assertEqual(len(inventory(project)['heading_candidates']), 2)
        labeled = apply(project, {'base_version': 0, 'source_sha256': project['source_sha256'],
                                  'operations': [
                                      {'action': 'label', 'id': 'b00001', 'before': project['blocks'][0]['text'],
                                       'approved': True, 'reason': 'Confirmed heading', 'kind': 'heading',
                                       'title': 'Bonus', 'level': 1, 'old_label': '1'},
                                      {'action': 'label', 'id': 'b00003', 'before': project['blocks'][2]['text'],
                                       'approved': True, 'reason': 'Confirmed heading', 'kind': 'heading',
                                       'title': 'Notices', 'level': 1, 'old_label': '2'}]})
        finding = {'id': 'F-1', 'lens': 'deal', 'status': 'proposed',
                   'evidence': [{'block_id': 'b00002', 'quote': 'exceed $100,000'}],
                   'affected_blocks': ['b00002'], 'issue': 'Draft excludes sales at exactly $100,000.',
                   'consequence': 'Vendor may lose bonus at threshold.',
                   'proposal': 'Say sales equal or exceed $100,000 if the negotiated term is inclusive.',
                   'uncertainty': 'Negotiated term requires confirmation.',
                   'decision_needed': 'Confirm inclusive threshold.'}
        review = {'source_sha256': labeled['source_sha256'], 'project_version': 1,
                  'context': {'contract_type': 'services', 'represented_party': 'vendor',
                              'objective': 'inclusive bonus threshold', 'jurisdiction': 'unknown'},
                  'findings': [finding]}
        self.assertTrue(validate_review(labeled, review)['valid'])
        self.assertIn('Confirm inclusive threshold', decision_cards(labeled, review))
        choices = choice_template(labeled, review)
        choices['selections'][0].update(choice='adopt', reason='Client confirms equal or greater was negotiated')
        self.assertTrue(validate_choices(labeled, review, choices)['valid'])
        revised = apply(labeled, {'base_version': 1, 'source_sha256': labeled['source_sha256'],
                                  'operations': [{'action': 'replace', 'id': 'b00002',
                                                  'before': labeled['blocks'][1]['text'],
                                                  'after': 'Vendor earns a $500 bonus when sales equal or exceed $100,000.',
                                                  'reason': 'Client confirmed inclusive threshold',
                                                  'approved': True, 'classification': 'substantive',
                                                  'finding_id': 'F-1'}]}, review, choices)
        clean, _ = render(revised, 'decimal')
        self.assertEqual(check(revised, clean)['unresolved_references'], [])
        self.assertTrue(audit(labeled, revised)['flags'])
        self.assertIn('equal or exceed', revision_report(labeled, revised))
