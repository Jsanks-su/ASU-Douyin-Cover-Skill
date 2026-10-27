"""Browse the bundled poster references using only Python's standard library."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_catalog():
    return json.loads((ROOT / 'references' / 'catalog.json').read_text(encoding='utf-8'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', type=int)
    parser.add_argument('--tags', nargs='+', default=[])
    parser.add_argument('--limit', type=int, default=12)
    parser.add_argument('--sheets', action='store_true')
    args = parser.parse_args()
    data = read_catalog()
    if args.sheets:
        print(json.dumps([str((ROOT / s).resolve()) for s in data['contact_sheets']], ensure_ascii=False, indent=2))
        return
    refs = data['references']
    if args.id is not None:
        refs = [r for r in refs if r['id'] == args.id]
        if not refs:
            parser.error('reference ID must be between 1 and 170')
    else:
        unknown = set(args.tags) - set(data['tags'])
        if unknown:
            parser.error('unknown tags: ' + ', '.join(sorted(unknown)))
        if args.tags:
            refs = [r for r in refs if set(args.tags) & set(r['tags'])]
        refs.sort(key=lambda r: (-len(set(args.tags) & set(r['tags'])), not r['recommended_start'], r['id']))
        refs = refs[:max(1, args.limit)]
    output = []
    for r in refs:
        output.append({**r, 'image_absolute': str((ROOT / r['image']).resolve()), 'contact_sheet_absolute': str((ROOT / r['contact_sheet']).resolve())})
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
