"""Portable Markdown views for decisions and revision review."""
from .review import validate_review
from .core import compare
from .audit import audit


def _safe(value):
    return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('\n', ' ')


def decision_cards(project, review):
    validate_review(project, review)
    context = review['context']
    rows = ['# Contract decisions', '',
            f"Contract: {_safe(context['contract_type'])} · Party: {_safe(context['represented_party'])} · Jurisdiction: {_safe(context['jurisdiction'])}",
            '', 'Choose an option for each material finding. Record your reason before applying an edit.', '']
    for f in review['findings']:
        rows += [f"## {_safe(f['id'])} · {_safe(f['lens'])}", '',
                 f"**Text:** {'; '.join(_safe(e['block_id'] + ': ' + e['quote']) for e in f['evidence']) or _safe(f.get('absence_basis', ''))}", '',
                 f"**Issue:** {_safe(f['issue'])}", '',
                 f"**Effect:** {_safe(f['consequence'])}", '',
                 f"**Uncertainty:** {_safe(f['uncertainty'])}", '',
                 f"**Choice needed:** {_safe(f['decision_needed'])}", '',
                 f"- [ ] Adopt the proposed change: {_safe(f['proposal'])}",
                 '- [ ] Keep the existing wording',
                 '- [ ] Defer pending more information',
                 '', '**Reason/alternative:** ____________________', '']
    if not review['findings']:
        rows += ['No findings recorded within the stated review scope.']
    return '\n'.join(rows).rstrip() + '\n'


def revision_report(original, revised, style='preserve'):
    changes = compare(original, revised, style)
    flags = audit(original, revised)['flags']
    rows = ['# Revision report', '', f"Source SHA-256: `{revised['source_sha256']}` · Version: {revised['version']}", '',
            '## Decisions', '']
    for key, item in revised['decisions'].items():
        rows.append(f"- **{_safe(key)}:** {_safe(item['status'])} — {_safe(item['reason'])}")
    if not revised['decisions']:
        rows.append('No inclusion decisions recorded.')
    rows += ['', '## Review flags', '']
    for flag in flags:
        rows.append(f"- **{_safe(flag['block_id'])}:** {_safe(flag['changes'])}")
    if not flags:
        rows.append('No lexical flags; review all edits for meaning regardless.')
    rows += ['', '## Text comparison', '', '```diff', changes['unified_diff'].rstrip(), '```', '']
    return '\n'.join(rows)
