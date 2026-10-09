"""Read-only retrieval comparison. No generation, reranking, or production writes."""
import argparse, csv, re
from collections import defaultdict
import numpy as np
from token128_common import *
from chunk_documents_token128 import archive_end, norm

def covered(span, selected, pages):
    text=pages[(span["doc_id"],span["page_number"])]
    intervals=[]
    for row in selected:
        for s in row["source_spans"]:
            if (s["doc_id"],s["page_number"])==(span["doc_id"],span["page_number"]):
                intervals.append((s["start"],s["end"]))
    return all(text[i].isspace() or any(a<=i<b for a,b in intervals)
               for i in range(span["start"],span["end"]))
def supported(fact,selected,pages):
    return any(all(covered(s,selected,pages) for s in alt["source_spans"])
               for alt in fact["alternatives"])
def assess(target,ranked,pages):
    top=ranked[:5];facts=[]
    for fact in target["facts"]:
        singles=[r for r in ranked if supported(fact,[r],pages)]
        single=singles[0] if singles else None
        accumulated=[];completion=None
        for r in ranked:
            accumulated.append(r)
            if supported(fact,accumulated,pages):completion=r["rank"];break
        facts.append({"fact_id":fact["fact_id"],"label":fact["label"],
          "hit_at5":supported(fact,top,pages),
          "single_chunk_rank":single["rank"] if single else None,
          "single_chunk_similarity":single["score"] if single else None,
          "single_chunk_id":single["chunk_id"] if single else None,
          "union_completion_rank":completion})
    n=sum(x["hit_at5"] for x in facts);total=len(facts)
    eligible=target["scope_status"]=="eligible"
    return {"facts":facts,"fact_hits":n,"fact_total":total,"fact_coverage":n/total,
       "any_fact_hit_at5":n>0,"complete_at5":n==total,
       "scope_eligible":eligible,"scope_valid_complete_at5":n==total if eligible else None,
       "school_match_at5":all(r["source_file"].startswith(target["school"]+"_") for r in top),
       "document_scope_match_count_at5":sum(r["document_metadata"]["scope_class"]==target["query_scope"] for r in top),
       "top5_count":len(top)}
def old_spans(rows,pages,metadata):
    cache={}
    for key,text in pages.items():
        slices=[]
        for start in range(0,len(text),400):
            raw=text[start:start+500]
            if raw.strip():
                a=start+len(raw)-len(raw.lstrip());b=start+len(raw.rstrip())
                slices.append((a,b))
            if start+500>=len(text):break
        cache[key]=slices
    for r in rows:
        a,b=cache[(r["doc_id"],r["page_number"])][r["chunk_index"]-1]
        assert pages[(r["doc_id"],r["page_number"])][a:b]==r["text"]
        r["source_spans"]=[{"doc_id":r["doc_id"],"page_number":r["page_number"],"start":a,"end":b}]
        r["document_metadata"]=metadata[r["doc_id"]]
def token_stats(rows,tok,key):
    lengths=[count(tok,r[key]) for r in rows]
    return {"chunks":len(rows),"over128":sum(n>128 for n in lengths),
      "truncation_ratio":sum(n>128 for n in lengths)/len(rows),
      "max":max(lengths),"median":float(np.median(lengths)),"p95":float(np.percentile(lengths,95)),
      "token_counts":lengths}
def aggregate(rows,side):
    all_a=[r[side] for r in rows];valid=[a for a in all_a if a["scope_eligible"]]
    return {"questions":len(rows),"scope_eligible_questions":len(valid),
      "scope_unverified_questions":len(all_a)-len(valid),
      "valid_fact_hits":sum(a["fact_hits"] for a in valid),"valid_fact_total":sum(a["fact_total"] for a in valid),
      "valid_complete_questions":sum(a["complete_at5"] for a in valid),
      "raw_fact_hits":sum(a["fact_hits"] for a in all_a),"raw_fact_total":sum(a["fact_total"] for a in all_a),
      "raw_complete_questions":sum(a["complete_at5"] for a in all_a),
      "all_school_match":all(a["school_match_at5"] for a in all_a),
      "document_scope_matches":sum(a["document_scope_match_count_at5"] for a in all_a),
      "retrieved_chunks":sum(a["top5_count"] for a in all_a)}
def frac(a):return f"{a['fact_hits']}/{a['fact_total']}"
def yn(x):return "是" if x else "否"
def ranktext(f):return str(f["single_chunk_rank"]) if f["single_chunk_rank"] is not None else "无单块；联合"+str(f["union_completion_rank"])
def report(v,rows,stats,summary,audit):
    lines=["# token128_clause_v1 本地检索实验记录","",
      "本轮仅运行离线 Embedding 与 Retrieval，没有调用 LLM；以下不是回答正确率。旧生产代码、索引、Baseline、Gold、人工标签均保留。",
      "",
      "## 实验口径","",
      "- 同一模型缓存快照、CPU、归一化向量、学校过滤、点积排序、Top-K=5。Before 须复现冻结 Top5，并逐题对照实际 retrieve.py。",
      "- 切块目标112 tokens，硬上限128（含特殊符号和元数据）；元数据最多40 tokens。按条款边界，过长条款按句/行/分句拆分，再以token边界兜底；所有正文字符保留。",
      "- 证据映射与程序/配置 SHA-256 在 After 前冻结，切块器不读QA。命中必须覆盖预登记原文区间的全部非空白字符；允许Top5多块联合覆盖，不用关键词或相似度代替事实支持。",
      "- 目标事实 Hit@5以事实为分母；完整覆盖以全部目标事实为条件。排名为首个完整单块排名，同时保存最小联合覆盖前缀排名；两者不可混为一谈。",
      "- Q03、Q04、Q10、Q15的中韩共8题缺乏已确认的研究生适用证据：保留原题并单列定位结果，有效命中为NA，不计入22题有效分母。Q14采用已审核的硕士24学分事实作诊断目标，原Gold不变。",
      "- 适用范围匹配仅衡量文档层面的本科/研究生类别；不自动证明院系、入学年份、身份条件适用。证据中相应限制必须保留。",
      "",
      "## Token与原文覆盖","",
      "|指标|Before|After|","|---|---:|---:|",
      f"|Chunk数|{stats['before']['chunks']}|{stats['after']['chunks']}|",
      f"|超128输入|{stats['before']['over128']} ({stats['before']['truncation_ratio']:.2%})|{stats['after']['over128']} ({stats['after']['truncation_ratio']:.2%})|",
      f"|最大输入tokens|{stats['before']['max']}|{stats['after']['max']}|",
      f"|中位数|{stats['before']['median']}|{stats['after']['median']}|","",
      f"新Chunks对pages.jsonl的官方或不确定正文覆盖率为100%：{audit['official_or_uncertain_characters']}字符；{audit['archive_characters']}字符的明确归档说明另存archive_notes.jsonl。逐页区间、哈希和覆盖审计见chunking_audit.json及coverage_verification.json。该指标不证明原PDF提取完整，也不修复丢失的表格合并单元格结构。",
      f"共有{len(audit['warnings'])}个原始文本单元因超过128上限被拆分，原文保留，跨页不猜测合并。特殊长条款可能需要多个检索位才能覆盖。",
      "",
      "## 汇总","",
      "|范围|有效目标事实 Before→After|完整证据 Before→After|适用范围匹配Chunk Before→After|",
      "|---|---|---|---|"]
    for lang in ("all","zh","ko"):
        b=summary[lang]["before"];a=summary[lang]["after"]
        lines.append(f"|{lang}|{b['valid_fact_hits']}/{b['valid_fact_total']} → {a['valid_fact_hits']}/{a['valid_fact_total']}|{b['valid_complete_questions']}/{b['scope_eligible_questions']} → {a['valid_complete_questions']}/{a['scope_eligible_questions']}|{b['document_scope_matches']}/{b['retrieved_chunks']} → {a['document_scope_matches']}/{a['retrieved_chunks']}|")
    lines+=["","学校匹配须全部通过。相似度仅写入逐事实明细作为辅助，不用于判断改善。","",
      "## 全30题 Before / After","",
      "事实列也显示范围待确认题的原文定位覆盖；这些题不算有效答案证据。",
      "",
      "|题号|原评分|目标事实 Before→After|完整覆盖 Before→After|适用性|丢失事实|",
      "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"|{r['question_id']}|{r['manual_label']}|{frac(r['before'])} → {frac(r['after'])}|{yn(r['before']['complete_at5'])} → {yn(r['after']['complete_at5'])}|{'已映射范围' if r['before']['scope_eligible'] else '待确认，NA'}|{','.join(r['lost_fact_ids']) or '无'}|")
    lines+=["","## Q03、Q05、Q08专项","",
      "Q03即使命中本科1门/1学分条款，也不能视为研究生问题修复。Q05按8项材料及预登记条件检查，避免只命中部分清单便判正确。Q08仅使用本科文件月份，不借研究生文件充当替代；2월 중/8월 중意为该月期间，不能自动解释为中旬。",""]
    for r in rows:
        if r["pair_id"] not in ("Q03","Q05","Q08"):continue
        lines += [f"### {r['question_id']}","",f"Top5事实覆盖 {frac(r['before'])} → {frac(r['after'])}；完整证据 {yn(r['before']['complete_at5'])} → {yn(r['after']['complete_at5'])}。","",
          "|事实|Before排名|After排名|Hit@5 Before→After|","|---|---|---|---|"]
        for b,a in zip(r["before"]["facts"],r["after"]["facts"]):
            lines.append(f"|{b['label']}|{ranktext(b)}|{ranktext(a)}|{yn(b['hit_at5'])} → {yn(a['hit_at5'])}|")
        lines.append("")
    lines+=["## 原13条Correct回归检查","",
      "任何原已覆盖事实丢失即标记回归；即使同时增加其他事实，也不抵消。原Correct是历史人工回答评分，不保证其Gold或适用范围正确。",
      "",
      "|题号|事实 Before→After|丢失事实|判定|","|---|---|---|---|"]
    for r in rows:
        if r["manual_label"]=="Correct":
            lines.append(f"|{r['question_id']}|{frac(r['before'])} → {frac(r['after'])}|{','.join(r['lost_fact_ids']) or '无'}|{'证据回归' if r['lost_fact_ids'] else '未发现已映射事实丢失'}|")
    regress=summary["correct_regressions"]
    lines+=["","## 结论与限制","",
      f"128-token静默截断已在新索引消除，正文覆盖审计通过。原Correct证据回归{len(regress)}题："+("、".join(regress) if regress else "无")+"。",
      "本轮可证明工程上的长度约束是否满足；检索结论以以上事实覆盖和范围指标为准。缩短Chunk使长清单/跨段条件分散，元数据重复也可能影响排序；这些是本方案的取舍。仅有一组对照实验，不能把所有排序变化分别归因于某一项规则。",
      "有回归或完整证据未改善时，不建议替换生产索引。即使指标改善，也需要后续人工证据复核，不能推断LLM回答和引用已经修复。",
      "证据映射采用已冻结的明确原文位置，尚未登记的等价证据可能造成保守低估；After后不据此调整映射或规则。表格语义、Gold修订、研究生适用性和生成问题均不在本轮修复范围。",
      "实验完成即停止，保留全部产物，等待审核；不切换生产代码/索引，不开展第二轮修复。",
      "",
      "## 产物与运行命令","",
      "目录："+str(v),"",
      "evaluation/retrieval_comparison_30.csv：全30题；fact_comparison.csv：逐事实排名/相似度/命中；correct_regression_13.csv：13条回归；pair_comparison_15.csv：中韩差异；before_retrieval_30.jsonl与after_retrieval_30.jsonl：完整排序和原文；token_statistics.json：逐块长度；retrieval_summary.json：汇总。logs保存各阶段时间、参数与校验。",
      "",
      "~~~powershell",
      ".\\.venv\\Scripts\\python.exe -B -X utf8 -m unittest discover -s tests -p test_token128_chunking.py -v",
      ".\\.venv\\Scripts\\python.exe -B -X utf8 scripts/prepare_token128_experiment.py --config configs/chunking/token128_clause_v1.json",
      ".\\.venv\\Scripts\\python.exe -B -X utf8 scripts/chunk_documents_token128.py --config configs/chunking/token128_clause_v1.json",
      ".\\.venv\\Scripts\\python.exe -B -X utf8 scripts/build_embeddings_versioned.py --version-dir data/experiments/token128_clause_v1",
      ".\\.venv\\Scripts\\python.exe -B -X utf8 scripts/evaluate_retrieval_versions.py --version-dir data/experiments/token128_clause_v1",
      "~~~","",
      "上述命令记录本次流程。输出采用独占创建，已完成目录不可覆盖重跑；复现实验应另设版本目录并重新冻结配置。",""]
    return "\n".join(lines)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--version-dir",required=True);args=ap.parse_args()
    v=path(args.version_dir);seal=verify_seal(v);verify_protected(v);out=v/"evaluation"
    if (out/"after_retrieval_30.jsonl").exists():raise FileExistsError("Refusing to overwrite results")
    log=Log(v,"retrieval");log.event("start",preregistered_at=seal["frozen_at"],paid_llm=False,top_k=5)
    qa=jl(ROOT/"data/evaluation/qa_eval_set.jsonl")
    baseline={r["question_id"]:r for r in jl(ROOT/"data/evaluation/baseline_evaluation_results_frozen.jsonl")}
    targets={r["question_id"]:r for r in jl(out/"evidence_targets.jsonl")}
    with (ROOT/"data/evaluation/manual_review_30.csv").open(encoding="utf-8-sig",newline="") as fp:
        labels={r["question_id"]:r["manual_label"] for r in csv.DictReader(fp)}
    pages={(r["doc_id"],r["page_number"]):r["text"] for r in jl(ROOT/"data/processed/pages.jsonl")}
    old=jl(ROOT/"data/processed/chunks.jsonl");new=jl(v/"chunks.jsonl")
    metadata={r["doc_id"]:r for r in jl(v/"document_metadata.jsonl")}
    old_spans(old,pages,metadata)
    cov={key:bytearray(len(text)) for key,text in pages.items()}
    for r in new:
        text="".join(pages[(s["doc_id"],s["page_number"])][s["start"]:s["end"]] for s in r["source_spans"])
        assert text==r["text"] and digest(text)==r["body_sha256"]
        assert r["embedding_text"]==r["metadata_prefix"]+norm(text)
        for s in r["source_spans"]:
            assert digest(pages[(s["doc_id"],s["page_number"])][s["start"]:s["end"]])==s["sha256"]
            cov[(s["doc_id"],s["page_number"])][s["start"]:s["end"]]=b"\1"*(s["end"]-s["start"])
    for key,text in pages.items():assert all(cov[key][archive_end(text,key[1]):]),key
    coverage={"verified_at":now(),"pages":len(pages),"coverage":1.0,"exact_text_and_hash_verified":True}
    em=readj(v/"embeddings/embedding_metadata.json");mapping=jl(v/"embeddings/embedding_rows.jsonl")
    assert em["chunks_sha256"]==sha(v/"chunks.jsonl")
    assert em["matrix_sha256"]==sha(v/"embeddings/chunk_embeddings.npy")
    assert em["row_mapping_sha256"]==sha(v/"embeddings/embedding_rows.jsonl")
    assert len(mapping)==len(new)
    for i,(r,m) in enumerate(zip(new,mapping)):
        assert i==m["row"] and r["chunk_id"]==m["chunk_id"] and digest(r["embedding_text"])==m["embedding_text_sha256"]
    matrices={"before":np.load(ROOT/"outputs/embeddings/chunk_embeddings.npy"),
              "after":np.load(v/"embeddings/chunk_embeddings.npy")}
    chunks={"before":old,"after":new}
    for side in chunks:assert matrices[side].shape==(len(chunks[side]),384)
    model=load_model();stats={"before":token_stats(old,model.tokenizer,"text"),
      "after":token_stats(new,model.tokenizer,"embedding_text")}
    assert stats["after"]["over128"]==0
    import retrieve as prod
    assert prod.MODEL_NAME==MODEL and prod.TOP_K==5
    prod.SentenceTransformer=lambda *a,**kw:model
    rr=[];raw={"before":[],"after":[]};factrows=[];comparison=[]
    maxdelta=0.0
    for q in qa:
        qid=q["question_id"];target=targets[qid]
        assert q["question"]==baseline[qid]["question"]==target["question"]
        assert "\ufffd" not in q["question"] and any(ord(c)>127 for c in q["question"])
        prefix=next((p for school,p in prod.SCHOOL_ALIASES.items() if school in q["question"]),None)
        assert prefix==target["school"]+"_"
        vector=model.encode([q["question"]],convert_to_numpy=True,normalize_embeddings=True)[0]
        result={"question_id":qid,"pair_id":q["pair_id"],"language":q["question_language"],"manual_label":labels[qid]}
        for side in ("before","after"):
            rows=chunks[side];indices=[i for i,r in enumerate(rows) if r["source_file"].startswith(prefix)]
            scores=matrices[side][indices]@vector;order=np.argsort(scores)[::-1]
            ranked=[{**rows[indices[int(j)]],"rank":rank,"score":float(scores[j])} for rank,j in enumerate(order,1)]
            prod.CHUNKS_PATH=ROOT/"data/processed/chunks.jsonl" if side=="before" else v/"chunks.jsonl"
            prod.EMBEDDINGS_PATH=ROOT/"outputs/embeddings/chunk_embeddings.npy" if side=="before" else v/"embeddings/chunk_embeddings.npy"
            actual=prod.retrieve(q["question"],top_k=5)
            assert [r["chunk_id"] for r in actual]==[r["chunk_id"] for r in ranked[:5]],(qid,side)
            assert max(abs(x["score"]-y["score"]) for x,y in zip(actual,ranked))<1e-6
            if side=="before":
                frozen=baseline[qid]["retrieval_results"]
                assert [r["chunk_id"] for r in frozen]==[r["chunk_id"] for r in actual],qid
                delta=max(abs(x["score"]-y["score"]) for x,y in zip(frozen,actual));maxdelta=max(maxdelta,delta)
                assert delta<1e-6
                assert all(x["text"]==y["text"] for x,y in zip(frozen,actual))
            result[side]=assess(target,ranked,pages)
            raw[side].append({"question_id":qid,"question":q["question"],"query_sha256":digest(q["question"]),
              "school_filter":prefix,"candidate_count":len(indices),"assessment":result[side],
              "top5":ranked[:5],"full_ranking":ranked})
        b=result["before"];a=result["after"]
        result["lost_fact_ids"]=[x["fact_id"] for x,y in zip(b["facts"],a["facts"]) if x["hit_at5"] and not y["hit_at5"]]
        result["gained_fact_ids"]=[x["fact_id"] for x,y in zip(b["facts"],a["facts"]) if not x["hit_at5"] and y["hit_at5"]]
        result["complete_regression"]=b["complete_at5"] and not a["complete_at5"]
        rr.append(result)
        for x,y in zip(b["facts"],a["facts"]):
            factrows.append({"question_id":qid,"manual_label":labels[qid],"scope_eligible":b["scope_eligible"],
              "fact_id":x["fact_id"],"fact_label":x["label"],
              **{"before_"+k:val for k,val in x.items() if k not in ("fact_id","label")},
              **{"after_"+k:val for k,val in y.items() if k not in ("fact_id","label")}})
        comparison.append({"question_id":qid,"manual_label":labels[qid],"language":q["question_language"],
          "scope_status":target["scope_status"],"before_fact_hits":b["fact_hits"],"after_fact_hits":a["fact_hits"],
          "fact_total":b["fact_total"],"before_complete":b["complete_at5"],"after_complete":a["complete_at5"],
          "before_valid_complete":b["scope_valid_complete_at5"],"after_valid_complete":a["scope_valid_complete_at5"],
          "before_school_match":b["school_match_at5"],"after_school_match":a["school_match_at5"],
          "before_scope_matches":b["document_scope_match_count_at5"],"after_scope_matches":a["document_scope_match_count_at5"],
          "lost_fact_ids":";".join(result["lost_fact_ids"]),"gained_fact_ids":";".join(result["gained_fact_ids"]),
          "original_correct_regression":labels[qid]=="Correct" and bool(result["lost_fact_ids"]),
          "before_rank_details":json.dumps(b["facts"],ensure_ascii=False),"after_rank_details":json.dumps(a["facts"],ensure_ascii=False)})
        log.event("question_complete",question_id=qid,before_facts=frac(b),after_facts=frac(a),
           scope_eligible=b["scope_eligible"],lost_fact_ids=result["lost_fact_ids"])
    assert len(rr)==30 and sum(r["manual_label"]=="Correct" for r in rr)==13
    summary={lang:{side:aggregate([r for r in rr if lang=="all" or r["language"]==lang],side)
                      for side in ("before","after")} for lang in ("all","zh","ko")}
    summary.update({"created_at":now(),"correct_regressions":[r["question_id"] for r in rr if r["manual_label"]=="Correct" and r["lost_fact_ids"]],
      "complete_regressions":[r["question_id"] for r in rr if r["complete_regression"]],
      "frozen_top5_reproduced":30,"frozen_max_score_delta":maxdelta,"retrieve_py_consistency_checks":60,
      "protected_inputs":verify_protected(v),"preregistration_verified":bool(verify_seal(v)),
      "query_max_tokens":max(count(model.tokenizer,q["question"]) for q in qa)})
    pairrows=[]
    for pair in sorted({r["pair_id"] for r in rr}):
        langs={r["language"]:r for r in rr if r["pair_id"]==pair}
        pairrows.append({"pair_id":pair,**{lang+"_"+side+"_coverage":frac(langs[lang][side]) for lang in ("zh","ko") for side in ("before","after")}})
    writejl(out/"before_retrieval_30.jsonl",raw["before"]);writejl(out/"after_retrieval_30.jsonl",raw["after"])
    writecsv(out/"retrieval_comparison_30.csv",comparison);writecsv(out/"fact_comparison.csv",factrows)
    writecsv(out/"correct_regression_13.csv",[r for r in comparison if r["manual_label"]=="Correct"])
    writecsv(out/"pair_comparison_15.csv",pairrows);writej(out/"retrieval_summary.json",summary)
    writej(out/"token_statistics.json",stats);writej(out/"coverage_verification.json",coverage)
    write_text(out/"retrieval_report.md",report(v,rr,stats,summary,readj(v/"chunking_audit.json")))
    log.event("complete",summary=summary,report=str(out/"retrieval_report.md"))
if __name__=="__main__":main()
