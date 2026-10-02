import unittest
from contract_check import ingest, apply
from contract_check.presentation import decision_cards, revision_report, structure_preview
from contract_check.review import choice_template


class PresentationTest(unittest.TestCase):
    def test_structure_choices_do_not_force_sections(self):
        preview = structure_preview(ingest('1. Fees\n\nPay on receipt.'))
        self.assertIn('Unconfirmed heading candidates: Fees', preview)
        self.assertIn('include / omit / defer', preview)
        self.assertIn('Definitions', preview)

    def test_missing_clause_choice_and_revision_report(self):
        project = ingest('Services end on December 31.')
        finding = {'id': 'F-1', 'lens': 'structural', 'status': 'proposed',
                   'evidence': [], 'absence_basis': 'Reviewed all provisions; client requested notice clause.',
                   'affected_blocks': [], 'issue': 'Notice mechanism absent',
                   'consequence': 'Delivery may be disputed', 'proposal': 'Add notice mechanics',
                   'uncertainty': 'Delivery method unknown', 'decision_needed': 'Choose method'}
        review = {'source_sha256': project['source_sha256'], 'project_version': 0,
                  'context': {x: 'unknown' for x in ('contract_type', 'represented_party', 'objective', 'jurisdiction')},
                  'findings': [finding]}
        self.assertIn('Reviewed all provisions', decision_cards(project, review))
        review['findings'][0]['evidence'] = [{'block_id': 'b00001', 'quote': 'December 31'}]
        choices = choice_template(project, review)
        choices['selections'][0].update(choice='adopt', reason='Client approved extension')
        revised = apply(project, {'source_sha256': project['source_sha256'], 'base_version': 0,
                                  'operations': [{'action': 'replace', 'id': 'b00001',
                                                  'before': project['blocks'][0]['text'],
                                                  'after': 'Services end on January 31.',
                                                  'reason': 'Approved extension', 'approved': True,
                                                  'finding_id': 'F-1'}]}, review, choices)
        report = revision_report(project, revised)
        self.assertIn('December 31', report)
        self.assertIn('January 31', report)
