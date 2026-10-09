"""Freeze independent evidence locations and input hashes BEFORE any After retrieval."""
import argparse,re
from token128_common import *
def compact_map(s):
    chars=[];positions=[]
    for i,c in enumerate(s):
        if not c.isspace():chars.append(c);positions.append(i)
    return "".join(chars),positions
def locate(text,needle):
    compact,pos=compact_map(text)
    if isinstance(needle,str):
        n,_=compact_map(needle);a=compact.find(n)
        if a<0:raise ValueError("Unmatched evidence: "+needle)
        return pos[a],pos[a+len(n)-1]+1
    start,_=compact_map(needle["from"]);end,_=compact_map(needle["to"])
    a=compact.find(start);b=compact.find(end,a+len(start))
    if a<0 or b<0:raise ValueError("Unmatched evidence range: "+str(needle))
    return pos[a],pos[b+len(end)-1]+1
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);args=ap.parse_args()
    cfg=readj(path(args.config));version=path(cfg["output_dir"])
    if version.exists():raise FileExistsError("Version directory already exists; do not overwrite.")
    pages=jl(path(cfg["pages"]));qa=jl(ROOT/"data/evaluation/qa_eval_set.jsonl")
    spec=readj(ROOT/"configs/chunking/token128_evidence_targets_v1.json")
    resolved=[]
    for group in spec["groups"]:
        facts=[]
        for fact in group["facts"]:
            alts=[]
            for alt in fact["alternatives"]:
                candidates=[p for p in pages if p["doc_id"]==alt["doc_id"] and (alt["page_number"] is None or p["page_number"]==alt["page_number"])]
                matches=[]
                for p in candidates:
                    try:
                        spans=[]
                        for n in alt["required"]:
                            a,b=locate(p["text"],n)
                            spans.append({"doc_id":p["doc_id"],"page_number":p["page_number"],"start":a,"end":b,
                              "text":p["text"][a:b],"sha256":digest(p["text"][a:b])})
                        matches.append({"source_spans":spans})
                    except ValueError:continue
                if not matches:raise ValueError(f"Unresolved {group['pair_id']}/{fact['fact_id']}: {alt}")
                alts+=matches
            facts.append({**fact,"alternatives":alts})
        for q in qa:
            if q["pair_id"]==group["pair_id"]:
                resolved.append({**group,"question_id":q["question_id"],"question":q["question"],"facts":facts,
                  "created_at":now(),"role":"diagnostic_targets_not_gold_edits"})
    assert len(resolved)==30
    protected=[]
    for sub,pattern in [("scripts","*.py"),("data/raw_docs","*.pdf"),("data/processed","*"),("outputs/embeddings","*"),("data/evaluation","*.*")]:
        protected+=list((ROOT/sub).glob(pattern))
    added={"token128_common.py","chunk_documents_token128.py","build_embeddings_versioned.py","evaluate_retrieval_versions.py","prepare_token128_experiment.py"}
    protected=[p for p in protected if p.is_file() and not (p.parent==ROOT/"scripts" and p.name in added)]
    protected += [ROOT/"README.md",ROOT/"requirements.txt",path(cfg["source_catalog"]),
      ROOT/"data/evaluation/error_analysis/error_analysis_report.md",ROOT/"data/evaluation/error_analysis/error_analysis_30.csv"]
    version.mkdir(parents=True);log=Log(version,"prepare")
    writej(version/"manifest.json",{"created_at":now(),"version":cfg["version"],"model":MODEL,"snapshot":SNAPSHOT,
       "protected_files":{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(protected))},
       "limits":"No production changes, no paid LLM, no Gold or label edits, no overwrite."})
    writej(version/"config_snapshot.json",cfg)
    writejl(version/"evaluation/evidence_targets.jsonl",resolved)
    code=[ROOT/"scripts"/x for x in added]+[path(args.config),ROOT/"configs/chunking/token128_evidence_targets_v1.json",
        version/"config_snapshot.json",version/"evaluation/evidence_targets.jsonl",ROOT/"tests/test_token128_chunking.py"]
    writej(version/"preregistration.json",{"frozen_at":now(),"after_results_seen":False,
       "files":{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(code)},
       "facts":sum(len(g["facts"]) for g in resolved),"mapping":"Explicit original-page spans; no question-driven splitting."})
    log.event("preregistered",questions=30,facts=sum(len(g["facts"]) for g in resolved),protected=verify_protected(version))
if __name__=="__main__":main()
