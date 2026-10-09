"""Utilities for the isolated token128 experiment; no production imports or API calls."""
from __future__ import annotations
import os,sys,json,hashlib,csv
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SNAPSHOT="e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
CACHE=ROOT/".cache/sentence_transformers"
MODEL_PATH=CACHE/"models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots"/SNAPSHOT
os.environ["HF_HUB_OFFLINE"]="1"
os.environ["TRANSFORMERS_OFFLINE"]="1"
os.environ["TOKENIZERS_PARALLELISM"]="false"
sys.dont_write_bytecode=True
def now():return datetime.now(timezone(timedelta(hours=9))).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def readj(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def jl(p):return [json.loads(l) for l in Path(p).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
def write_text(p,s):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8",newline="\n") as out:out.write(s)
def writej(p,o):write_text(p,json.dumps(o,ensure_ascii=False,indent=2)+"\n")
def writejl(p,rows):write_text(p,"".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows))
def writecsv(p,rows):
    with Path(p).open("x",encoding="utf-8-sig",newline="") as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def path(s):return (ROOT/s).resolve()
def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(MODEL_PATH),local_files_only=True)
def count(tok,text):return len(tok(text,add_special_tokens=True,truncation=False)["input_ids"])
def load_model():
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer(str(MODEL_PATH),local_files_only=True,device="cpu")
    assert model.max_seq_length==128
    return model
def verify_protected(version):
    m=readj(version/"manifest.json")
    changes=[p for p,h in m["protected_files"].items() if sha(path(p))!=h]
    if changes:raise RuntimeError("Protected inputs changed: "+str(changes))
    return {"count":len(m["protected_files"]),"unchanged":True}
def verify_seal(version):
    seal=readj(version/"preregistration.json")
    for p,h in seal["files"].items():
        if sha(path(p))!=h:raise RuntimeError("Pre-registered file changed: "+p)
    return seal
class Log:
    def __init__(self,version,stage):
        p=version/"logs"/(stage+"_"+datetime.now().strftime("%Y%m%d_%H%M%S_%f")+".jsonl")
        p.parent.mkdir(parents=True,exist_ok=True);self.file=p.open("x",encoding="utf-8");self.path=p
    def event(self,event,**kw):
        row={"time":now(),"event":event,**kw};self.file.write(json.dumps(row,ensure_ascii=False)+"\n");self.file.flush()
        print(json.dumps(row,ensure_ascii=False),flush=True)
