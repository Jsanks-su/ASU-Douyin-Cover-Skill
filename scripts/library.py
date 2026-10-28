"""Browse the bundled poster references using only Python's standard library."""
import argparse
import json
from pathlib import Path
from matching import rank
from creative import get_record, load_index as load_creative_index, summary as creative_summary

ROOT = Path(__file__).resolve().parents[1]

def read_catalog():
    return json.loads((ROOT / 'references' / 'catalog.json').read_text(encoding='utf-8'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', type=int)
    parser.add_argument('--tags', nargs='+', default=[])
    parser.add_argument('--limit', type=int, default=12)
    parser.add_argument('--sheets', action='store_true')
    parser.add_argument('--profile', type=Path, help='rank against a vision-authored source JSON profile')
    parser.add_argument('--reference', type=int, help='explicit user choice, with --profile only')
    args = parser.parse_args()
    if not 1 <= args.limit <= 170:
        parser.error('limit must be between 1 and 170')
    if args.profile:
        if args.id is not None or args.tags or args.sheets:
            parser.error('--profile cannot combine with --id, --tags or --sheets')
        try:
            result = rank(json.loads(args.profile.read_text(encoding='utf-8-sig')), args.limit, args.reference)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            parser.error(str(exc))
        return
    if args.reference is not None:
        parser.error('--reference requires --profile')
    if args.sheets and (args.id is not None or args.tags):
        parser.error('--sheets cannot combine with --id or --tags')
    if args.id is not None and args.tags:
        parser.error('--id cannot combine with --tags')
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
        refs = refs[:args.limit]
    output = []
    creative_records=load_creative_index(ROOT)
    for r in refs:
        reading=get_record(r['id'],ROOT,creative_records)
        output.append({**r, 'image_absolute': str((ROOT / r['image']).resolve()), 'contact_sheet_absolute': str((ROOT / r['contact_sheet']).resolve()),
                       'creative':reading if args.id is not None else creative_summary(reading)})
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
