import unittest
from contract_check import ingest
from contract_check.review import validate_review


class ReviewTest(unittest.TestCase):
    def test_rejects_fabricated_quote_and_stale_version(self):
        project = ingest('A party shall give notice.')
        record = {'source_sha256': project['source_sha256'], 'project_version': 0,
                  'context': {x: 'unknown' for x in ('contract_type', 'represented_party', 'objective', 'jurisdiction')},
                  'findings': [{'id': 'F-1', 'lens': 'linguistic', 'status': 'proposed',
                                'evidence': [{'block_id': 'b00001', 'quote': 'invented'}],
                                'affected_blocks': ['b00001'],
                                **{x: 'unknown' for x in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed')}}]}
        with self.assertRaisesRegex(ValueError, 'quote'):
            validate_review(project, record)
        record['findings'][0]['evidence'][0]['quote'] = 'give notice'
        self.assertTrue(validate_review(project, record)['valid'])
        record['project_version'] = 9
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_review(project, record)
