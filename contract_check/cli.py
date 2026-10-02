"""Command line interface for the host-independent structural engine."""
import argparse
import json
from pathlib import Path
from .core import ingest, apply, render, check, compare
from .review import validate_review


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main(argv=None):
    p = argparse.ArgumentParser(prog='contract-check')
    sub = p.add_subparsers(dest='command', required=True)
    for name, args in [('ingest', ['input', 'output']), ('apply', ['project', 'plan', 'output']),
                       ('render', ['project', 'output']), ('check', ['project', 'input']),
                       ('compare', ['original', 'revised', 'output']), ('validate-review', ['project', 'review'])]:
        cmd = sub.add_parser(name)
        for arg in args:
            cmd.add_argument(arg)
        if name in ('render', 'compare'):
            cmd.add_argument('--style', choices=['preserve', 'decimal', 'articles'], default='preserve')
        if name == 'render':
            cmd.add_argument('--update-refs', action='store_true')
            cmd.add_argument('--map-output')
    a = p.parse_args(argv)
    try:
        if a.command == 'ingest':
            save(a.output, ingest(Path(a.input).read_text(encoding='utf-8')))
        elif a.command == 'apply':
            save(a.output, apply(load(a.project), load(a.plan)))
        elif a.command == 'render':
            text, info = render(load(a.project), a.style, a.update_refs)
            Path(a.output).write_text(text, encoding='utf-8')
            if a.map_output:
                save(a.map_output, info)
        elif a.command == 'check':
            report = check(load(a.project), Path(a.input).read_text(encoding='utf-8'))
            print(json.dumps(report, indent=2))
            return 2 if any(report[k] for k in ('duplicate_labels', 'unresolved_references', 'duplicate_definitions')) else 0
        elif a.command == 'compare':
            save(a.output, compare(load(a.original), load(a.revised), a.style))
        elif a.command == 'validate-review':
            print(json.dumps(validate_review(load(a.project), load(a.review)), indent=2))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        p.exit(1, f'contract-check: {error}\n')
    return 0
