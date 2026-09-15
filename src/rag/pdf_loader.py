"""
Extract text from NASA PDFs and stream JSON chunks to disk.
Memory‑safe: processes one page at a time.
"""
import json
from pathlib import Path
import PyPDF2

PDF_DIR = Path("data/raw")
OUTPUT_FILE = Path("data/extracted/pdf_chunks.json")


def iter_chunks(text, chunk_size=800, overlap=100):
    """Yield text chunks without building a full list."""
    if not text:
        return
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        yield text[start:end]
        if end == text_len:
            break
        start = end - overlap


def main():
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found.")
        return

    total_chunks = 0
    first = True

    # Open output file once and write JSON array manually
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("[\n")

        for pdf_path in pdf_files:
            print(f"Processing {pdf_path.name}...")
            try:
                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    num_pages = len(reader.pages)
                    print(f"  Pages: {num_pages}")

                    for page_num, page in enumerate(reader.pages):
                        try:
                            text = page.extract_text() or ""
                        except Exception as e:
                            print(f"    Page {page_num} extraction error: {e}")
                            text = ""

                        for chunk in iter_chunks(text):
                            if not first:
                                out.write(",\n")
                            out.write(json.dumps({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "chunk_id": total_chunks,
                                "text": chunk
                            }))
                            first = False
                            total_chunks += 1

                            # Optional progress every 100 chunks
                            if total_chunks % 100 == 0:
                                print(f"    {total_chunks} chunks written...")
            except Exception as e:
                print(f"  Failed to process {pdf_path.name}: {e}")

        out.write("\n]")

    print(f"\n✅ Saved {total_chunks} chunks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()