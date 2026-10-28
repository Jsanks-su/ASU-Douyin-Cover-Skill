"""Rank bundled layouts against a vision-authored source profile; standard library only.

This is a transparent compatibility heuristic, not an image recognizer or similarity model.
The host must inspect source pixels and shortlisted full-size posters before selecting.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
from creative import load_index as load_creative_index, summary as creative_summary

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TYPES = {'portrait', 'object', 'food', 'scene', 'interface', 'document', 'mixed', 'unknown'}
ENERGIES = {'restrained', 'neutral', 'dynamic', 'solemn', 'playful'}
COLORS = {'black', 'white', 'cream', 'gray', 'red', 'orange', 'yellow', 'green', 'blue', 'cyan', 'coral', 'violet', 'purple', 'pink', 'brown', 'maroon', 'teal'}
FIELDS = {'source_type', 'image_size', 'effective_region', 'title', 'preserve_fields', 'preserve_features', 'allow_crop', 'allow_cutout', 'allow_duotone', 'preserve_colors', 'auxiliary_text', 'palette', 'energy', 'intent', 'photo_note'}
CAPACITY = {'brief': 3, 'short': 8, 'medium': 16, 'long': 30}
AREA = {'small': .25, 'medium': .55, 'large': .9}  # ordinal heuristic, NOT measured area
ASPECT = {'portrait': .7, 'landscape': 1.65, 'square': 1., 'free': None}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def validate_profile(raw):
    if not isinstance(raw, dict):
        raise ValueError('profile must be a JSON object')
    unknown = set(raw) - FIELDS
    if unknown:
        raise ValueError('unknown profile fields: ' + ', '.join(sorted(unknown)))
    p = dict(raw)
    if p.get('source_type') not in SOURCE_TYPES:
        raise ValueError('source_type must be one of: ' + ', '.join(sorted(SOURCE_TYPES)))
    size = p.get('image_size')
    if not isinstance(size, list) or len(size) != 2 or any(type(x) is not int or x <= 0 for x in size):
        raise ValueError('image_size must contain two positive integer pixel dimensions')
    if not isinstance(p.get('title'), str) or not p['title'].strip():
        raise ValueError('title must be the nonempty final cover title')
    notes = []
    if 'effective_region' not in p:
        notes.append('No effective_region supplied; whole-frame aspect used. Inspect black bars, phone UI and irrelevant borders first.')
    box = p.setdefault('effective_region', [0, 0, 1, 1])
    if not isinstance(box, list) or len(box) != 4 or any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1 for x in box) or box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError('effective_region must be normalized [left, top, right, bottom] inside [0,1], with positive width/height')
    for key, default in [('allow_crop', True), ('allow_cutout', True), ('allow_duotone', True), ('preserve_colors', False)]:
        if type(p.setdefault(key, default)) is not bool:
            raise ValueError(key + ' must be a boolean')
    if p.setdefault('auxiliary_text', 'low') not in {'low', 'medium', 'high'}:
        raise ValueError('auxiliary_text must be low, medium or high')
    for key in ('preserve_fields', 'preserve_features'):
        if not isinstance(p.setdefault(key, []), list) or any(not isinstance(x, str) or not x.strip() for x in p[key]):
            raise ValueError(key + ' must be an array of nonempty strings')
    if p['source_type'] in {'interface', 'document'} and not p['preserve_fields']:
        notes.append('Text-bearing source: identify protected fields/regions during visual review; default readability penalty remains active.')
    if not isinstance(p.setdefault('palette', []), list) or any(not isinstance(x, str) or x not in COLORS for x in p['palette']):
        raise ValueError('palette must contain canonical color names: ' + ', '.join(sorted(COLORS)))
    if 'energy' in p and p['energy'] not in ENERGIES:
        raise ValueError('energy must be one of: ' + ', '.join(sorted(ENERGIES)))
    for key in ('intent', 'photo_note'):
        if key in p and not isinstance(p[key], str):
            raise ValueError(key + ' must be a string')
    if p['source_type'] == 'unknown':
        notes.append('Unknown source type: source fit is provisional; classify from actual pixels during visual review.')
    # Latin word units plus approximate CJK typographic units for an explicit language override.
    words = len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", p['title']))
    cjk = len(re.findall(r'[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]', p['title']))
    units = max(1, words + math.ceil(cjk / 2))
    aspect = size[0] * (box[2] - box[0]) / (size[1] * (box[3] - box[1]))
    return p, dict(effective_aspect=round(aspect, 5), title_units=units, title_characters=len(p['title']), warnings=notes)


def score_entry(entry, ref, p, derived):
    a, o = entry['adaptation'], entry['observed']
    insertion, area = a['insertion'], AREA[a['area']]
    kind, native = entry['kind'], entry['native_image']
    textual = p['source_type'] in {'interface', 'document'} or bool(p['preserve_fields'])
    reasons, risks = [], []
    if textual:
        fit = {'full': 1., 'rect': 1., 'band': .6, 'negative': .4, 'mask': .2, 'cutout': .15, 'none': .05}[insertion] * (.45 + .55 * area)
        if insertion == 'full':
            fit *= .78
            risks.append('Full-bleed photographic composition may lose its spatial/subject structure when replaced by a flat interface; compare an intact rectangular placement.')
            if entry['family'] == 'portrait':
                fit *= .65
        if area < .6 or insertion not in {'rect', 'full'}:
            risks.append('Protected text may be unreadable or fragmented; prove an intact region fits at cover size.')
    elif p['source_type'] == 'portrait':
        fit = {'full': .9, 'rect': .85, 'cutout': 1., 'mask': .65, 'negative': .4, 'band': .55, 'none': .1}[insertion]
        if entry['family'] == 'portrait':
            fit = min(1., fit + .1)
    elif p['source_type'] in {'food', 'object'}:
        fit = {'full': .85, 'rect': .85, 'cutout': .9, 'mask': .6, 'negative': .4, 'band': .6, 'none': .1}[insertion]
        if entry['family'] == 'portrait':
            fit -= .2
            risks.append('Original composition depends on a face/body; adapt identity and silhouette without inventing a person.')
    elif p['source_type'] == 'scene':
        fit = {'full': 1., 'rect': .95, 'cutout': .2, 'mask': .3, 'negative': .25, 'band': .6, 'none': .1}[insertion]
    else:
        fit = {'full': .8, 'rect': .8, 'cutout': .55, 'mask': .45, 'negative': .4, 'band': .55, 'none': .1}[insertion]
    permitted = True
    if not p['allow_cutout'] and insertion in {'cutout', 'mask'}:
        permitted = False
        fit *= .2
        risks.append('Profile forbids the cutout/masking route inferred here; select a different route or reference.')
    reasons.append(f"Source insertion: {insertion}, {a['area']} (inferred route, not a measured native slot).")

    target = ASPECT[a['aspect']]
    mismatch = abs(math.log(derived['effective_aspect'] / target)) if target else .15
    aspect_fit = math.exp(-mismatch * (.55 if a['crop'] == 'flexible' else 1.1))
    if not p['allow_crop'] and mismatch > .4:
        aspect_fit *= .45
        risks.append('Effective source aspect differs from inferred slot; preserve all content with letterboxing/re-layout, never silently crop.')
    elif mismatch > .65:
        risks.append('Source/slot aspect mismatch; check actual protected region and crop loss visually.')

    capacity = CAPACITY[a['title_capacity']]
    excess = max(0., derived['title_units'] / capacity - 1.)
    # A one-word original can often take 1–3 words. Avoid declaring exact pixel capacity.
    title_fit = math.exp(-1.4 * excess)
    char_excess = max(0., derived['title_characters'] / (capacity * 7 + 8) - 1.)
    title_fit *= math.exp(-.7 * char_excess)
    if title_fit < .65:
        risks.append('Title exceeds coarse capacity; compare actual font width/line breaks without rewriting a fixed title.')
    reasons.append(f"Title: {derived['title_units']} approximate units vs {a['title_capacity']} capacity guide ({capacity}); visual typesetting still required.")

    density = {'low': 0, 'medium': 1, 'high': 2}
    shortfall = max(0, density[a['detail_density']] - density[p['auxiliary_text']])
    info_fit = (1., .55, .15)[shortfall]
    if shortfall:
        risks.append('Reference needs more supporting copy than the current content budget; no padding with fabricated facts.')
    roles = set(o['roles'])
    if roles & {'table', 'number'}:
        risks.append('Numbers/tables require meaningful content mapping; no automatic import of source values.')

    adaptation = 1.
    if native in {'graphic', 'type', 'illustration', 'diagram'}:
        adaptation -= .22 if insertion in {'rect', 'full', 'band'} else .4
        risks.append('Original is graphic/type/illustration: proposed photo insertion must preserve the core visual structure.')
        if textual and insertion in {'mask', 'cutout', 'negative'}:
            adaptation -= .2
        if not p['allow_duotone'] or p['preserve_colors']:
            adaptation -= .12
            risks.append('Color/tonal transformations restricted; check whether reference language survives unchanged source colors.')
    # Original poster aspect, distinct from source-slot aspect. Collections are assessed after subimage selection.
    rw, rh = ref['size']
    poster_aspect = rw / rh
    if kind == 'single_design' and abs(math.log(poster_aspect / .75)) > .6:
        adaptation -= .2
        risks.append('Original poster has an extreme aspect vs 3:4; retain structure when reframing.')
    if o['visible_motifs'] >= 3 and kind == 'single_design':
        adaptation -= .08
        risks.append('Multiple motifs in original: reuse genuine source regions; do not invent extra subjects/cases.')
    if kind == 'collection_page':
        adaptation -= .3
        risks.append('Collection page: MUST select and inspect one child design before generation. This parent score is provisional.')
    elif kind == 'specimen_page':
        adaptation -= .2
        risks.append('Specimen/detail page: identify a concrete layout/region, and map supporting content before use.')
    reasons.append('Supporting content: ' + p['auxiliary_text'] + ' available vs ' + a['detail_density'] + ' reference density.')

    # User style preferences break close compatibility ties; they do not override source retention.
    style = .5
    if p['palette']:
        style += .3 * len(set(p['palette']) & set(o['palette'])) / len(set(p['palette']))
    if 'energy' in p:
        style += .2 if p['energy'] == o['energy'] else -.1
    components = dict(source_fit=max(0., fit), aspect_fit=aspect_fit, title_fit=title_fit, supporting_copy=info_fit,
                      adaptation_ease=max(0., adaptation), style_fit=max(0., min(1., style)))
    weights = dict(source_fit=.34, aspect_fit=.15, title_fit=.18, supporting_copy=.15, adaptation_ease=.14, style_fit=.04)
    utility = sum(components[k] * weights[k] for k in components)
    return dict(id=entry['id'], label=ref['label'], image=entry['image'], image_absolute=str((ROOT / entry['image']).resolve()),
        contact_sheet_absolute=str((ROOT/ref['contact_sheet']).resolve()), family=entry['family'], kind=kind,
        compatibility_utility=round(utility, 5), components={k: round(v, 4) for k,v in components.items()},
        proposed_insertion=a, observed=o, permitted_route=permitted,
        region_selection_required=kind!='single_design', reasons=reasons, risks=risks,
        evidence=entry['review'])


def rank(raw, limit=12, reference=None):
    if type(limit) is not int or not 1 <= limit <= 170:
        raise ValueError('limit must be between 1 and 170')
    p, derived = validate_profile(raw)
    catalog = read_json(ROOT/'references/catalog.json')
    index = read_json(ROOT/'references/matching-index.json')
    refs = {r['id']: r for r in catalog['references']}
    entries = index['entries']
    creative = load_creative_index(ROOT)
    if index.get('schema_version') != 1 or len(entries)!=len(refs) or {e['id'] for e in entries}!=set(refs):
        raise ValueError('matching index schema/coverage mismatch; rebuild or visually browse the catalog')
    if reference is not None and reference not in refs:
        raise ValueError('reference must be between 1 and 170')
    checked, stale = [], []
    for entry in entries:
        path = ROOT/entry['image']
        if entry['image'] != refs[entry['id']]['image'] or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['image_sha256']:
            stale.append(entry['id'])
        else:
            checked.append(entry)
        reading=creative[entry['id']]
        if reading['image']!=entry['image'] or reading['image_sha256']!=entry['image_sha256']:
            raise ValueError('creative/layout image evidence mismatch; re-open reference and refresh both records')
    if reference in stale:
        raise ValueError('requested reference has stale/missing image evidence; inspect and refresh its dossier first')
    pool = [score_entry(e, refs[e['id']], p, derived) for e in checked if reference is None or e['id']==reference]
    for candidate in pool:
        candidate['creative_summary']=creative_summary(creative[candidate['id']])
        candidate['creative_transfer_status']='not_reviewed'
        candidate['generation_ready']=False
        candidate['auto_generation_eligible']=creative[candidate['id']]['default_usage']!='critique_only'
        if not candidate['auto_generation_eligible']:
            candidate['risks'].append('Critique/negative example page: do not automatically treat the criticized appearance as a recommended cover template.')
    if not pool:
        raise ValueError('no references with current image evidence; visually review/rebuild index')
    digest = json.dumps(p, sort_keys=True, ensure_ascii=False)
    def tie(item):
        return hashlib.sha256((digest + ':' + str(item['id'])).encode()).hexdigest()
    # Mild family diversity affects shortlist order, not base utility. No ID/start-reference preference.
    selected, used = [], Counter()
    while pool and len(selected) < limit:
        def priority(item):
            penalty = min(.08, .04 * used[item['family']])
            return (-(item['compatibility_utility'] - penalty), tie(item))
        best = min(pool, key=priority)
        penalty = min(.08, .04 * used[best['family']])
        best['shortlist_diversity_penalty'] = penalty
        selected.append(best)
        used[best['family']] += 1
        pool.remove(best)
    return dict(schema_version=1,mode='user_selected' if reference is not None else 'automatic_shortlist',
        evaluated_count=len(checked) if reference is None else 1,library_count=len(refs),
        stale_excluded_ids=stale,derived_source=derived,source_profile=p,
        score_meaning='Compatibility heuristic only; not visual similarity, confidence, or a calibrated probability. Parent-page scores require child selection.',
        selection_status='awaiting_core_idea_transfer_review',
        creative_gate='Read selected full record with creative.py --id. Map core idea and all must_survive relations to actual source. Only a supported/adaptable visual mapping may generate; unsupported/uncertain candidates cannot win on layout utility. No numeric creative score.',
        next_step='Inspect source and at least three plausible full-image candidates (unless user-selected). Compare distinctive strengths and core relations BEFORE layout utility; reject lost creative mechanisms. Pass generation_anchor and core_checks into the image task card. Expand shortlist when weak. No generation yet.',
        candidates=selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--limit', type=int, default=12)
    parser.add_argument('--reference', type=int, help='user explicitly selected reference; bypass automatic ranking')
    args = parser.parse_args()
    try:
        print(json.dumps(rank(read_json(args.profile), args.limit, args.reference), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
