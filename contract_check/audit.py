"""Deterministic change flags for human semantic review."""
import re
from .core import validate

QUANTITY = re.compile(r'(?<!\w)(?:\$\s*)?\d[\d,]*(?:\.\d+)?\s*(?:%|percent|days?|months?|years?|hours?)?', re.I)
CONTROL = re.compile(r'\b(?:not|never|unless|except|only|must|shall|may|will|before|after|within|equal|exceed|greater|less|at\s+least|more\s+than|up\s+to|including|exclusive|inclusive)\b', re.I)


def _tokens(pattern, text):
    return [m.group(0).strip().lower() for m in pattern.finditer(text)]


def audit(old, new):
    validate(old)
    validate(new)
    if old['source_sha256'] != new['source_sha256']:
        raise ValueError('unrelated projects')
    before = {b['id']: b for b in old['blocks']}
    after = {b['id']: b for b in new['blocks']}
    flags = []
    for bid in before.keys() & after.keys():
        a, b = before[bid]['text'], after[bid]['text']
        if a == b:
            continue
        changed = {}
        for label, pattern in [('quantities', QUANTITY), ('control_words', CONTROL)]:
            left, right = _tokens(pattern, a), _tokens(pattern, b)
            if left != right:
                changed[label] = {'before': left, 'after': right}
        if changed:
            flags.append({'block_id': bid, 'changes': changed})
    for bid in before.keys() - after.keys():
        flags.append({'block_id': bid, 'changes': {'deleted': True}})
    for bid in after.keys() - before.keys():
        flags.append({'block_id': bid, 'changes': {'inserted': True}})
    return {'scope': 'lexical quantity and control-word changes, insertions and deletions; human review required',
            'flags': sorted(flags, key=lambda f: f['block_id'])}
