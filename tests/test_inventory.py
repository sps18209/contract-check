import unittest
from contract_check import ingest
from contract_check.inventory import inventory


class InventoryTest(unittest.TestCase):
    def test_candidates_and_definition_mentions(self):
        project = ingest('Article 3 Services\n\n"Services" means consulting.\n\nServices begin tomorrow.')
        result = inventory(project)
        self.assertEqual(result['heading_candidates'][0]['old_kind'], 'Article')
        self.assertEqual(result['defined_terms'][0]['definition_blocks'], ['b00002'])
        self.assertEqual(result['defined_terms'][0]['case_insensitive_mentions'], 3)
