import csv,json,shutil,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reviewctl as rc
import routes
MODULE=Path(__file__).resolve().parents[4]/'test-fixtures'
def csvwrite(p,records):
 fields=list(records[0]) if records else rc.M['triage_fields']
 with Path(p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
def comment(**changes):
 d=dict.fromkeys(rc.M['triage_fields'],'');d.update(comment_id='MOCK-X',reviewer='MOCK',section='Conclusion',issue='MOCK unrelated Experiment X request',severity='OPTIONAL',confidence='HIGH',decision='REJECT',decision_reason='Experiment X does not test the fixed arithmetic claim C01 and would not improve its evidence.',evidence_pointer='inputs/handoff/03_claim_registry.yaml C01',required_action='No new experiment; preserve scope.',routing='STAGE3_LOCAL',affected_assets='None',author_decision_needed='false',status='RESOLVED',resolution_record='revision/revision_log.md');d.update(changes);return d
class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'MOCK-review';shutil.copytree(MODULE/'review',self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_A_complete_stage2_intake_snapshot_resume(self):
  r=Path(self.tmp.name)/'fresh';src=Path(__file__).resolve().parents[4]/'test-fixtures/manuscript'
  result=rc.init(r,src,True);self.assertEqual(result['status'],'BASELINE_STRUCTURALLY_COMPLETE');self.assertEqual(rc.state(r)['current_phase'],0);self.assertTrue((r/'input_snapshot/manuscript.md').exists())
  with self.assertRaises(FileExistsError):rc.init(r,src,True)
 def test_B_incomplete_returns_stage2(self):
  (self.root/'reviewed_manuscript.md').write_text('# MOCK outline only\n');self.assertEqual(rc.check(self.root)['status'],'REQUIRES_STAGE2_REVISION')
 def test_C_independent_reports_recorded(self):
  s=rc.state(self.root);contexts=[x['context_id'] for r in s['rounds'].values() for x in r['reviewers'].values()]
  self.assertEqual(len(contexts),6);self.assertEqual(len(set(contexts)),6)
  for n in [1,2]:self.assertTrue(s['rounds'][str(n)]['frozen'])
 def test_D_consensus_required(self):
  (self.root/'round_2/consensus.md').write_text('Status: UNFILLED');self.assertIn('Round consensus 2',rc.check(self.root)['pending'])
 def test_E_all_severities_valid(self):
  for i,level in enumerate(['BLOCKER','MAJOR','MODERATE','MINOR','OPTIONAL']):
   csvwrite(self.root/'round_2/triage.csv',[comment(comment_id=f'MOCK-{i}',severity=level)]);self.assertEqual(rc.triage_errors(self.root),[])
 def test_F_unrelated_experiment_rejected_with_evidence(self):
  csvwrite(self.root/'round_2/triage.csv',[comment()]);self.assertEqual(rc.triage_errors(self.root),[])
  csvwrite(self.root/'round_2/triage.csv',[comment(decision_reason='No')]);self.assertTrue(rc.triage_errors(self.root))
 def test_F_accept_and_partial(self):
  for decision in ['ACCEPT','PARTIALLY_ACCEPT']:
   csvwrite(self.root/'round_2/triage.csv',[comment(decision=decision,decision_reason='Accept the wording clarification but exclude unrelated Experiment X because C01 concerns fixed arithmetic.')]);self.assertEqual(rc.triage_errors(self.root),[])
 def test_G_local_issue_does_not_restart_other_stages(self):
  csvwrite(self.root/'round_2/triage.csv',[comment(decision='ACCEPT',status='OPEN',severity='MODERATE',issue='MOCK wording needs clarification')]);r=rc.check(self.root);self.assertEqual(r['status'],'REVIEW_IN_PROGRESS')
 def test_H_figure_restructure_routes_stage2(self):
  csvwrite(self.root/'round_2/triage.csv',[comment(decision='ACCEPT',routing='STAGE2',status='OPEN',severity='MAJOR',issue='MOCK panels need recomposition')]);self.assertEqual(rc.check(self.root)['status'],'REQUIRES_STAGE2_REVISION')
 def test_I_missing_experiment_requires_evidence(self):
  csvwrite(self.root/'round_2/triage.csv',[comment(decision='AUTHOR_DECISION',routing='STAGE1',status='OPEN',severity='BLOCKER',issue='MOCK expanded central claim lacks experiment')]);self.assertEqual(rc.check(self.root)['status'],'REQUIRES_NEW_EVIDENCE')
 def test_J_polish_numeric_drift(self):
  p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text().replace('mean was 2','mean was 20'));self.assertTrue(rc.polish_diff(self.root)['errors'])
 def test_J_caption_numeric_drift(self):
  p=self.root/'figures/final/Figure_01_caption.md';p.write_text(p.read_text()+' MOCK value 92.6%.');self.assertTrue(rc.polish_diff(self.root)['errors'])
 def test_K_abstract_results_conflict(self):
  p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text().replace('## Abstract','## Abstract\n\nMOCK mean was 20 dimensionless units.'))
  records=rc.rows(self.root/'qa/numeric_occurrences.csv');d=dict(records[0]);d.update(excerpt='MOCK mean was 20 dimensionless units',value='20');records.append(d);csvwrite(self.root/'qa/numeric_occurrences.csv',records)
  self.assertTrue(any('Cross-section' in e for e in rc.numeric_check(self.root)))
 def test_L_actual_reviewer_found_conclusion_overclaim(self):
  first=[]
  for who in 'ABC':first+=rc.read(self.root/f'round_1/reviewer_{who}.json')
  self.assertTrue(first);self.assertTrue(any('conclusion' in str(c).lower() and 'universal' in str(c).lower() for c in first))
  self.assertNotIn('universally reliable',(self.root/'reviewed_manuscript.md').read_text())
 def test_M_unknown_display_and_missing_caption(self):
  p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text()+'\nSee Figure 99.\n');self.assertIn('Unknown display callout Figure 99',rc.mechanical(self.root)['errors'])
  (self.root/'figures/final/Figure_01_caption.md').unlink();self.assertEqual(rc.check(self.root)['status'],'REQUIRES_STAGE2_REVISION')
 def test_N_fresh_packet_contains_no_review_history(self):
  p=self.root/'round_2/packet'
  for name in ['round_1','revision','polishing','qa','decisions']:self.assertFalse((p/name).exists())
  self.assertTrue((p/'reviewed_manuscript.md').exists())
 def test_O_central_blocker_invalidates_ready(self):
  s=rc.state(self.root);s['open_blockers']=['MOCK central evidence absent'];rc.save(self.root,s);r=rc.finalize(self.root)
  self.assertEqual(r['status'],'BLOCKED');self.assertFalse((self.root/'MOCK_REVIEWED_ONLY.md').exists());self.assertFalse((self.root/'REVIEWED_MANUSCRIPT_READY.md').exists())
 def test_P_complete_ready_and_self_contained_handoff(self):
  r=rc.finalize(self.root);self.assertEqual(r['status'],'REVIEWED_MANUSCRIPT_READY',r);self.assertTrue(r['test_only']);self.assertFalse((self.root/'REVIEWED_MANUSCRIPT_READY.md').exists())
  out=Path(self.tmp.name)/'PUBLICATION_HANDOFF';rc.package(self.root,out)
  for rel,h in rc.read(out/'checksums.json').items():self.assertEqual(rc.sha(out/rel),h)
  self.assertTrue((out/'reviewed_manuscript.md').exists());self.assertFalse((out/'manuscript.md').exists());self.assertFalse(list(out.glob('*.tex')))
 def test_Q_specialist_routes_boundary(self):
  for name in rc.M['allowed_specialists']:
   if name.startswith('nature-'):
    self.assertFalse(routes.route(name)['executed'])
   else:
    try: result=routes.route(name)
    except FileNotFoundError: pass  # Optional stages are separately installed.
    else: self.assertFalse(result['executed'])
  for name in rc.M['forbidden_specialists']:
   with self.assertRaises(ValueError):routes.route(name)
 def test_no_unnecessary_rewrite(self):
  before=(self.root/'versions/manuscript_v1_stage2.md').read_text().split('\n\n');after=(self.root/'reviewed_manuscript.md').read_text().split('\n\n')
  self.assertEqual(len(before),len(after));self.assertEqual(sum(a!=b for a,b in zip(before,after)),2)
 def test_fact_source_tampering(self):
  p=self.root/'inputs/handoff/data/mock.csv';p.write_text('value\n200\n');self.assertEqual(rc.check(self.root)['status'],'BLOCKED')
 def test_snapshot_tampering(self):
  (self.root/'input_snapshot/manuscript.md').write_text('MOCK changed original');self.assertTrue(any('snapshot changed' in e for e in rc.check(self.root)['errors']))
 def test_changed_text_invalidates_fresh_round(self):
  p=self.root/'reviewed_manuscript.md';p.write_text(p.read_text()+'\nMOCK extra scientific statement.\n');self.assertIn('Fresh review stale after content changes',rc.check(self.root)['pending'])
 def test_reports_cannot_change_after_freeze(self):
  p=self.root/'round_1/reviewer_A.md';p.write_text(p.read_text()+'Changed');self.assertIn('Frozen report changed',rc.check(self.root)['errors'])
 def test_reopen_retains_issues_and_invalidates_round(self):
  csvwrite(self.root/'round_2/triage.csv',[comment(status='OPEN',severity='MAJOR',decision='ACCEPT')])
  p=self.root/'decisions/reopen.md';p.write_text('MOCK reopen rationale: substantial revised argument needs a new isolated assessment.\n')
  rc.reopen(self.root,2,'decisions/reopen.md')
  self.assertTrue(any(r['comment_id']=='MOCK-X' for r in rc.all_triage(self.root)))
  self.assertNotIn('2',rc.state(self.root)['rounds']);self.assertNotEqual(rc.check(self.root)['status'],'REVIEWED_MANUSCRIPT_READY')
 def test_numeric_map_change_invalidates_audits(self):
  p=self.root/'qa/numeric_occurrences.csv';p.write_text(p.read_text().splitlines()[0]+'\n')
  self.assertFalse(rc.valid_audit(self.root,'numeric_fact_audit'))
 def test_manifest_and_state(self):
  paths=rc.M['always_load']+rc.M['templates']+rc.M['scripts']+list(rc.M['paper_types'].values())
  for group in rc.M['phase_routes'].values():paths+=group
  for rel in paths:self.assertTrue((rc.S/rel).is_file(),rel)
  d=rc.state(self.root);d['current_phase']=11;rc.save(self.root,d)
  with self.assertRaises(ValueError):rc.state(self.root)
if __name__=='__main__':unittest.main(verbosity=2)
