# SPDX-License-Identifier: AGPL-3.0-or-later
"""Experimental Heretic plugin: target first-token KL on frozen raw prefixes.

Not an acceptance-rate, performance or output-correctness metric.
"""
from pathlib import Path
import json,hashlib
import torch
import torch.nn.functional as F
from pydantic import BaseModel
from heretic.scorer import Scorer,Score

class Settings(BaseModel):
 teacher_directory:str

class TeacherKL(Scorer):
 settings:Settings
 @property
 def reproducible(self):return False
 @property
 def score_name(self):return 'Teacher first-token KL (calibration only)'
 def init(self,ctx):
  p=Path(self.settings.teacher_directory)
  self.rows=[r for r in json.loads((p/'teacher-sequences.json').read_text()) if r['split']=='calibration']
  self.teacher=torch.load(p/'teacher-calibration-logits.pt',map_location='cpu',weights_only=True).float().log_softmax(-1)
  actual=hashlib.sha256(json.dumps(ctx.get_model().tokenizer.get_vocab(),sort_keys=True).encode()).hexdigest()
  if actual!=json.loads((p/'manifest.json').read_text())['vocab_hash']:raise ValueError('Vocabulary mapping mismatch')
  if len(self.rows)!=self.teacher.shape[0]:raise ValueError('Teacher calibration length mismatch')
 def get_score(self,ctx):
  model=ctx.get_model().model;values=[]
  with torch.no_grad():
   for row,teacher in zip(self.rows,self.teacher):
    ids=torch.tensor([row['input_ids']],dtype=torch.long,device=model.device)
    z=model(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False).logits[0,-1].float().cpu()
    if z.shape!=teacher.shape or not torch.isfinite(z).all():raise ValueError('Invalid candidate logits')
    values.append(F.kl_div(z.log_softmax(-1),teacher,reduction='sum',log_target=True).item())
  value=sum(values)/len(values)
  return Score(value=value,rich_display=f'{value:.6f}',md_display=f'{value:.6f}')
