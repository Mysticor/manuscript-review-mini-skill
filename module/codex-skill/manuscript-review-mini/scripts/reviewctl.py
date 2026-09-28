"""Review mechanics; semantic judgment, reviewer execution and approval belong to agents/users."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,csv,hashlib,json,re,shutil,sys,tempfile
import yaml
S=Path(__file__).resolve().parents[1];M=yaml.safe_load((S/'manifest.yaml').read_text())
STATUSES={'REVIEW_IN_PROGRESS','REQUIRES_AUTHOR_DECISION','REQUIRES_STAGE2_REVISION','REQUIRES_NEW_EVIDENCE','REVIEWED_WITH_MINOR_ISSUES','REVIEWED_MANUSCRIPT_READY','BLOCKED'}
QA=['claim_evidence_audit','methods_experiment_audit','statistics_audit','citation_audit','figure_table_audit','numeric_fact_audit','consistency_audit']
CONTENT=['reviewed_manuscript.md','reviewed_supplementary.md','references.bib','figures','tables','inputs','source_verification','manuscript_blueprint','manuscript_asset_manifest.csv','terminology_ledger.yaml','section_registry.csv','claim_evidence_map.csv','numeric_trace.csv']
# Shared project coordination; stage logic remains local.
import sys as _coord_sys
_coord_sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'workflow-contract'))
import project_contract as _coord

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=p.parent,delete=False,encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);tmp=Path(f.name)
 tmp.replace(p)
def rows(p):
 with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def local(root,rel):
 if not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('Expected relative path: '+str(rel))
 root=Path(root).resolve();p=(root/rel).resolve()
 if not p.is_relative_to(root) or not p.is_file():raise ValueError('Missing/external file: '+rel)
 return p
def state(root):
 d=read(Path(root)/'state.json');required=read(S/'templates/state.json')
 if any(k not in d for k in required):raise ValueError('Missing state field')
 if type(d['current_phase'])!=int or d['current_phase'] not in range(10):raise ValueError('Invalid phase')
 if d['paper_type'] not in M['paper_types'] or d['review_readiness'] not in STATUSES:raise ValueError('Invalid state enum')
 for k in ['open_blockers','major_concerns','author_decisions']:
  if not isinstance(d[k],list):raise ValueError('Expected state list '+k)
 return d
def save(root,d):d['last_updated']=now();write(Path(root)/'state.json',d)
def filled(p):return Path(p).is_file() and len(Path(p).read_text().strip())>=35 and not re.search(r'\[TO_COMPLETE\]|Status: UNFILLED',Path(p).read_text(),re.I)
def files(root):
 root=Path(root);found=[]
 for name in CONTENT:
  p=root/name
  if p.is_file():found.append(p)
  elif p.is_dir():found += [q for q in p.rglob('*') if q.is_file()]
 return sorted(found)
def fingerprint(root):
 root=Path(root);h=hashlib.sha256()
 for p in files(root):h.update(str(p.relative_to(root)).encode());h.update(p.read_bytes())
 s=state(root);h.update(json.dumps({k:s[k] for k in ['paper_type','target_journal']},sort_keys=True).encode())
 return h.hexdigest()
def copy_input(src,dst,exclude=None):
 for p in src.iterdir():
  if exclude and p.resolve()==exclude.resolve():continue
  if p.is_symlink():raise ValueError('Materialize source symlinks before import')
  for q in p.rglob('*') if p.is_dir() else []:
   if q.is_symlink():raise ValueError('Materialize nested source symlinks')
  if p.is_dir():shutil.copytree(p,dst/p.name)
  else:shutil.copy2(p,dst/p.name)

def init(root,source,test_only=False):
 root=Path(root).resolve();source=Path(source).resolve()
 if root.exists():raise FileExistsError('Review exists; resume state')
 if root.is_relative_to(source) and root.parent!=source:raise ValueError('Use immediate review/ child or external sibling directory')
 if source==root or source.is_relative_to(root):raise ValueError('Review must not contain source directory')
 if not (source/'manuscript.md').exists():raise ValueError('Stage2 manuscript.md required; adapt explicit equivalent input first')
 source_state=read(source/'state.json') if (source/'state.json').exists() else {}
 if source_state.get('test_only') and not test_only:raise ValueError('MOCK Stage2 requires explicit mock review')
 root.mkdir(parents=True);snap=root/'input_snapshot';snap.mkdir();copy_input(source,snap,root)
 write(root/'input_snapshot_checksums.json',{str(p.relative_to(snap)):sha(p) for p in snap.rglob('*') if p.is_file()})
 for n in CONTENT:
  srcname={'reviewed_manuscript.md':'manuscript.md','reviewed_supplementary.md':'supplementary.md'}.get(n,n);p=snap/srcname
  if p.is_dir():shutil.copytree(p,root/n)
  elif p.exists():shutil.copy2(p,root/n)
 for d in ['round_1','round_2','revision','polishing','qa','versions','decisions']:(root/d).mkdir()
 shutil.copy2(root/'reviewed_manuscript.md',root/'versions/manuscript_v1_stage2.md')
 for dest,template in [('00_baseline_audit.md','baseline_audit.md'),('round_1/consensus.md','reviewer_consensus.md'),('round_2/consensus.md','reviewer_consensus.md'),('round_1/triage.csv','triage.csv'),('round_2/triage.csv','triage.csv'),('revision/revision_plan.md','revision_plan.md'),('revision/revision_log.md','revision_log.md'),('revision/unresolved_comments.csv','triage.csv'),('qa/numeric_occurrences.csv','numeric_occurrences.csv'),('qa/claim_evidence_audit.md','claim_evidence_audit.md'),('qa/citation_audit.md','citation_audit.md'),('qa/figure_table_audit.md','figure_table_audit.md'),('qa/consistency_audit.md','consistency_audit.md')]:shutil.copy2(S/'templates'/template,root/dest)
 for name in ['methods_experiment_audit','statistics_audit','numeric_fact_audit','unresolved_items']:(root/'qa'/f'{name}.md').write_text('# '+name+'\nStatus: UNFILLED\n')
 for name in ['polishing_report','fact_lock_audit']:(root/'polishing'/f'{name}.md').write_text('# '+name+'\nStatus: UNFILLED\n')
 d=read(S/'templates/state.json');ptype=source_state.get('paper_type','original_research').replace('_','-');d.update(project=root.parent.name,paper_type=ptype if ptype in M['paper_types'] else 'mixed',target_journal=source_state.get('target_journal') or 'generic',test_only=test_only,review_mode='mini');save(root,d)
 shutil.copy2(S/'templates/triage.csv',root/'issues.csv')
 for n in [1,2]:(root/f'round_{n}/triage.csv').unlink()
 for name in ['revision/revision_plan.md','revision/revision_log.md','revision/unresolved_comments.csv']:(root/name).unlink()
 (root/'revision/changes.md').write_text('# Revision actions and outcomes\nStatus: UNFILLED\n')
 for name in QA:(root/'qa'/f'{name}.md').unlink()
 shutil.copy2(S/'templates/combined_audit.md',root/'qa/combined_audit.md')
 return baseline(root)

def baseline(root):
 root=Path(root);issues=[]
 for name in ['reviewed_manuscript.md','references.bib','manuscript_asset_manifest.csv','claim_evidence_map.csv','section_registry.csv']:
  if not (root/name).is_file():issues.append('Missing '+name)
 if not (root/'reviewed_supplementary.md').is_file() and not filled(root/'supplementary_not_required.md'):issues.append('Missing supplementary or explicit not-required rationale')
 text=(root/'reviewed_manuscript.md').read_text()
 if len(text)<200 or re.search(r'\[(?:TO_COMPLETE|DATA_REQUIRED|SOURCE_REQUIRED|VERIFY)[^\]]*\]',text):issues.append('Incomplete prose/placeholders')
 if (root/'section_registry.csv').exists():
  for r in rows(root/'section_registry.csv'):
   match=re.search(r'^#{1,6}\s+'+re.escape(r['heading'])+r'\s*$',text,re.M)
   if not match:issues.append('Missing approved section '+r['heading'])
   else:
    body=re.split(r'^#{1,6}\s+',text[match.end():],maxsplit=1,flags=re.M)[0]
    if len(body.strip())<45:issues.append('Incomplete approved section '+r['heading'])
 if (root/'manuscript_asset_manifest.csv').exists():
  for a in rows(root/'manuscript_asset_manifest.csv'):
   for field in ['final_path','caption_path']:
    try:local(root,a[field])
    except ValueError as e:issues.append(str(e))
 result={'status':'REQUIRES_STAGE2_REVISION' if issues else 'BASELINE_STRUCTURALLY_COMPLETE','issues':issues,'semantic_audit_required':True}
 write(root/'qa/baseline_scan.json',result);s=state(root);s['review_readiness']='REQUIRES_STAGE2_REVISION' if issues else 'REVIEW_IN_PROGRESS';save(root,s)
 return result

def packet(root,round_number):
 root=Path(root);s=state(root)
 if baseline(root)['issues']:raise ValueError('Incomplete Stage2; no formal round')
 if not filled(root/'00_baseline_audit.md'):raise ValueError('Complete substantive baseline audit first')
 if round_number not in [1,2]:raise ValueError('Supported rounds 1 and 2; use explicit versioned review for additional rounds')
 dest=root/f'round_{round_number}/packet'
 if dest.exists():raise FileExistsError('Frozen packet exists; use a documented new round version')
 if round_number==2 and (not language_ok(root) or not valid_audit(root,'fact_lock') or polish_diff(root)['errors']):raise ValueError('Finish fact-safe polishing before fresh review')
 dest.mkdir()
 for p in files(root):
  out=dest/p.relative_to(root);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
 write(dest/'packet_checksums.json',{str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()})
 s=state(root);s['rounds'][str(round_number)]={'content_fingerprint':fingerprint(root),'packet_hash':sha(dest/'packet_checksums.json'),'reviewers':{},'frozen':False};s['review_round']=round_number;save(root,s)
 return {'packet':str(dest),'fresh':round_number==2,'review_history_included':False}

def mini(root):return state(root).get('review_mode')=='mini'
def reviewers_ok(root,r):
 who=set(r.get('reviewers',{}))
 contexts=[v.get('context_id') for v in r.get('reviewers',{}).values()]
 return (set('AB')<=who<=set('ABC') if mini(root) else who==set('ABC')) and all(contexts) and len(contexts)==len(set(contexts))

def risk_record(root):
 a=state(root).get('revision_risk',{})
 try:
  if a.get('fingerprint')!=fingerprint(root) or a.get('issue_hash')!=issue_hash(root):return None
  if a.get('round1_packet_hash')!=state(root)['rounds']['1']['packet_hash']:return None
  p=local(root,a['record'])
  return read(p) if sha(p)==a['hash'] else None
 except (KeyError,ValueError,OSError):return None

def valid_risk(root):return risk_record(root) is not None

def nonprose_changed(root):
 root=Path(root);r=state(root)['rounds'].get('1',{})
 if not r.get('frozen'):return True
 expected=read(root/'round_1/packet/packet_checksums.json')
 current={str(p.relative_to(root)):sha(p) for p in files(root) if p.name not in {'reviewed_manuscript.md','reviewed_supplementary.md'}}
 before={k:v for k,v in expected.items() if Path(k).name not in {'reviewed_manuscript.md','reviewed_supplementary.md'}}
 return current!=before

def needs_fresh(root):
 if not mini(root):return True
 r=risk_record(root)
 if r is None:return True
 if r['material_change'] or r['unresolved_disagreement'] or nonprose_changed(root):return True
 return any(c['severity'] in {'BLOCKER','MAJOR'} and c['decision']!='REJECT' for c in all_triage(root))

def assess_risk(root,record):
 root=Path(root);p=local(root,record);d=read(p)
 if not mini(root):raise ValueError('Risk routing is only available in mini')
 if not state(root)['rounds'].get('1',{}).get('frozen'):raise ValueError('Freeze independent Round1 before risk assessment')
 for k in ['material_change','unresolved_disagreement']:
  if type(d.get(k)) is not bool:raise ValueError('Explicit boolean required: '+k)
 for k in ['change_summary','scientific_and_structural_impact','evidence_pointers','closure_summary']:
  if not isinstance(d.get(k),str) or len(d[k].strip())<25:raise ValueError('Substantive assessment required: '+k)
 s=state(root);s['revision_risk']={'record':record,'hash':sha(p),'fingerprint':fingerprint(root),'issue_hash':issue_hash(root),'round1_packet_hash':s['rounds']['1']['packet_hash']};save(root,s)
 return {'fresh_review_required':needs_fresh(root),'semantic_assessment_required':True}

def audit_all(root,record):
 root=Path(root);p=local(root,record);text=p.read_text()
 names=QA+['fact_lock','issue_closure']
 for name in names:
  found=re.search(r'^## '+re.escape(name)+r'\s*\n(.*?)(?=^## |\Z)',text,re.M|re.S)
  if not found or len(found.group(1).strip())<35 or '[TO_COMPLETE]' in found.group(1):raise ValueError('Substantive audit or justified N/A required: '+name)
 for name in names:audit(root,name,record)
 return {'record':record,'audits':names,'semantic_truth_not_certified':True}

def language_ok(root):
 return state(root)['polishing_status']=='COMPLETE' or (mini(root) and state(root)['polishing_status']=='NOT_NEEDED')

def language_check(root,record):
 root=Path(root);p=local(root,record)
 if not mini(root) or not filled(p):raise ValueError('Mini language assessment record required')
 lock=read(root/'polishing/fact_lock.json')
 if lock['fingerprint']!=fingerprint(root) or polish_diff(root)['errors']:raise ValueError('No-edit assessment requires unchanged fact-locked content')
 s=state(root);s['polishing_status']='NOT_NEEDED';save(root,s);audit(root,'fact_lock',record)
 return {'status':'NOT_NEEDED','reason_record':record}

def coverage(root):
 s=state(root)
 return {'mode':'mini' if mini(root) else 'full','rounds':{n:{'reviewers':sorted(r['reviewers']),'contexts':[v['context_id'] for v in r['reviewers'].values()],'frozen':r.get('frozen',False)} for n,r in s['rounds'].items()},'fresh_review_required':needs_fresh(root) if mini(root) else True,'second_round_performed':bool(s['rounds'].get('2',{}).get('frozen')),'language_status':s['polishing_status'],'scope_note':'Software records of actual review scope; not journal acceptance or equal coverage to six independent reviewers.'}

def register_report(root,round_number,reviewer,context_id):
 root=Path(root);s=state(root);r=s['rounds'][str(round_number)];folder=root/f'round_{round_number}'
 if r['frozen']:raise ValueError('Frozen reports immutable')
 if reviewer not in 'ABC' or len(reviewer)!=1:raise ValueError('Reviewer A/B/C')
 if not context_id:raise ValueError('Actual isolated context ID required')
 used=[v['context_id'] for rd in list(s['rounds'].values())+s.get('round_history',[]) for v in rd['reviewers'].values()]
 if context_id in used:raise ValueError('Independent/fresh reviewer context required')
 p=folder/f'reviewer_{reviewer}.md';j=folder/f'reviewer_{reviewer}.json'
 if not filled(p) or not isinstance(read(j),list):raise ValueError('Complete report and JSON concern array required')
 for c in read(j):
  for key in ['comment_id','issue','severity','claim_pointer','evidence_pointer','resolution_test']:
   if not c.get(key):raise ValueError('Missing report concern '+key)
 r['reviewers'][reviewer]={'context_id':context_id,'report_hash':sha(p),'comments_hash':sha(j),'packet_hash':r['packet_hash']};save(root,s);return r

def freeze_round(root,round_number):
 root=Path(root);s=state(root);r=s['rounds'][str(round_number)]
 if not reviewers_ok(root,r):raise ValueError('Required independent reports missing')
 for who,v in r['reviewers'].items():
  if sha(root/f'round_{round_number}/reviewer_{who}.md')!=v['report_hash'] or sha(root/f'round_{round_number}/reviewer_{who}.json')!=v['comments_hash']:raise ValueError('Report changed before freeze')
 r['frozen']=True;r['frozen_at']=now();save(root,s);return r

def issue_hash(root):
 p=Path(root)/'qa/numeric_occurrences.csv'
 return hashlib.sha256((json.dumps(all_triage(root),sort_keys=True)+(p.read_text() if p.exists() else '')).encode()).hexdigest()

def approve(root,gate,record,accept_minor=False):
 root=Path(root);p=local(root,record)
 if gate not in 'ABCD' or len(gate)!=1 or not filled(p):raise ValueError('Actual decision record required')
 s=state(root);s['author_decisions'].append({'gate':gate,'record':record,'hash':sha(p),'fingerprint':fingerprint(root),'accept_minor':accept_minor,'issue_hash':issue_hash(root),'at':now()});save(root,s)
 return s['author_decisions'][-1]
def approved(root,gate,fresh=False):
 records=[d for d in state(root)['author_decisions'] if d['gate']==gate]
 if not records:return False
 d=records[-1]
 return sha(local(root,d['record']))==d['hash'] and (not fresh or (d['fingerprint']==fingerprint(root) and d.get('issue_hash')==issue_hash(root)))
def audit(root,name,record):
 root=Path(root);p=local(root,record)
 if not filled(p):raise ValueError('Substantive source-grounded audit required')
 s=state(root);s['audit_records'][name]={'status':'PASS','fingerprint':fingerprint(root),'record':record,'hash':sha(p),'issue_hash':issue_hash(root)};save(root,s);return s['audit_records'][name]
def valid_audit(root,name):
 a=state(root)['audit_records'].get(name,{})
 return a.get('status')=='PASS' and a.get('fingerprint')==fingerprint(root) and a.get('issue_hash')==issue_hash(root) and sha(local(root,a['record']))==a.get('hash')
def milestone(root,name):
 if not re.fullmatch(r'[a-zA-Z0-9_-]+',name):raise ValueError('Version name invalid')
 root=Path(root);dest=root/'versions'/f'{name}.md'
 if dest.exists():raise FileExistsError('Version exists')
 shutil.copy2(root/'reviewed_manuscript.md',dest);s=state(root);s['current_manuscript_version']=name;save(root,s);return {'version':str(dest)}
NUM=r'(?<![\w])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?'
def tokens(text):return Counter(re.findall(NUM,text))
def fact_lock(root,record):
 root=Path(root)
 if not approved(root,'A') or not state(root)['rounds'].get('1',{}).get('frozen'):raise ValueError('Frozen Round1 and direction approval required')
 if mini(root):
  if not filled(root/'revision/changes.md'):raise ValueError('Revision actions/outcomes required')
 elif not filled(root/'revision/revision_plan.md') or not filled(root/'revision/revision_log.md'):raise ValueError('Revision plan/log required before polishing')
 if any(r.get('severity') in {'BLOCKER','MAJOR'} and r.get('status')!='RESOLVED' for r in all_triage(root)):raise ValueError('Resolve scientific/major revisions first')
 p=local(root,record)
 if not filled(p):raise ValueError('Describe actual result/condition/claim-boundary lock')
 milestone(root,'before_polishing-'+datetime.now().strftime('%Y%m%d%H%M%S%f') if mini(root) else 'before_polishing')
 d={'fingerprint':fingerprint(root),'record':record,'record_hash':sha(p),'numeric_tokens':dict(tokens((root/'reviewed_manuscript.md').read_text())),'citations':sorted(set(re.findall(r'(?<!\w)@([\w:./-]+)',(root/'reviewed_manuscript.md').read_text()))),'sources':{str(p.relative_to(root)):sha(p) for p in files(root) if p.suffix in {'.csv','.yaml','.bib'} or '/inputs/' in str(p)}}
 d['text_facts']={str(p.relative_to(root)):{'numbers':dict(tokens(p.read_text())), 'citations':sorted(set(re.findall(r'(?<!\w)@([\w:./-]+)',p.read_text())))} for p in files(root) if p.suffix in {'.md','.svg'} and 'inputs' not in p.relative_to(root).parts}
 write(root/'polishing/fact_lock.json',d);return d

def polish_diff(root):
 root=Path(root);d=read(root/'polishing/fact_lock.json');text=(root/'reviewed_manuscript.md').read_text();errors=[]
 if tokens(text)!=Counter(d['numeric_tokens']):errors.append('Numeric token inventory changed during polishing')
 if sorted(set(re.findall(r'(?<!\w)@([\w:./-]+)',text)))!=d['citations']:errors.append('Citations changed during polishing')
 for rel,facts in d.get('text_facts',{}).items():
  t=local(root,rel).read_text()
  if tokens(t)!=Counter(facts['numbers']) or sorted(set(re.findall(r'(?<!\w)@([\w:./-]+)',t)))!=facts['citations']:errors.append('Text/label numeric or citation drift '+rel)
 for rel,h in d['sources'].items():
  if sha(local(root,rel))!=h:errors.append('Locked source changed '+rel)
 return {'errors':errors,'semantic_diff_review_required':True}

def all_triage(root):
 if mini(root):return rows(Path(root)/'issues.csv')
 return sum([rows(Path(root)/f'round_{n}/triage.csv') for n in [1,2]],[])
def triage_errors(root):
 errors=[];seen=set()
 for r in all_triage(root):
  if any(k not in r for k in M['triage_fields']):errors.append('Missing triage column');continue
  if not r['comment_id'] or r['comment_id'] in seen:errors.append('Duplicate/empty comment ID')
  seen.add(r['comment_id'])
  if r['severity'] not in {'BLOCKER','MAJOR','MODERATE','MINOR','OPTIONAL'} or r['decision'] not in {'ACCEPT','PARTIALLY_ACCEPT','REJECT','AUTHOR_DECISION'}:errors.append('Invalid triage enum')
  if r['routing'] not in {'STAGE3_LOCAL','STAGE2','STAGE1'}:errors.append('Invalid issue routing')
  if r['status'] not in {'OPEN','RESOLVED','DEFERRED'}:errors.append('Invalid issue status')
  if r['decision'] in {'REJECT','PARTIALLY_ACCEPT'} and (len(r['decision_reason'])<25 or not r['evidence_pointer']):errors.append('Unsupported rejection/partial acceptance '+r['comment_id'])
  if r['status']=='RESOLVED' and not filled(local(root,r['resolution_record'])):errors.append('Missing resolution record '+r['comment_id'])
 for n in [1,2]:
  for p in (Path(root)/f'round_{n}').glob('reviewer_*.json'):
   for c in read(p):
    if c['comment_id'] not in seen:errors.append('Untriaged reviewer comment '+c['comment_id'])
 return errors

def numeric_check(root):
 root=Path(root);errors=[];values={}
 for r in rows(root/'qa/numeric_occurrences.csv'):
  p=local(root,r['location']);text=p.read_text();excerpt=r['excerpt']
  if not excerpt or excerpt not in text:errors.append('Numeric occurrence absent '+r['fact_id'])
  if r['value'] not in re.findall(NUM,excerpt):errors.append('Numeric value not in cited excerpt '+r['fact_id'])
  source=local(root,r['source_file']);actual=r['source_value']
  if source.suffix=='.csv':
   matches=[x for x in rows(source) if x.get('result_id',x.get('fact_id'))==r['fact_id']]
   if len(matches)==1 and r['source_field']=='value' and matches[0].get('unit')!=r['source_unit']:errors.append('Authoritative unit mismatch '+r['fact_id'])
   if len(matches)!=1 or matches[0].get(r['source_field'])!=actual:errors.append('Authoritative fact mismatch '+r['fact_id'])
  else:errors.append('Unsupported fact-source format: supply a source-grounded CSV fact ledger')
  if r['value']!=actual or r['unit']!=r['source_unit']:errors.append('Numeric/unit conflict '+r['fact_id'])
  key=(r['fact_id'],r['source_field']);values.setdefault(key,set()).add((r['value'],r['unit']))
 for key,v in values.items():
  if len(v)>1:errors.append('Cross-section numeric conflict '+str(key))
 return errors

def mechanical(root):
 root=Path(root);errors=[];paper=(root/'reviewed_manuscript.md').read_text();texts=[paper]
 if (root/'reviewed_supplementary.md').exists():texts.append((root/'reviewed_supplementary.md').read_text())
 ids=set()
 for a in rows(root/'manuscript_asset_manifest.csv'):
  aid=a['manuscript_asset_id']
  if aid in ids:errors.append('Duplicate display ID '+aid)
  ids.add(aid)
  final=local(root,a['final_path']);caption=local(root,a['caption_path'])
  if a.get('sha256') and sha(final)!=a['sha256']:errors.append('Final asset hash mismatch '+aid)
  if not filled(caption):errors.append('Missing meaningful caption '+aid)
  texts.append(caption.read_text())
  if aid not in '\n'.join(texts[:2]):errors.append('Unreferenced display '+aid)
 for label in re.findall(r'\b(?:Figure|Table)\s+\d+\b','\n'.join(texts)):
  if label not in ids:errors.append('Unknown display callout '+label)
 bib=(root/'references.bib').read_text();keys=re.findall(r'@\w+\s*[{(]\s*([^,\s]+)\s*,',bib)
 if len(keys)!=len(set(keys)):errors.append('Duplicate bibliography key')
 for key in set(re.findall(r'(?<!\w)@([\w:./-]+)','\n'.join(texts)))-set(keys):errors.append('Missing bibliography key '+key)
 if re.search(r'\[(?:DATA_REQUIRED|SOURCE_REQUIRED|VERIFY|TO_COMPLETE)[^\]]*\]','\n'.join(texts)):errors.append('Unresolved evidence placeholder')
 ledger=root/'terminology_ledger.yaml'
 if ledger.exists():
  terms=yaml.safe_load(ledger.read_text()).get('terms',[])
  if isinstance(terms,list):
   for term in terms:
    for variant in term.get('forbidden_variants',[]):
     if re.search(r'(?<!\w)'+re.escape(variant)+r'(?!\w)','\n'.join(texts)):errors.append('Terminology variant '+variant)
 errors+=numeric_check(root)
 warnings=[{'phrase':m.group(),'location':'reviewed_manuscript.md','offset':m.start()} for m in re.finditer(r'\b(proves|universally|universal|causes|substantially outperforms|generalizable|state-of-the-art)\b',paper,re.I)]
 scan=[]
 for p in files(root):
  if p.suffix in {'.md','.csv','.svg'} and 'inputs' not in p.relative_to(root).parts:
   scan += [{'path':str(p.relative_to(root)),'token':m.group(),'offset':m.start()} for m in re.finditer(NUM,p.read_text())]
 write(root/'qa/numeric_scan.json',scan)
 return {'errors':errors,'semantic_overclaim_candidates':warnings,'numeric_occurrence_coverage_requires_agent':True}

def _check(root):
 root=Path(root);s=state(root);errors=[];pending=[]
 snap=root/'input_snapshot'
 for rel,h in read(root/'input_snapshot_checksums.json').items():
  if sha(local(snap,rel))!=h:errors.append('Input snapshot changed '+rel)
 if baseline(root)['issues']:return {'status':'REQUIRES_STAGE2_REVISION','errors':baseline(root)['issues'],'pending':[],'test_only':s['test_only']}
 errors+=triage_errors(root);errors+=mechanical(root)['errors']
 snapfacts=root/'inputs/handoff'
 if (snapfacts/'04_results_facts.csv').exists():
  for row in rows(snapfacts/'04_results_facts.csv'):
   for field,hfield in [('source_file','source_sha256'),('analysis_script','analysis_sha256')]:
    source=local(snapfacts,row[field])
    if row.get(hfield) and sha(source)!=row[hfield]:errors.append('Actual evidence hash mismatch '+row['result_id'])
 if not filled(root/'00_baseline_audit.md'):pending.append('Substantive baseline audit')
 if mini(root):
  if not valid_risk(root):pending.append('Current evidence-backed revision risk assessment required')
  if not valid_audit(root,'issue_closure'):pending.append('Current issue closure and regression check required')
 for n in ([1,2] if not mini(root) or needs_fresh(root) or '2' in s['rounds'] else [1]):
  r=s['rounds'].get(str(n),{})
  if not r.get('frozen'):pending.append('Frozen round '+str(n));continue
  if not reviewers_ok(root,r):errors.append('Required independent reviewers missing')
  folder=root/f'round_{n}';packetdir=folder/'packet'
  if sha(packetdir/'packet_checksums.json')!=r['packet_hash']:errors.append('Packet manifest changed')
  for rel,h in read(packetdir/'packet_checksums.json').items():
   if sha(local(packetdir,rel))!=h:errors.append('Frozen reviewer input changed '+rel)
  for who,v in r['reviewers'].items():
   if sha(folder/f'reviewer_{who}.md')!=v['report_hash'] or sha(folder/f'reviewer_{who}.json')!=v['comments_hash']:errors.append('Frozen report changed')
  if not filled(folder/'consensus.md'):pending.append('Round consensus '+str(n))
  if n==2 and r['content_fingerprint']!=fingerprint(root):pending.append('Fresh review stale after content changes')
 triage=all_triage(root);openitems=[r for r in triage if r['status']!='RESOLVED']
 new=s['requires_new_evidence'] or any(r['routing']=='STAGE1' for r in openitems)
 back=any(r['routing']=='STAGE2' for r in openitems)
 author=any(r['decision']=='AUTHOR_DECISION' or r['author_decision_needed'].lower()=='true' for r in openitems)
 if s['open_blockers'] or any(r['severity']=='BLOCKER' for r in openitems):errors.append('Unresolved central blocker')
 if s['major_concerns'] or any(r['severity'] in {'MAJOR','MODERATE'} for r in openitems):pending.append('Open major/moderate concerns')
 for name in QA+['fact_lock']:
  if not valid_audit(root,name):pending.append('Current audit required '+name)
 if not language_ok(root):pending.append('Fact-safe polishing incomplete')
 elif polish_diff(root)['errors']:errors+=polish_diff(root)['errors']
 if mini(root) and s['polishing_status']=='NOT_NEEDED' and read(root/'polishing/fact_lock.json')['fingerprint']!=fingerprint(root):errors.append('Content changed after no-edit language check')
 for g in 'ACD':
  if not approved(root,g,g in 'CD'):pending.append('Author Gate '+g)
 if any(r['routing']=='STAGE1' for r in triage) and not approved(root,'B'):pending.append('Author evidence Gate B')
 if not s['test_only'] and re.search(r'\b(MOCK|FIXTURE)\b','\n'.join(p.read_text(errors='replace') for p in files(root) if p.suffix in {'.md','.bib','.csv','.json','.yaml'})):errors.append('MOCK content cannot become production-ready')
 minor=bool(openitems);decisions=[d for d in s['author_decisions'] if d['gate']=='D'];minoraccepted=bool(decisions and decisions[-1].get('accept_minor') and approved(root,'D',True))
 status='REQUIRES_NEW_EVIDENCE' if new else 'REQUIRES_STAGE2_REVISION' if back else 'BLOCKED' if errors else 'REQUIRES_AUTHOR_DECISION' if author else 'REVIEW_IN_PROGRESS' if pending else 'REVIEWED_WITH_MINOR_ISSUES' if minor and not minoraccepted else 'REVIEWED_MANUSCRIPT_READY'
 return {'status':status,'errors':sorted(set(errors)),'pending':sorted(set(pending)),'test_only':s['test_only'],'fingerprint':fingerprint(root),'remaining_minor':[r['comment_id'] for r in openitems if r['severity'] in {'MINOR','OPTIONAL'}], 'review_coverage':coverage(root)}
def check(root):
 try:return _check(root)
 except (ValueError,KeyError,TypeError,AttributeError,OSError,yaml.YAMLError) as e:return {'status':'BLOCKED','errors':['Malformed/missing input: '+str(e)],'pending':[],'test_only':True}
def finalize(root):
 root=Path(root);r=check(root);s=state(root);s['review_readiness']=r['status']
 for name in ['REVIEWED_MANUSCRIPT_READY.md','MOCK_REVIEWED_ONLY.md']:
  p=root/name
  if p.exists():p.rename(root/'versions'/(datetime.now().strftime('%Y%m%d%H%M%S%f')+'-'+name))
 if r['status']=='REVIEWED_MANUSCRIPT_READY':
  name='MOCK_REVIEWED_ONLY.md' if r['test_only'] else 'REVIEWED_MANUSCRIPT_READY.md';(root/name).write_text(r['status']+'\n'+('MOCK software acceptance only.\n' if r['test_only'] else '')+'Scientific review milestone; not typeset, submitted or editorially accepted.\n');s['current_phase']=9
 else:
  s['current_phase']=4 if r['status'] in {'REQUIRES_NEW_EVIDENCE','REQUIRES_STAGE2_REVISION'} else 8
 s['next_actions']=r['errors']+r['pending'] if r['status']!='REVIEWED_MANUSCRIPT_READY' else ['Stop at Stage3; wait for explicit Stage4 request']
 save(root,s);write(root/'qa/readiness.json',r);return r

def package(root,destination):
 root=Path(root).resolve();dest=Path(destination).resolve();r=finalize(root)
 if r['status'] not in {'REVIEWED_MANUSCRIPT_READY','REVIEWED_WITH_MINOR_ISSUES'}:return r
 if dest.exists():raise FileExistsError('Use a new publication handoff version')
 if root.is_relative_to(dest):raise ValueError('Destination must not contain review')
 dest.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.publication-',dir=dest.parent))
 try:
  for p in files(root):
   out=stage/p.relative_to(root);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
  write(stage/'readiness.json',r);write(stage/'unresolved_minor_items.json',r['remaining_minor'])
  write(stage/'review_coverage.json',coverage(root))
  profile=root/'inputs/handoff/01_target_journal_profile.md'
  if profile.exists():shutil.copy2(profile,stage/'target_journal_profile.md')
  else:(stage/'target_journal_profile.md').write_text(str(state(root)['target_journal'])+'\n')
  (stage/'publication_notes.md').write_text('Stage 3 reviewed Markdown and current assets. Preserve claims/data/captions in Stage 4. No LaTeX or manuscript PDF has been generated here.\n'+('MOCK / FIXTURE only, not for publication.\n' if r['test_only'] else '')+'Read readiness.json and unresolved_minor_items.json before production.\n')
  marker='MOCK_HANDOFF_ONLY.md' if r['test_only'] else 'REVIEWED_MANUSCRIPT_READY.md' if r['status']=='REVIEWED_MANUSCRIPT_READY' else 'REVIEWED_WITH_MINOR_ISSUES.md';(stage/marker).write_text(r['status']+'\n')
  write(stage/'checksums.json',{str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()});stage.rename(dest)
 except Exception:shutil.rmtree(stage);raise
 return r

def transition(root,phase):
 s=state(root)
 if phase!=s['current_phase']+1 or phase==9:raise ValueError('Sequential transition required; use finalize for phase 9')
 if phase==2 and (baseline(root)['issues'] or not filled(Path(root)/'00_baseline_audit.md')):raise ValueError('Complete baseline first')
 if phase==3 and not s['rounds'].get('1',{}).get('frozen'):raise ValueError('Freeze Round1 first')
 if phase==4 and not approved(root,'A'):raise ValueError('Gate A required')
 if phase==5 and any(r['severity'] in {'BLOCKER','MAJOR'} and r['status']!='RESOLVED' for r in all_triage(root)):raise ValueError('Science before polish')
 if phase==6 and (not language_ok(root) or not valid_audit(root,'fact_lock')):raise ValueError('Fact-safe polish required')
 if phase==7 and (not approved(root,'C',True) or (not mini(root) or needs_fresh(root)) and not s['rounds'].get('2',{}).get('frozen')):raise ValueError('Required review and Gate C missing')
 if phase==7 and mini(root) and (not valid_risk(root) or not valid_audit(root,'issue_closure')):raise ValueError('Risk assessment and issue closure required')
 s['current_phase']=phase;save(root,s);return s

def reopen(root,round_number,record):
 root=Path(root);s=state(root);p=local(root,record)
 if round_number not in [1,2] or not filled(p):raise ValueError('Document reason for reopening round')
 if round_number==1 and s['rounds'].get('2',{}).get('frozen'):
  reopen(root,2,record);s=state(root)
 folder=root/f'round_{round_number}'
 if not s['rounds'].get(str(round_number),{}).get('frozen'):raise ValueError('Only frozen rounds can be reopened')
 carry=None if mini(root) else (folder/'triage.csv').read_text()
 history=s['rounds'].pop(str(round_number));history['reopen_record']=record;s.setdefault('round_history',[]).append(history)
 folder.rename(root/'versions'/('round_'+str(round_number)+'_'+datetime.now().strftime('%Y%m%d%H%M%S%f')));folder.mkdir()
 for name,template in [('triage.csv','triage.csv'),('consensus.md','reviewer_consensus.md')]:shutil.copy2(S/'templates'/template,folder/name)
 if mini(root):(folder/'triage.csv').unlink()
 else:(folder/'triage.csv').write_text(carry)
 s['current_phase']=2 if round_number==1 else 6;s['review_readiness']='REVIEW_IN_PROGRESS';save(root,s)
 return {'status':'REVIEW_IN_PROGRESS','reopened_round':round_number}

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['init','state','baseline','packet','register-report','freeze-round','approve','audit','milestone','fact-lock','polish-diff','check','finalize','package','fingerprint','transition','reopen','assess-risk','audit-all','language-check']);p.add_argument('review');p.add_argument('--source');p.add_argument('--mock',action='store_true');p.add_argument('--round',type=int);p.add_argument('--phase',type=int);p.add_argument('--reviewer');p.add_argument('--context-id');p.add_argument('--gate');p.add_argument('--record');p.add_argument('--name');p.add_argument('--output');p.add_argument('--accept-minor',action='store_true');a=p.parse_args();cmd=a.command
 try:
  if cmd!='init':_coord.enter(a.review,'manuscript_review',cmd in ['finalize','package'])
  if cmd=='init':r=init(a.review,a.source,a.mock)
  elif cmd=='assess-risk':r=assess_risk(a.review,a.record)
  elif cmd=='audit-all':r=audit_all(a.review,a.record)
  elif cmd=='language-check':r=language_check(a.review,a.record)
  elif cmd=='transition':r=transition(a.review,a.phase)
  elif cmd=='reopen':r=reopen(a.review,a.round,a.record)
  elif cmd=='packet':r=packet(a.review,a.round)
  elif cmd=='register-report':r=register_report(a.review,a.round,a.reviewer,a.context_id)
  elif cmd=='freeze-round':r=freeze_round(a.review,a.round)
  elif cmd=='approve':r=approve(a.review,a.gate,a.record,a.accept_minor)
  elif cmd=='audit':r=audit(a.review,a.name,a.record)
  elif cmd=='milestone':r=milestone(a.review,a.name)
  elif cmd=='fact-lock':r=fact_lock(a.review,a.record)
  elif cmd=='package':r=package(a.review,a.output)
  elif cmd=='fingerprint':r={'fingerprint':fingerprint(a.review)}
  else:r=globals()[cmd.replace('-','_')](a.review)
  if cmd=='init':_coord.enter(a.review,'manuscript_review')
  if cmd=='finalize' and r.get('status')=='REVIEWED_MANUSCRIPT_READY':_coord.completed(a.review,'manuscript_review',Path(a.review)/'qa/readiness.json',{'reviewed_manuscript':Path(a.review)/'reviewed_manuscript.md'})
  if cmd=='approve':_coord.record_decision(a.review,'manuscript_review',r)
  print(json.dumps(r,ensure_ascii=False,indent=2));return 2 if r.get('status') in {'BLOCKED','REQUIRES_NEW_EVIDENCE','REQUIRES_STAGE2_REVISION'} else 0
 except (ValueError,TypeError,KeyError,OSError) as e:print(json.dumps({'status':'ERROR','error':str(e)}));return 1
if __name__=='__main__':sys.exit(main())
