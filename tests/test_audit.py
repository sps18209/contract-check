import unittest
from contract_check import ingest, apply
from contract_check.audit import audit


class AuditTest(unittest.TestCase):
    def test_flags_quantity_and_negation_changes(self):
        original = ingest('The fee must not exceed $10,000.')
        revised = apply(original, {'base_version': 0, 'source_sha256': original['source_sha256'],
                                   'operations': [{'action': 'replace', 'id': 'b00001',
                                                   'before': original['blocks'][0]['text'],
                                                   'after': 'The fee may exceed $100,000.',
                                                   'reason': 'Approved counteroffer', 'approved': True}]})
        changes = audit(original, revised)['flags'][0]['changes']
        self.assertEqual(changes['quantities']['before'], ['$10,000'])
        self.assertEqual(changes['quantities']['after'], ['$100,000'])
        self.assertEqual(changes['control_words']['before'], ['must', 'not', 'exceed'])
        self.assertEqual(changes['control_words']['after'], ['may', 'exceed'])
