import os
import unittest,tempfile,sys,json,importlib.util,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reviewctl as rc
class MiniTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.root=self.base/'review'
  self.source=Path(__file__).resolve().parents[4]/'test-fixtures/manuscript'
  rc.init(self.root,self.source,True)
  self.note='MOCK software test only: checked fixture evidence and unchanged content; no actual independent scientific review or author approval is asserted.'
  for rel in ['00_baseline_audit.md','revision/changes.md','polishing/language_check.md','decisions/mock.md']:(self.root/rel).write_text(self.note)
 def tearDown(self):self.tmp.cleanup()
 def round(self,n,people='AB'):
  rc.packet(self.root,n)
  for who in people:
   (self.root/f'round_{n}/reviewer_{who}.md').write_text(self.note)
   rc.write(self.root/f'round_{n}/reviewer_{who}.json',[])
   rc.register_report(self.root,n,who,f'MOCK-not-real-context-{n}-{who}')
  rc.freeze_round(self.root,n);(self.root/f'round_{n}/consensus.md').write_text(self.note)
 def risk(self,material=False):
  rc.write(self.root/'revision/risk.json',dict(material_change=material,unresolved_disagreement=False,change_summary=self.note,scientific_and_structural_impact=self.note,evidence_pointers='MOCK round_1/packet/reviewed_manuscript.md compared to reviewed_manuscript.md; no actual review',closure_summary=self.note))
  return rc.assess_risk(self.root,'revision/risk.json')
 def audits(self):
  (self.root/'qa/combined_audit.md').write_text('\n\n'.join('## '+n+'\n'+self.note for n in rc.QA+['fact_lock','issue_closure']))
  rc.audit_all(self.root,'qa/combined_audit.md')
  for g in 'CD':rc.approve(self.root,g,'decisions/mock.md')
 def complete(self):
  self.round(1);rc.approve(self.root,'A','decisions/mock.md');rc.fact_lock(self.root,'revision/changes.md');rc.language_check(self.root,'polishing/language_check.md');self.risk();self.audits()
 def test_single_ledger_and_two_reviewers_ready(self):
  self.assertFalse((self.root/'round_1/triage.csv').exists());self.assertTrue((self.root/'issues.csv').exists())
  self.complete();r=rc.check(self.root);self.assertEqual(r['status'],'REVIEWED_MANUSCRIPT_READY',r)
  self.assertFalse(r['review_coverage']['second_round_performed']);self.assertEqual(r['review_coverage']['language_status'],'NOT_NEEDED')
 def test_one_reviewer_cannot_freeze(self):
  with self.assertRaises(ValueError):self.round(1,'A')
 def test_reused_context_rejected(self):
  rc.packet(self.root,1)
  for who in 'AB':
   (self.root/f'round_1/reviewer_{who}.md').write_text(self.note);rc.write(self.root/f'round_1/reviewer_{who}.json',[])
  rc.register_report(self.root,1,'A','MOCK-shared')
  with self.assertRaises(ValueError):rc.register_report(self.root,1,'B','MOCK-shared')
 def test_material_requires_new_round(self):
  self.complete();self.assertTrue(self.risk(True)['fresh_review_required']);self.audits()
  self.assertIn('Frozen round 2',rc.check(self.root)['pending'])
  self.round(2);self.audits();self.assertEqual(rc.check(self.root)['status'],'REVIEWED_MANUSCRIPT_READY')
 def test_current_review_becomes_stale(self):
  self.complete();self.risk(True);self.round(2);self.audits()
  p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text()+'\nMOCK changed scientific interpretation.\n')
  self.assertNotEqual(rc.check(self.root)['status'],'REVIEWED_MANUSCRIPT_READY')
 def test_accepted_major_forces_review_even_if_risk_false(self):
  self.complete();d=dict.fromkeys(rc.M['triage_fields'],'');d.update(comment_id='MOCK-major',reviewer='A',section='Discussion',issue='MOCK material revision',severity='MAJOR',confidence='HIGH',decision='ACCEPT',decision_reason=self.note,evidence_pointer='reviewed_manuscript.md',required_action=self.note,routing='STAGE3_LOCAL',affected_assets='None',author_decision_needed='false',status='RESOLVED',resolution_record='revision/changes.md')
  with (self.root/'issues.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rc.M['triage_fields']);w.writeheader();w.writerow(d)
  self.assertTrue(self.risk(False)['fresh_review_required']);self.audits();self.assertIn('Frozen round 2',rc.check(self.root)['pending'])
 def test_missing_risk_cannot_skip_round2(self):
  self.complete();(self.root/'revision/risk.json').unlink();self.assertNotEqual(rc.check(self.root)['status'],'REVIEWED_MANUSCRIPT_READY')
 def test_risk_changed_invalidates(self):
  self.complete();p=self.root/'revision/risk.json';d=rc.read(p);d['change_summary']='Edited assessment without registration';rc.write(p,d)
  self.assertFalse(rc.valid_risk(self.root))
 def test_noedit_cannot_hide_semantic_change(self):
  self.complete();p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text()+'\nMOCK new unsupported interpretation.\n');self.risk();self.audits()
  self.assertIn('Content changed after no-edit language check',rc.check(self.root)['errors'])
 def test_changed_asset_requires_fresh_review(self):
  self.complete();p=self.root/'figures/final/Figure_01_caption.md';p.write_text(p.read_text()+'\nMOCK changed interpretation.\n')
  self.assertTrue(self.risk()['fresh_review_required'])
 def test_audit_all_needs_every_dimension(self):
  self.complete();(self.root/'qa/combined_audit.md').write_text('## claim_evidence_audit\n'+self.note)
  with self.assertRaises(ValueError):rc.audit_all(self.root,'qa/combined_audit.md')
 def test_package_publication_intake_and_mock_isolation(self):
  self.complete();dest=self.base/'handoff';r=rc.package(self.root,dest);self.assertEqual(r['status'],'REVIEWED_MANUSCRIPT_READY',r)
  self.assertTrue((dest/'MOCK_HANDOFF_ONLY.md').exists());self.assertFalse((dest/'REVIEWED_MANUSCRIPT_READY.md').exists());self.assertTrue((dest/'review_coverage.json').exists())
  p=Path(os.environ.get('DOWNSTREAM_SKILL_ROOT', '/nonexistent/optional-skill'))/'scripts/publicationctl.py'
  if not p.is_file(): self.skipTest('Optional downstream Skill is not installed')
  spec=importlib.util.spec_from_file_location('mini_publication',p);pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
  pub.init(self.base/'publication',dest,True)
  self.assertTrue((self.base/'publication/canonical/reviewed_manuscript.md').exists())
 def test_fact_lock_can_be_refreshed_after_scientific_revision(self):
  self.complete();p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text()+'\nMOCK revised scope within the fixture only.\n')
  rc.fact_lock(self.root,'revision/changes.md');rc.language_check(self.root,'polishing/language_check.md')
  self.risk(True);self.audits();self.assertIn('Frozen round 2',rc.check(self.root)['pending'])
  self.round(2);self.audits();self.assertEqual(rc.check(self.root)['status'],'REVIEWED_MANUSCRIPT_READY')
 def test_unresolved_central_blocker_never_waived(self):
  self.complete();s=rc.state(self.root);s['open_blockers']=['MOCK missing core evidence'];rc.save(self.root,s)
  self.assertEqual(rc.finalize(self.root)['status'],'BLOCKED')
if __name__=='__main__':unittest.main()
