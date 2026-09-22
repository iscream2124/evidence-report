import json
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from evidence_report.core import (add_evidence, add_source, completion_failures,
                                  create_run, extract_pdfs, read_json)


class EvidenceRunTest(unittest.TestCase):
    def test_local_pdf_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf = root / "official.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            with pdf.open("wb") as stream:
                writer.write(stream)

            run = create_run("조리로봇 참여요건", root / "runs")
            source = add_source(run, str(pdf), official=True)
            result = extract_pdfs(run)
            claim = add_evidence(run, claim="외산 로봇 신청 가능", status="confirmed",
                                 source_id=source["id"], page=1, section="Q7")

            self.assertEqual(result[0]["pages"], 1)
            self.assertEqual(claim["source_sha256"], source["sha256"])
            state = read_json(run / "qa/run-state.json")
            self.assertTrue(state["official_sources_secured"])
            self.assertTrue(state["page_level_evidence_recorded"])
            self.assertTrue(state["claim_states_separated"])
            evidence = json.loads((run / "evidence/evidence.json").read_text())
            self.assertEqual(evidence["claims"][0]["page"], 1)
            self.assertIn("critical_pages_visually_checked", completion_failures(state))

    def test_pdf_magic_allows_non_pdf_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_path = root / "FileDown.do"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            with source_path.open("wb") as stream:
                writer.write(stream)
            run = create_run("확장자 없는 PDF", root / "runs")
            add_source(run, str(source_path), official=True)
            self.assertEqual(extract_pdfs(run)[0]["pages"], 1)


if __name__ == "__main__":
    unittest.main()
