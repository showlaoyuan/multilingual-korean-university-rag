"""Encode only preregistered new chunks with the unchanged local model."""
import argparse
from token128_common import *
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--version-dir",required=True);args=ap.parse_args()
    v=path(args.version_dir);verify_seal(v);verify_protected(v)
    dest=v/"embeddings"
    if dest.exists():raise FileExistsError("Refusing to overwrite embedding directory")
    log=Log(v,"embedding");log.event("start",model=MODEL,snapshot=SNAPSHOT)
    rows=jl(v/"chunks.jsonl");model=load_model();texts=[r["embedding_text"] for r in rows]
    for r in rows:
        ids=model.tokenizer(r["embedding_text"],truncation=False,add_special_tokens=True)["input_ids"]
        assert len(ids)==r["token_count"]<=128
        actual=model.tokenize([r["embedding_text"]])["input_ids"][0].tolist()
        assert actual==ids,"Model silently changed/truncated tokens"
    import numpy as np
    matrix=model.encode(texts,batch_size=16,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False)
    assert matrix.shape==(len(rows),384) and np.isfinite(matrix).all()
    assert np.allclose(np.linalg.norm(matrix,axis=1),1,atol=1e-6)
    dest.mkdir()
    with (dest/"chunk_embeddings.npy").open("xb") as fp:np.save(fp,matrix)
    mapping=[{"row":i,"chunk_id":r["chunk_id"],"embedding_text_sha256":digest(r["embedding_text"]),
      "body_sha256":r["body_sha256"],"token_count":r["token_count"]} for i,r in enumerate(rows)]
    writejl(dest/"embedding_rows.jsonl",mapping)
    import sentence_transformers,transformers,torch
    writej(dest/"embedding_metadata.json",{"model_name":MODEL,"snapshot":SNAPSHOT,"max_seq_length":model.max_seq_length,
      "chunk_count":len(rows),"embedding_dimension":384,"normalized":True,"offline":True,"device":str(model.device),
      "chunks_sha256":sha(v/"chunks.jsonl"),"row_mapping_sha256":sha(dest/"embedding_rows.jsonl"),
      "matrix_sha256":sha(dest/"chunk_embeddings.npy"),"truncated_inputs":0,
      "versions":{"sentence_transformers":sentence_transformers.__version__,"transformers":transformers.__version__,"torch":torch.__version__},
      "protected_inputs":verify_protected(v)})
    log.event("complete",shape=list(matrix.shape),truncated_inputs=0,protected=verify_protected(v))
if __name__=="__main__":main()
