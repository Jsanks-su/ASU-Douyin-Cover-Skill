"""Read visual strengths and creative mechanisms; interpretation is not a score."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MECHANISMS={
    'cross_plane':'跨层/破次元','figure_ground':'图地转换','letter_as_image':'字形即图像',
    'scale_conflict':'尺度反差','semantic_substitution':'语义替换','repetition_sequence':'重复/序列',
    'graphic_connection':'具体连接','material_contrast':'材质对照','information_order':'信息秩序',
    'image_type_integration':'图文融合','formal_rhythm':'形式节奏','visual_pun':'视觉双关',
    'layering':'叠层','negative_space':'负空间','perspective':'透视','metamorphosis':'形态转换',
    'motion':'动势','collection':'多设计比较'
}


def load_index(root=ROOT):
    data=json.loads((Path(root)/'references/creative-index.json').read_text(encoding='utf-8'))
    rows=data['entries']
    if data.get('schema_version')!=1 or data.get('count')!=170 or len(rows)!=170 or {r['id'] for r in rows}!=set(range(1,171)):
        raise ValueError('creative index schema/coverage mismatch; full visual review required')
    return {r['id']:r for r in rows}


def summary(row):
    return {k:row[k] for k in ('core_idea','mechanisms','must_survive','needs_from_input','failure_modes','default_usage')}


def get_record(rid,root=ROOT,records=None):
    rows=load_index(root) if records is None else records
    if rid not in rows:
        raise ValueError('reference must be between 1 and 170')
    row=rows[rid]
    path=Path(root)/row['image']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['image_sha256']:
        raise ValueError('creative record has stale image evidence; re-open image and refresh reading')
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--id',type=int,help='full creative record for this reference')
    group.add_argument('--mechanism',choices=sorted(MECHANISMS),help='compare readings with this mechanism')
    group.add_argument('--mechanisms',action='store_true',help='list mechanism names')
    args=parser.parse_args()
    try:
        if args.mechanisms:
            result=MECHANISMS
        elif args.id is not None:
            result=get_record(args.id)
        else:
            rows=load_index()
            result=[dict(id=r['id'],label=r['label'],**summary(get_record(r['id'],records=rows))) for r in rows.values() if args.mechanism in r['mechanisms']]
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError) as exc:
        parser.error(str(exc))


if __name__=='__main__':main()
