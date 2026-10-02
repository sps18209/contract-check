import unittest
from contract_check import ingest, apply
from contract_check.review import choice_template, validate_choices


class ChoiceTest(unittest.TestCase):
    def test_retained_finding_cannot_authorize_edit(self):
        project = ingest('Seller shall give 10 days notice.')
        review = {'source_sha256': project['source_sha256'], 'project_version': 0,
                  'context': {x: 'unknown' for x in ('contract_type', 'represented_party', 'objective', 'jurisdiction')},
                  'findings': [{'id': 'F-1', 'lens': 'termination', 'status': 'proposed',
                                'evidence': [{'block_id': 'b00001', 'quote': '10 days notice'}],
                                'affected_blocks': ['b00001'],
                                **{x: 'unknown' for x in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed')}}]}
        choices = choice_template(project, review)
        choices['selections'][0].update(choice='retain', reason='Keep negotiated wording')
        self.assertTrue(validate_choices(project, review, choices)['valid'])
        plan = {'base_version': 0, 'source_sha256': project['source_sha256'],
                'operations': [{'action': 'replace', 'id': 'b00001', 'before': project['blocks'][0]['text'],
                                'after': 'Seller shall give 30 days notice.', 'reason': 'Change period',
                                'approved': True, 'classification': 'substantive', 'finding_id': 'F-1'}]}
        with self.assertRaisesRegex(ValueError, 'not linked to an adopted'):
            apply(project, plan, review, choices)
        choices['selections'][0]['choice'] = 'adopt'
        revised = apply(project, plan, review, choices)
        self.assertIn('30 days', revised['blocks'][0]['text'])

    def test_missing_choice_is_rejected(self):
        project = ingest('Text.')
        review = {'source_sha256': project['source_sha256'], 'project_version': 0,
                  'context': {x: 'unknown' for x in ('contract_type', 'represented_party', 'objective', 'jurisdiction')},
                  'findings': []}
        choices = choice_template(project, review)
        choices['selections'].append({'finding_id': 'F-fake', 'choice': 'adopt', 'reason': 'Anything'})
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            validate_choices(project, review, choices)
