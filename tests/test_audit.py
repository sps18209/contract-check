import unittest
from contract_check import ingest, apply
from contract_check.audit import audit
from contract_check.review import choice_template


class AuditTest(unittest.TestCase):
    def test_flags_quantity_and_negation_changes(self):
        original = ingest('The fee must not exceed $10,000.')
        review = {'source_sha256': original['source_sha256'], 'project_version': 0,
                  'context': {k: 'unknown' for k in ('contract_type', 'represented_party', 'objective', 'jurisdiction')},
                  'findings': [{'id': 'F-fee', 'lens': 'deal', 'status': 'proposed',
                                'evidence': [{'block_id': 'b00001', 'quote': 'must not exceed $10,000'}],
                                'affected_blocks': ['b00001'],
                                **{k: 'Approved counteroffer' for k in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed')}}]}
        choices = choice_template(original, review)
        choices['selections'][0].update(choice='adopt', reason='Client approved counteroffer')
        revised = apply(original, {'base_version': 0, 'source_sha256': original['source_sha256'],
                                   'operations': [{'action': 'replace', 'id': 'b00001',
                                                   'before': original['blocks'][0]['text'],
                                                   'after': 'The fee may exceed $100,000.',
                                                   'reason': 'Approved counteroffer', 'approved': True,
                                                   'finding_id': 'F-fee'}]}, review, choices)
        changes = audit(original, revised)['flags'][0]['changes']
        self.assertEqual(changes['quantities']['before'], ['$10,000'])
        self.assertEqual(changes['quantities']['after'], ['$100,000'])
        self.assertEqual(changes['control_words']['before'], ['must', 'not', 'exceed'])
        self.assertEqual(changes['control_words']['after'], ['may', 'exceed'])
