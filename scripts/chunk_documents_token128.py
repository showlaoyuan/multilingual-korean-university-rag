"""Lossless body-span partitioning under a model-token budget; never reads QA."""
from __future__ import annotations
import argparse,re
from collections import defaultdict
from token128_common import *
START=re.compile(r"^\s*(?:제\s*\d+\s*[장조]|[①②③④⑤⑥⑦⑧⑨⑩]|[0-9]+[.)](?![0-9])|[가-하A-Z][.)]|[-∙•※▣])")
def norm(s):return re.sub(r"\s+"," ",s).strip()
def archive_end(text,page_number):
    if page_number!=1:return 0
    # Only positively identified archival templates. Unknown material is kept.
    if text.startswith(("本科","研究生","首尔","外国","学位","论文")) and "大学官方来源" in text:
        m=re.search(r"以下为原文正文离线排版，未翻译或更改制度；表格保留原有合并单元格，图片链接指向官\s*网。\n?",text)
        if m:return m.end()
    if "PDF正文阅读版" in text[:300]:
        m=re.search(r"PDF正文阅读版[^\n]*原始HWPX[^\n]*\n",text[:400])
        if m:return m.end()
    return 0
def is_heading(line,tok):
    s=line.strip()
    if not s or len(s)>75 or count(tok,s)>24:return False
    if re.search(r"(?:한다|있음|없음|가능|함|됩니다|습니다)[.!]?$",s):return False
    return bool(re.match(r"제\s*\d+\s*장",s) or
        re.fullmatch(r"(?:[0-9]+[.)]|[가-하A-Z][.)]|[▣∙])\s*[^:：.;。]{2,45}",s) or
        re.fullmatch(r"[^:：.;。]{2,35}(?:안내|요건|유의사항|신청|자격|절차|이수|등록|Documents|Procedure|Notes)",s))
def units(text,start,tok):
    """Every character belongs to a unit; PDF line wraps stay within clauses."""
    lines=[];pos=0
    for line in text.splitlines(keepends=True):
        end=pos+len(line)
        if end>start:lines.append((max(start,pos),end,line[max(0,start-pos):]))
        pos=end
    cuts=[start]
    for a,b,line in lines:
        if a>start and (START.match(line) or is_heading(line,tok)):cuts.append(a)
    cuts.append(len(text))
    return [(a,b) for a,b in zip(cuts,cuts[1:]) if b>a]
def short(tok,s,budget):
    s=norm(s)
    if count(tok,s)<=budget:return s
    offsets=tok(s,add_special_tokens=False,return_offsets_mapping=True)["offset_mapping"]
    for _,end in reversed(offsets):
        candidate=s[:end].rstrip()+"…"
        if count(tok,candidate)<=budget:return candidate
    return ""
def prefix(tok,meta,heading,cfg):
    # Full metadata are stored separately; abbreviations apply only to embedding context.
    essential=meta["school_name"]+" | "+meta["scope_tag"]
    title=short(tok,meta["title_ko"],cfg["metadata_title_tokens"])
    hd=short(tok,heading,cfg["metadata_heading_tokens"])
    parts=[essential,title,hd]
    result=" | ".join(x for x in parts if x)+"\n"
    while count(tok,result)>cfg["metadata_max_tokens"]:
        if hd:hd=short(tok,hd,max(3,count(tok,hd)-2))
        elif title:title=short(tok,title,max(3,count(tok,title)-2))
        else:raise ValueError("Essential metadata exceeds budget")
        result=" | ".join(x for x in [essential,title,hd] if x)+"\n"
        if hd=="…":hd=""
        if title=="…":title=""
    return result
def split_long(text,a,b,pre,tok,limit):
    if count(tok,pre+norm(text[a:b]))<=limit:return [(a,b,"clause")]
    # Prefer a complete sentence, then a PDF line or subclause; never discard characters.
    cuts=sorted(set([a,b]+[a+m.end() for m in re.finditer(r"[。！？!?]\s*|(?<!\d)[.]\s+|[;；]\s*|\n|[,，]\s*",text[a:b])]))
    result=[];start=a
    while start<b:
        if count(tok,pre+norm(text[start:b]))<=limit:
            result.append((start,b,"long_clause_tail"));break
        fits=[end for end in cuts if end>start and count(tok,pre+norm(text[start:end]))<=limit]
        if fits:end=max(fits);why="sentence_line_or_subclause"
        else:
            off=tok(text[start:b],add_special_tokens=False,return_offsets_mapping=True)["offset_mapping"]
            ends=sorted(set(start+y for x,y in off if y>0))
            # Bounded by at most limit raw tokens, then verify actual concatenated input.
            fits=[end for end in ends[:limit] if count(tok,pre+norm(text[start:end]))<=limit]
            if not fits:raise ValueError("Cannot fit even one source character")
            end=max(fits);why="token_fallback"
        result.append((start,end,why));start=end
    return result
def make_metadata(cfg,pages):
    catalog={str(x["id"]).zfill(2):x for x in readj(path(cfg["source_catalog"]))}
    result={}
    for doc in sorted({p["doc_id"] for p in pages}):
        entry=catalog[cfg["document_source_ids"][doc]]
        scope=entry["scope"]
        scope_class="undergraduate" if "本科" in scope else "graduate" if ("大学院" in scope or "研究生" in scope) else "unknown"
        tag={"undergraduate":"학부","graduate":"대학원","unknown":"범위 미확인"}[scope_class]
        if "外国留学生" in scope:tag+=" 외국인 유학생"
        result[doc]={"doc_id":doc,"school":doc.split("_")[0],"school_name":cfg["school_names"][doc.split("_")[0]],
          "title_ko":entry["title_ko"],"title_zh":entry["title_zh"],"scope":scope,"scope_class":scope_class,
          "scope_tag":tag,"source_url":entry.get("source_url"),"source_catalog_id":entry["id"],
          "scope_note":"Document-level scope, not proof that every clause applies to every graduate program."}
    return result
def chunk_pages(pages,metadata,tok,cfg):
    records=[];archives=[];page_audits=[];warnings=[]
    sequence=defaultdict(int);heading_by_doc={}
    for page in pages:
        doc=page["doc_id"];text=page["text"];body_start=archive_end(text,page["page_number"])
        if body_start:
            archives.append({"doc_id":doc,"page_number":page["page_number"],"start":0,"end":body_start,
                "text":text[:body_start],"sha256":digest(text[:body_start]),"rule":"explicit_archive_template"})
        heading=heading_by_doc.get(doc,"");parts=[]
        for i,(a,b) in enumerate(units(text,body_start,tok),1):
            first=text[a:b].splitlines()[0] if text[a:b].splitlines() else ""
            if is_heading(first,tok):heading=norm(first)
            pre=prefix(tok,metadata[doc],heading,cfg)
            divided=split_long(text,a,b,pre,tok,cfg["max_tokens"])
            if len(divided)>1:warnings.append({"doc_id":doc,"page_number":page["page_number"],
                "clause_id":f"{doc}_p{page['page_number']}_u{i}","start":a,"end":b,"parts":len(divided),
                "reason":"Full clause plus metadata exceeds 128 tokens; original characters retained."})
            for a2,b2,why in divided:
                parts.append({"start":a2,"end":b2,"heading":heading,"prefix":pre,
                 "clause_id":f"{doc}_p{page['page_number']}_u{i}","split_reason":why})
        heading_by_doc[doc]=heading
        groups=[];current=[]
        for part in parts:
            trial=current+[part]
            same=not current or current[0]["prefix"]==part["prefix"]
            combined=part["prefix"]+norm(text[trial[0]["start"]:trial[-1]["end"]])
            if current and (not same or count(tok,combined)>cfg["target_tokens"]):
                groups.append(current);current=[part]
            else:current=trial
        if current:groups.append(current)
        coverage=bytearray(len(text))
        for gi,group in enumerate(groups):
            a=group[0]["start"];b=group[-1]["end"];pre=group[0]["prefix"];overlap=None
            if gi>0:
                prev=groups[gi-1][-1]
                prevtxt=text[prev["start"]:prev["end"]]
                if (prev["end"]==a and prev["prefix"]==pre and prev["split_reason"]=="clause"
                    and count(tok,prevtxt)<=cfg["overlap_max_tokens"]
                    and count(tok,pre+norm(text[prev["start"]:b]))<=cfg["max_tokens"]):
                    overlap={"start":prev["start"],"end":a};a=prev["start"]
            body=text[a:b];encoded=pre+norm(body);n=count(tok,encoded)
            if n>cfg["max_tokens"]:raise AssertionError("Silent truncation prohibited")
            sequence[doc]+=1
            record={"chunk_id":f"{cfg['version']}__{doc}__{sequence[doc]:04d}","doc_id":doc,
             "source_file":page["source_file"],"page_number":page["page_number"],"text":body,
             "embedding_text":encoded,"token_count":n,"metadata_prefix":pre,
             "document_metadata":metadata[doc],"section_title":group[0]["heading"],
             "source_spans":[{"doc_id":doc,"page_number":page["page_number"],"start":a,"end":b,"sha256":digest(body)}],
             "clauses":group,"overlap":overlap,"body_sha256":digest(body)}
            records.append(record)
            coverage[a:b]=bytes([1])*(b-a)
        missing=[i for i in range(body_start,len(text)) if not coverage[i]]
        assert not missing,(doc,page["page_number"],missing[:10])
        page_audits.append({"doc_id":doc,"page_number":page["page_number"],"source_text_sha256":digest(text),
          "total_characters":len(text),"archive_start":0,"archive_end":body_start,
          "official_or_uncertain_start":body_start,"official_or_uncertain_end":len(text),
          "official_or_uncertain_characters":len(text)-body_start,
          "covered_characters":sum(coverage[body_start:]),"coverage":1.0,"uncovered_ranges":[]})
    return records,archives,page_audits,warnings
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);args=ap.parse_args()
    cfg=readj(path(args.config));version=path(cfg["output_dir"]);verify_seal(version);verify_protected(version)
    if (version/"chunks.jsonl").exists():raise FileExistsError("Refusing to overwrite chunks")
    log=Log(version,"chunking");log.event("start",config=args.config,qa_inputs_read=False)
    pages=jl(path(cfg["pages"]));tok=load_tokenizer();meta=make_metadata(cfg,pages)
    records,archives,audits,warnings=chunk_pages(pages,meta,tok,cfg)
    # Independently reconstruct every source span; audit is over exact characters, including whitespace.
    pm={(p["doc_id"],p["page_number"]):p["text"] for p in pages}
    for r in records:
        assert r["text"]=="".join(pm[(s["doc_id"],s["page_number"])][s["start"]:s["end"]] for s in r["source_spans"])
        assert r["token_count"]==count(tok,r["embedding_text"])<=128
    writejl(version/"chunks.jsonl",records);writejl(version/"archive_notes.jsonl",archives)
    writejl(version/"document_metadata.jsonl",list(meta.values()))
    writej(version/"chunking_audit.json",{"time":now(),"coverage_basis":"Existing pages.jsonl, official-or-uncertain text; does not certify PDF extraction completeness.",
       "coverage":1.0,"official_or_uncertain_characters":sum(x["official_or_uncertain_characters"] for x in audits),
       "archive_characters":sum(x["archive_end"] for x in audits),"pages":audits,"warnings":warnings,
       "chunk_count":len(records),"max_tokens":max(r["token_count"] for r in records),"over_limit":0,
       "cross_page_merge":False,"cross_page_policy":"Page boundaries retained conservatively; no guessed table/paragraph repair.",
       "protected_inputs":verify_protected(version)})
    log.event("complete",chunks=len(records),coverage=1.0,split_clauses=len(warnings),archive_pages=len(archives),max_tokens=max(r["token_count"] for r in records))
if __name__=="__main__":main()
