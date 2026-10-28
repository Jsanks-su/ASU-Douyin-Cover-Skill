"""Behavioral safeguards for source-to-layout matching; no generation or network."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
import matching


def source(**changes):
    p=dict(source_type='object',image_size=[1200,1600],effective_region=[0,0,1,1],
        title='Think before you click.',preserve_fields=[],auxiliary_text='low')
    p.update(changes)
    return p


def by_id(result):
    return {c['id']:c for c in result['candidates']}


class MatchingBehavior(unittest.TestCase):
    def test_entire_library_with_current_image_evidence(self):
        r=matching.rank(source(),170)
        self.assertEqual(r['evaluated_count'],170)
        self.assertEqual(set(by_id(r)),set(range(1,171)))
        self.assertFalse(r['stale_excluded_ids'])
        self.assertEqual(r['selection_status'],'awaiting_core_idea_transfer_review')
        for c in r['candidates']:
            self.assertTrue(Path(c['image_absolute']).is_file())
            self.assertEqual(c['region_selection_required'],c['kind']!='single_design')

    def test_source_readability_changes_choices(self):
        portrait=matching.rank(source(source_type='portrait',preserve_fields=[]),12)
        ui=matching.rank(source(source_type='interface',preserve_fields=['MODEL X and exact slider state'],allow_cutout=False),12)
        self.assertNotEqual([c['id'] for c in portrait['candidates']],[c['id'] for c in ui['candidates']])
        self.assertTrue(all(c['proposed_insertion']['insertion'] in {'full','rect','band','negative'} for c in ui['candidates'][:3]))

    def test_effective_crop_not_phone_frame_controls_aspect(self):
        # Same actual landscape region wrapped in a tall phone screenshot.
        wrapped=source(image_size=[1000,2000],effective_region=[0,.3,1,.6])
        cropped=source(image_size=[1000,600],effective_region=[0,0,1,1])
        a,b=matching.rank(wrapped,170),matching.rank(cropped,170)
        self.assertEqual(a['derived_source']['effective_aspect'],b['derived_source']['effective_aspect'])
        self.assertEqual({k:v['compatibility_utility'] for k,v in by_id(a).items()},
                         {k:v['compatibility_utility'] for k,v in by_id(b).items()})
        untrimmed=matching.rank(source(image_size=[1000,2000]),12)
        self.assertNotEqual([c['id'] for c in untrimmed['candidates']],[c['id'] for c in a['candidates'][:12]])

    def test_long_title_and_support_budget_have_material_effect(self):
        short=by_id(matching.rank(source(title='Think.'),170))
        long=by_id(matching.rank(source(title='A better question can save hours of clicking through tools before you know what you actually need to accomplish.'),170))
        brief=[k for k,c in short.items() if c['proposed_insertion']['title_capacity']=='brief']
        self.assertTrue(all(long[k]['compatibility_utility']<short[k]['compatibility_utility'] for k in brief))
        rich=by_id(matching.rank(source(auxiliary_text='high'),170))
        dense=[k for k,c in short.items() if c['proposed_insertion']['detail_density']=='high']
        low_same=by_id(matching.rank(source(),170))
        self.assertTrue(all(rich[k]['compatibility_utility']>low_same[k]['compatibility_utility'] for k in dense))

    def test_explicit_reference_does_not_get_replaced(self):
        r=matching.rank(source(source_type='interface',allow_cutout=False),reference=151)
        self.assertEqual([c['id'] for c in r['candidates']],[151])
        self.assertTrue(r['candidates'][0]['risks'])
        c=matching.rank(source(),reference=65)['candidates'][0]
        self.assertTrue(c['region_selection_required'])
        self.assertEqual(c['kind'],'collection_page')

    def test_cutout_permission_is_not_silently_ignored(self):
        r=matching.rank(source(allow_cutout=False),170)
        blocked=[c for c in r['candidates'] if c['proposed_insertion']['insertion'] in {'cutout','mask'}]
        self.assertTrue(blocked)
        self.assertTrue(all(not c['permitted_route'] for c in blocked))

    def test_visual_identity_does_not_get_mistaken_for_readable_ui(self):
        p=source(source_type='food',preserve_features=['wide ribbon noodles','blue fish motif on bowl'])
        plain=by_id(matching.rank(source(source_type='food'),170))
        protected=by_id(matching.rank(p,170))
        self.assertEqual({k:v['components']['source_fit'] for k,v in plain.items()},
                         {k:v['components']['source_fit'] for k,v in protected.items()})
        textual=by_id(matching.rank(source(source_type='food',preserve_fields=['nutrition label 100g']),170))
        self.assertNotEqual({k:v['components']['source_fit'] for k,v in textual.items()},
                            {k:v['components']['source_fit'] for k,v in protected.items()})

    def test_bad_profiles_fail_with_actionable_errors(self):
        invalid=[dict(typo=True),dict(source_type='AI'),dict(image_size=[0,1600]),dict(image_size=[True,1600]),
                 dict(effective_region=[0,0,2,1]),dict(effective_region=[.8,0,.2,1]),dict(effective_region=[0,0,float('nan'),1]),
                 dict(allow_cutout='false'),dict(title=' '),dict(preserve_fields='all'),dict(energy='loud'),dict(palette=['bluw'])]
        for change in invalid:
            with self.subTest(change=change),self.assertRaises(ValueError):
                matching.rank(source(**change))
        for limit in (0,171,-1,True):
            with self.assertRaises(ValueError): matching.rank(source(),limit)

    def test_portable_package_and_stale_asset_evidence(self):
        # Full relative tree in a different root; source data is not stored in the package.
        original_root=matching.ROOT
        # Keep the isolated directory under the caller's workspace (Windows app
        # sandbox temp ACLs may permit creation but reject child-directory writes).
        test_root=Path.cwd().resolve()
        with tempfile.TemporaryDirectory(prefix='cover-matching-',dir=test_root) as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to(test_root))
            relocated=Path(temp)/'moved-skill'
            shutil.copytree(original_root/'assets',relocated/'assets')
            shutil.copytree(original_root/'references',relocated/'references')
            shutil.copytree(original_root/'scripts',relocated/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
            p=Path(temp)/'profile.json'
            p.write_text(json.dumps(source()),encoding='utf-8')
            proc=subprocess.run([sys.executable,'-X','utf8',str(relocated/'scripts/library.py'),'--profile',str(p),'--limit','3'],cwd=temp,capture_output=True,text=True,encoding='utf-8',check=True)
            result=json.loads(proc.stdout)
            self.assertEqual(result['evaluated_count'],170)
            self.assertTrue(all(Path(c['image_absolute']).is_relative_to(relocated) for c in result['candidates']))
            target=relocated/'assets/posters/ref-001.jpg'
            target.write_bytes(target.read_bytes()+b'changed')
            matching.ROOT=relocated
            try:
                changed=matching.rank(source(),170)
                self.assertEqual(changed['stale_excluded_ids'],[1])
                self.assertEqual(changed['evaluated_count'],169)
                self.assertNotIn(1,by_id(changed))
                with self.assertRaisesRegex(ValueError,'stale'): matching.rank(source(),reference=1)
                target.write_bytes((original_root/'assets/posters/ref-001.jpg').read_bytes())
                index_path=relocated/'references/creative-index.json'
                creative_index=json.loads(index_path.read_text(encoding='utf-8'))
                creative_index['entries'][0]['image_sha256']='0'*64
                index_path.write_text(json.dumps(creative_index,ensure_ascii=False),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'creative/layout'):matching.rank(source())
            finally:
                matching.ROOT=original_root

    def test_old_browser_modes_and_conflicting_flags(self):
        for args in (['--id','151'],['--sheets'],['--tags','photographic','--limit','3']):
            r=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/'library.py'),*args],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue(json.loads(r.stdout))
        for args in (['--id','171'],['--limit','0'],['--id','151','--sheets'],['--reference','151']):
            r=subprocess.run([sys.executable,str(SCRIPTS/'library.py'),*args],capture_output=True)
            self.assertNotEqual(r.returncode,0)


if __name__=='__main__':
    unittest.main()
