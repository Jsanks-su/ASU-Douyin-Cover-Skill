"""Verify creative readings survive retrieval; no automatic art judgment claim."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
import creative
import matching


class CreativeContract(unittest.TestCase):
    def test_all_references_have_current_specific_readings(self):
        rows=creative.load_index()
        self.assertEqual(set(rows),set(range(1,171)))
        for rid,row in rows.items():
            self.assertEqual(row['id'],rid)
            self.assertEqual(row['image_sha256'],hashlib.sha256((creative.ROOT/row['image']).read_bytes()).hexdigest())
            for key in ('strengths','essential_relations','must_survive','needs_from_input','failure_modes','core_checks'):
                self.assertTrue(isinstance(row[key],list) and all(isinstance(x,str) and x.strip() for x in row[key]))
            self.assertTrue(set(row['mechanisms'])<=set(creative.MECHANISMS))
            self.assertTrue(row['core_idea'] and row['generation_anchor'])
            self.assertEqual(row['evidence']['basis'],'full_image')
            if row['kind']=='collection_page':self.assertTrue(row.get('subdesigns'))

    def test_layout_utility_never_silently_passes_the_creative_gate(self):
        profile=dict(source_type='interface',image_size=[1320,2868],effective_region=[.12,.33,.88,.57],
            title='A spark of inspiration beats all the scheming.',preserve_fields=['claude-opus-5.5','低'],allow_cutout=False)
        result=matching.rank(profile,12)
        for candidate in result['candidates']:
            self.assertFalse(candidate['generation_ready'])
            self.assertEqual(candidate['creative_transfer_status'],'not_reviewed')
            self.assertTrue(candidate['creative_summary']['must_survive'])
        self.assertIn('unsupported',result['creative_gate'])

    def test_full_reading_accessible_after_shortlisting(self):
        p=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/'library.py'),'--id','112'],capture_output=True,text=True,encoding='utf-8',check=True)
        record=json.loads(p.stdout)[0]['creative']
        self.assertEqual(record['id'],112)
        self.assertTrue(record['generation_anchor'] and record['core_checks'])
        self.assertIn('cross_plane',record['mechanisms'])
        self.assertTrue(record['evidence']['user_confirmed_reading'])

    def test_criticism_page_not_automatically_recommended(self):
        profile=dict(source_type='document',image_size=[1200,1600],title='Make the message clear.')
        item=matching.rank(profile,reference=119)['candidates'][0]
        self.assertFalse(item['auto_generation_eligible'])
        self.assertEqual(item['creative_summary']['default_usage'],'critique_only')

    def test_mechanism_comparison_cli_and_invalid_id(self):
        p=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/'creative.py'),'--mechanism','cross_plane'],capture_output=True,text=True,encoding='utf-8',check=True)
        rows=json.loads(p.stdout)
        self.assertIn(112,{r['id'] for r in rows})
        self.assertTrue(all('cross_plane' in r['mechanisms'] for r in rows))
        self.assertGreater(len({r['core_idea'] for r in rows}),1)
        p=subprocess.run([sys.executable,str(SCRIPTS/'creative.py'),'--id','171'],capture_output=True)
        self.assertNotEqual(p.returncode,0)


if __name__=='__main__':unittest.main()
