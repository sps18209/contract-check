import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from contract_check.docx import extract_docx


class DocxTest(unittest.TestCase):
    def test_table_order_and_warnings(self):
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body><w:p><w:r><w:t>Agreement</w:t></w:r></w:p>
        <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Fee</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>$100</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
        <w:p><w:ins><w:r><w:t>Revised term</w:t></w:r></w:ins></w:p>
        </w:body></w:document>'''
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'sample.docx'
            with ZipFile(path, 'w') as z:
                z.writestr('word/document.xml', xml)
                z.writestr('word/header1.xml', '<header/>')
            result = extract_docx(path)
        self.assertEqual(result['text'], 'Agreement\n\nFee\t$100\n\nRevised term\n')
        self.assertTrue(any('tracked changes' in w for w in result['manifest']['warnings']))
        self.assertTrue(any('headers or footers' in w for w in result['manifest']['warnings']))
