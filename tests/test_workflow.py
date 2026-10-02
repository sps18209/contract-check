import unittest
from contract_check import ingest, apply, render, check, compare

SOURCE = '1. Fees\n\nPay $100 under Section 1.\n\n2. Termination\n\nNotice is required under Section 2.\n'


def labeled():
    p = ingest(SOURCE)
    p = apply(p, {'base_version': 0, 'source_sha256': p['source_sha256'],
                  'operations': [
                      {'action': 'label', 'id': 'b00001', 'before': p['blocks'][0]['text'], 'approved': True,
                       'reason': 'Identified heading', 'kind': 'heading', 'title': 'Fees', 'level': 1, 'old_label': '1'},
                      {'action': 'label', 'id': 'b00003', 'before': p['blocks'][2]['text'], 'approved': True,
                       'reason': 'Identified heading', 'kind': 'heading', 'title': 'Termination', 'level': 1, 'old_label': '2'}]})
    return p


class ContractWorkflow(unittest.TestCase):
    def test_reorder_insert_and_update_references(self):
        p = labeled()
        revised = apply(p, {'base_version': p['version'], 'source_sha256': p['source_sha256'],
                            'operations': [{'action': 'insert', 'id': 'n00001', 'text': '3. Notices',
                                            'kind': 'heading', 'title': 'Notices', 'level': 1,
                                            'section_decision_id': 'notices',
                                            'reason': 'Add agreed notice heading', 'approved': True}],
                            'order': ['b00003', 'b00004', 'b00001', 'b00002', 'n00001'],
                            'order_reason': 'Put termination before fees', 'order_approved': True,
                            'decisions': {'notices': {'status': 'include', 'reason': 'Approved by client'}}})
        output, meta = render(revised, 'articles', update_refs=True)
        self.assertIn('Article 1 Termination', output)
        self.assertIn('Article 1.', output)  # Source Section 2 now points to first heading.
        self.assertIn('Article 2.', output)  # Source Section 1 now points to second heading.
        self.assertEqual(meta['reference_map']['section 1'], 'Article 2')
        self.assertEqual(revised['decisions']['notices']['status'], 'include')
        self.assertEqual(check(revised, output)['unresolved_references'], [])
        self.assertEqual(compare(p, revised)['changes'][-1]['change'], 'insert')

    def test_stale_plan_and_unapproved_change_rejected(self):
        p = labeled()
        plan = {'base_version': 0, 'source_sha256': p['source_sha256'], 'operations': []}
        with self.assertRaisesRegex(ValueError, 'stale'):
            apply(p, plan)
        plan['base_version'] = p['version']
        plan['operations'] = [{'action': 'delete', 'id': 'b00002', 'before': p['blocks'][1]['text'],
                               'reason': 'Remove fee'}]
        with self.assertRaisesRegex(ValueError, 'approval'):
            apply(p, plan)

    def test_unmapped_reference_fails_closed(self):
        p = labeled()
        p['blocks'][1]['text'] = 'See Section 99.'
        with self.assertRaisesRegex(ValueError, 'unmapped reference'):
            render(p, 'decimal', update_refs=True)

    def test_compound_reference_requires_manual_review(self):
        p = labeled()
        p['blocks'][1]['text'] = 'See Section 1(a) and Sections 1 and 2.'
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            render(p, 'decimal', update_refs=True)
        self.assertIn('Section 1(a)', check(p, p['blocks'][1]['text'])['unsupported_references'])

    def test_label_cannot_discard_operative_text(self):
        p = ingest('1. Fees\nVendor shall pay $100.')
        with self.assertRaisesRegex(ValueError, 'heading text contains content'):
            apply(p, {'base_version': 0, 'source_sha256': p['source_sha256'],
                      'operations': [{'action': 'label', 'id': 'b00001', 'before': p['blocks'][0]['text'],
                                      'approved': True, 'reason': 'Heading', 'kind': 'heading',
                                      'title': 'Fees', 'level': 1, 'old_label': '1'}]})

    def test_deleted_block_visible_in_comparison(self):
        p = labeled()
        from contract_check.review import choice_template
        review = {'source_sha256': p['source_sha256'], 'project_version': p['version'],
                  'context': {k: 'unknown' for k in ('contract_type', 'represented_party', 'objective', 'jurisdiction')},
                  'findings': [{'id': 'F-delete', 'lens': 'deal', 'status': 'proposed',
                                'evidence': [{'block_id': 'b00002', 'quote': 'Pay $100'}],
                                'affected_blocks': ['b00002'],
                                **{k: 'Client decision' for k in ('issue', 'consequence', 'proposal', 'uncertainty', 'decision_needed')}}]}
        choices = choice_template(p, review)
        choices['selections'][0].update(choice='adopt', reason='Client removed fee')
        revised = apply(p, {'base_version': p['version'], 'source_sha256': p['source_sha256'],
                            'operations': [{'action': 'delete', 'id': 'b00002', 'before': p['blocks'][1]['text'],
                                            'reason': 'Client removed fee', 'approved': True,
                                            'finding_id': 'F-delete'}]}, review, choices)
        self.assertTrue(any(c['change'] == 'delete' for c in compare(p, revised)['changes']))

    def test_article_source_reference_kind(self):
        p = ingest('Article 4 Scope\n\nSee Article 4.')
        p = apply(p, {'base_version': 0, 'source_sha256': p['source_sha256'],
                      'operations': [{'action': 'label', 'id': 'b00001', 'before': p['blocks'][0]['text'],
                                      'approved': True, 'reason': 'Existing heading', 'kind': 'heading',
                                      'title': 'Scope', 'level': 1, 'old_label': '4', 'old_kind': 'Article'}]})
        text, _ = render(p, 'articles', update_refs=True)
        self.assertIn('See Article 1.', text)

    def test_no_silent_hierarchy_skip(self):
        p = labeled()
        p['blocks'][0]['level'] = 2
        with self.assertRaisesRegex(ValueError, 'skips'):
            render(p, 'decimal')


if __name__ == '__main__':
    unittest.main()
