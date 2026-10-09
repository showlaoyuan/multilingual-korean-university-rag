"""Invariant tests independent of the 30 evaluation questions."""
import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from token128_common import *
from chunk_documents_token128 import archive_end,chunk_pages,split_long,units,norm
class TokenChunkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok=load_tokenizer();cls.cfg=readj(ROOT/"configs/chunking/token128_clause_v1.json")
        cls.meta={"example":{"school_name":"가상대학교","scope_tag":"학부","title_ko":"일반 규정","scope_class":"undergraduate"}}
    def check(self,text):
        pages=[{"doc_id":"example","source_file":"example.pdf","page_number":1,"text":text}]
        rows,archive,audit,warn=chunk_pages(pages,self.meta,self.tok,self.cfg)
        covered=set()
        for row in rows:
            self.assertLessEqual(count(self.tok,row["embedding_text"]),128)
            for s in row["source_spans"]:
                self.assertEqual(digest(text[s["start"]:s["end"]]),s["sha256"])
                covered.update(range(s["start"],s["end"]))
        self.assertEqual(covered,set(range(archive_end(text,1),len(text))))
        return rows,warn
    def test_long_unicode_clause_preserved(self):
        rows,warn=self.check("제1조(범위)\n① "+("학생은 해당 조건과 예외 사항을 모두 확인해야 한다. "*65)+"\n② 종료.\n")
        self.assertGreater(len(rows),1);self.assertTrue(warn)
    def test_unknown_preface_never_deleted(self):
        text="来源待核实：这段可能属于正文。\n가상대학교 학칙\n学生必须确认例外。\n"
        self.assertEqual(archive_end(text,1),0);self.check(text)
    def test_explicit_archive_partition(self):
        pre="本科指南\n大学官方来源\n以下为原文正文离线排版，未翻译或更改制度；表格保留原有合并单元格，图片链接指向官\n网。\n"
        self.assertEqual(archive_end(pre+"공식 본문\n",1),len(pre))
        self.assertEqual(archive_end(pre+"공식 본문\n",2),0)
        self.check(pre+"공식 본문\n")
    def test_table_and_whitespace_preserved(self):
        self.check("구분      유형 A      유형 B\n조건       17        29\n주의 : 예외가 있습니다.\n"*20)
    def test_lossless_clause_boundaries(self):
        txt="제1조(대상)\n① 모든 학생은\n조건을 확인한다.\n② 예외는 별도이다.\n"
        u=units(txt,0,self.tok)
        self.assertEqual("".join(txt[a:b] for a,b in u),txt)
        self.assertTrue(any("모든 학생은\n조건" in txt[a:b] for a,b in u))
    def test_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"immutable.json";writej(p,{"original":True})
            with self.assertRaises(FileExistsError):writej(p,{"original":False})
            self.assertEqual(readj(p),{"original":True})
if __name__=="__main__":unittest.main()
