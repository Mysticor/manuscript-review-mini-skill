from pathlib import Path
import argparse,json,yaml,os
S=Path(__file__).resolve().parents[1];M=yaml.safe_load((S/'manifest.yaml').read_text())
def route(name,paper_type='research',section='results',language='en',journal='generic'):
 if name not in M['allowed_specialists']:raise ValueError('OUTSIDE_STAGE_3: '+name)
 local=Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'skills'/name
 root=local.resolve() if (local/'SKILL.md').exists() else S.parents[1]/'vendor/nature-skills/skills'/name
 if not (root/'SKILL.md').is_file():raise FileNotFoundError(name)
 paths=[root/'SKILL.md']
 if name in {'nature-polishing','nature-writing'}:
  m=yaml.safe_load((root/'manifest.yaml').read_text());paths += [root/'manifest.yaml']+[root/p for p in m['always_load']]
  axes={'paper_type':paper_type,'section':section,'language':language,'journal':journal}
  if name=='nature-writing':
   axes['task']='manuscript';axes['section']={'results':'experiments','methods':'method'}.get(section,section)
  paths += [root/m['axes'][k]['values'][v] for k,v in axes.items()]
 for p in paths:
  if not p.is_file():raise FileNotFoundError(p)
 return {'specialist':name,'paths':[str(p.resolve()) for p in paths],'executed':False,'scope':'Stage 3 only; no polishing LaTeX-layout route or submission task'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('specialist');p.add_argument('--paper-type',default='research');p.add_argument('--section',default='results');a=p.parse_args();print(json.dumps(route(a.specialist,a.paper_type,a.section),ensure_ascii=False,indent=2))


def optional_humanizer(explicit=False,residual_ai_prose=False,author_voice=False):
    """Optional prose cleanup after fact lock; default remains nature-polishing."""
    root=Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'skills/humanizer'
    requested=explicit or residual_ai_prose or author_voice
    return {'route':'humanizer','skill':str(root/'SKILL.md'),'safety_wrapper':'project-coordination.md; immutable prose fact lock + semantic comparison'} if requested and (root/'SKILL.md').is_file() else {'route':'nature-polishing','humanizer_required':False}
