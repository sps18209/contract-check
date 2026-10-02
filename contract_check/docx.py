"""Conservative DOCX text extraction with a visible fidelity manifest."""
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def _text(node):
    parts = []
    for element in node.iter():
        if element.tag == W + 't':
            parts.append(element.text or '')
        elif element.tag == W + 'tab':
            parts.append('\t')
        elif element.tag in (W + 'br', W + 'cr'):
            parts.append('\n')
    return ''.join(parts).strip()


def extract_docx(path):
    """Return text and warnings; unsupported content remains visible as a warning."""
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            if 'word/document.xml' not in names:
                raise ValueError('DOCX has no document.xml')
            root = ET.fromstring(archive.read('word/document.xml'))
    except (BadZipFile, ET.ParseError) as exc:
        raise ValueError(f'invalid DOCX: {exc}') from exc
    body = root.find(W + 'body')
    if body is None:
        raise ValueError('DOCX has no body')
    warnings = []
    for label, condition in [
        ('tracked changes', bool(root.findall('.//' + W + 'ins') or root.findall('.//' + W + 'del'))),
        ('comments', any(n.startswith('word/comments') for n in names)),
        ('headers or footers', any(n.startswith(('word/header', 'word/footer')) for n in names)),
        ('footnotes or endnotes', any(n.startswith(('word/footnotes', 'word/endnotes')) for n in names)),
        ('drawings or text boxes', bool(root.findall('.//' + W + 'drawing') or root.findall('.//' + W + 'txbxContent'))),
        ('field codes', bool(root.findall('.//' + W + 'instrText'))),
    ]:
        if condition:
            warnings.append(label + ' detected; inspect the original before review')
    blocks = []
    for child in body:
        if child.tag == W + 'p':
            value = _text(child)
            if value:
                blocks.append({'kind': 'paragraph', 'text': value})
        elif child.tag == W + 'tbl':
            rows = []
            for row in child.findall(W + 'tr'):
                cells = []
                for cell in row.findall(W + 'tc'):
                    cells.append(' / '.join(t for p in cell.findall('.//' + W + 'p') if (t := _text(p))))
                rows.append('\t'.join(cells))
            blocks.append({'kind': 'table', 'text': '\n'.join(rows)})
        elif child.tag != W + 'sectPr':
            warnings.append('unsupported body element ' + child.tag + '; inspect the original')
    text = '\n\n'.join(b['text'] for b in blocks if b['text']) + '\n'
    if not text.strip():
        raise ValueError('no extractable text; verify the document visually')
    return {'text': text, 'manifest': {'source': str(Path(path).name), 'block_count': len(blocks),
                                      'blocks': blocks, 'warnings': sorted(set(warnings)),
                                      'fidelity': 'plain text and table cell order only; formatting and layout not preserved'}}
