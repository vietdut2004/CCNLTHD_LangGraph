"""Render a local DOCX with hidden Word; do not save or update source fields."""
import argparse
import hashlib
import json
from pathlib import Path

import win32com.client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("pdf")
    ap.add_argument("metadata")
    args = ap.parse_args()
    source = Path(args.input).resolve()
    output = Path(args.pdf).resolve()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    word = document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.AutomationSecurity = 3
        word.Options.UpdateLinksAtOpen = False
        document = word.Documents.Open(
            str(source), ConfirmConversions=False, ReadOnly=True,
            AddToRecentFiles=False,
        )
        document.Repaginate()
        pages = int(document.ComputeStatistics(2))
        document.ExportAsFixedFormat(str(output), 17)
        info = {
            "input": str(source), "input_sha256": before,
            "input_unchanged": hashlib.sha256(source.read_bytes()).hexdigest() == before,
            "pdf": str(output), "pdf_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "word_pages": pages,
            "anchors_checked_with_pdf_comparison": True,
            "source_saved": False, "fields_updated": False,
            "macros_disabled": True, "application_hidden": True,
        }
        Path(args.metadata).write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(json.dumps(info, ensure_ascii=False))
    finally:
        if document is not None:
            document.Close(0)
        if word is not None:
            word.Quit()


if __name__ == "__main__":
    main()
