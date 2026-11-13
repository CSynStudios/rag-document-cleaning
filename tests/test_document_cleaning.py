import importlib.util
from contextlib import nullcontext
from email.message import Message
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("clean_documents", PROJECT / "clean_documents.py")
cleaner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cleaner
SPEC.loader.exec_module(cleaner)
FETCH_SPEC = importlib.util.spec_from_file_location("fetch_sample", PROJECT / "fetch_sample.py")
sample = importlib.util.module_from_spec(FETCH_SPEC)
FETCH_SPEC.loader.exec_module(sample)


def test_html_removes_boilerplate_and_preserves_inline_text():
    html = """<html><head><title>Navigation title</title></head><body>
    <nav>Menu links</nav><main><h1>Guide<a class="headerlink">¶</a></h1><p>Use <b>clean</b> text.</p>
    <script>secretScript()</script><span hidden>Hidden text</span>
    <span aria-hidden="true">Icon</span></main><footer>Footer links</footer></body></html>"""
    assert cleaner.extract_text(html, ".html") == "Guide Use clean text."


def test_redaction_supports_documented_formats_and_preserves_dates():
    text = "Email owner@example.org or alt+tag@example.com. Call +63 917 555 0123, 0917-555-0123 or +1 (202) 555-0123. Date 2026-11-13."
    redacted, counts = cleaner.redact_contacts(text)
    assert counts == {"email": 2, "phone": 3}
    assert "@" not in redacted
    assert "555" not in redacted
    assert "2026-11-13" in redacted


def test_redaction_does_not_claim_name_or_address_detection():
    text = "Alex Example lives at 123 Sample Street."
    assert cleaner.redact_contacts(text) == (text, {"email": 0, "phone": 0})


@pytest.mark.parametrize("length", [1, 179, 180, 181, 330, 331, 600])
def test_chunks_are_bounded_and_reconstruct_the_complete_text(length):
    words = [f"word{index}" for index in range(length)]
    chunks = list(cleaner.chunk_text(" ".join(words)))
    reconstructed = chunks[0]["text"].split()
    for previous, current in zip(chunks, chunks[1:]):
        assert current["word_start"] == previous["word_end"] - cleaner.OVERLAP_WORDS
        reconstructed.extend(current["text"].split()[cleaner.OVERLAP_WORDS :])
    assert reconstructed == words
    assert all(len(chunk["text"].split()) <= cleaner.CHUNK_WORDS for chunk in chunks)


def test_end_to_end_removes_duplicates_and_keeps_distinct_documents(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    paragraph = " ".join(f"term{index}" for index in range(100))
    (incoming / "a.txt").write_text(paragraph, encoding="utf-8")
    (incoming / "b.html").write_text(f"<main><p>{paragraph}</p></main>", encoding="utf-8")
    (incoming / "c.txt").write_text(paragraph + " revised", encoding="utf-8")
    (incoming / "d.txt").write_text("Contact owner@example.org for a separate invoice.", encoding="utf-8")
    (incoming / "empty.txt").write_text("  ", encoding="utf-8")
    (incoming / "invalid.txt").write_bytes(b"\xff\xfe\x00")
    (incoming / "binary.txt").write_bytes(b"text\x00binary")
    (incoming / "large.txt").write_bytes(b"x" * (cleaner.MAX_BYTES + 1))
    output = tmp_path / "outputs"
    report = cleaner.clean_documents(incoming, output)
    assert report["summary"]["statuses"] == {
        "retained": 2,
        "exact_duplicate": 1,
        "near_duplicate": 1,
        "rejected_empty": 1,
        "rejected_encoding": 1,
        "rejected_binary": 1,
        "rejected_too_large": 1,
    }
    assert report["summary"]["redactions_in_retained_documents"] == {"email": 1, "phone": 0}
    documents = [json.loads(line) for line in (output / "documents.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(documents) == 2
    assert all("owner@example.org" not in document["text"] for document in documents)
    assert "owner@example.org" not in (output / "report.json").read_text(encoding="utf-8")
    assert (output / "chunks.jsonl").is_file()


def test_outputs_are_deterministic(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "a.txt").write_text("A short, useful guide.", encoding="utf-8")
    cleaner.clean_documents(incoming, tmp_path / "run1")
    cleaner.clean_documents(incoming, tmp_path / "run2")
    for filename in ("documents.jsonl", "chunks.jsonl", "report.json"):
        assert (tmp_path / "run1" / filename).read_bytes() == (tmp_path / "run2" / filename).read_bytes()


def test_existing_output_is_preserved(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    output = tmp_path / "outputs"
    output.mkdir()
    (output / "keep.txt").write_text("Preserve this file", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        cleaner.clean_documents(incoming, output)
    assert (output / "keep.txt").read_text(encoding="utf-8") == "Preserve this file"


def test_rejects_nested_output_and_missing_inputs(tmp_path):
    with pytest.raises(ValueError, match="existing directory"):
        cleaner.clean_documents(tmp_path / "missing", tmp_path / "output")
    with pytest.raises(ValueError, match="without nesting"):
        cleaner.clean_documents(tmp_path, tmp_path / "output")
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    with pytest.raises(ValueError, match="No HTML or text"):
        cleaner.clean_documents(incoming, tmp_path / "output")


def test_enforces_document_limit(tmp_path, monkeypatch):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    for index in range(3):
        (incoming / f"{index}.txt").write_text("text", encoding="utf-8")
    monkeypatch.setattr(cleaner, "MAX_DOCUMENTS", 2)
    with pytest.raises(ValueError, match="at most 2"):
        cleaner.clean_documents(incoming, tmp_path / "outputs")


def test_false_positive_lsh_candidate_is_retained(tmp_path, monkeypatch):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "a.txt").write_text("Instructions for cleaning tables and normalizing invoices.", encoding="utf-8")
    (incoming / "b.txt").write_text("The moon orbits Earth and reflects sunlight.", encoding="utf-8")
    candidates = iter([[], [cleaner.source_id("a.txt")]])
    monkeypatch.setattr(cleaner.MinHashLSH, "query", lambda self, signature: next(candidates))
    report = cleaner.clean_documents(incoming, tmp_path / "outputs")
    assert report["summary"]["retained_documents"] == 2


def test_filenames_with_contacts_are_not_written_to_outputs(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "owner@example.org.txt").write_text("Useful content.", encoding="utf-8")
    output = tmp_path / "outputs"
    cleaner.clean_documents(incoming, output)
    assert all("owner@example.org" not in path.read_text(encoding="utf-8") for path in output.iterdir())


def test_downloader_preserves_source_provenance_without_network(tmp_path, monkeypatch):
    headers = Message()
    headers["Content-Type"] = "text/html; charset=utf-8"

    response = SimpleNamespace(headers=headers, read=lambda limit: b"<main>Sample documentation</main>"[:limit])
    monkeypatch.setattr(sample, "urlopen", lambda request, timeout: nullcontext(response))
    destination = tmp_path / "sample"
    sample.fetch_sample(destination)
    manifest = json.loads((destination / "sources.json").read_text(encoding="utf-8"))
    assert len(manifest["sources"]) == 4
    assert all(entry["url"].startswith("https://docs.python.org/3.12/") for entry in manifest["sources"])
    assert (destination / "python-docs.license").is_file()
    with pytest.raises(ValueError, match="already exists"):
        sample.fetch_sample(destination)


def test_downloader_rejects_non_html_response(tmp_path, monkeypatch):
    headers = Message()
    headers["Content-Type"] = "application/octet-stream"

    response = SimpleNamespace(headers=headers)
    monkeypatch.setattr(sample, "urlopen", lambda request, timeout: nullcontext(response))
    destination = tmp_path / "sample"
    with pytest.raises(ValueError, match="Expected an HTML"):
        sample.fetch_sample(destination)
    assert not destination.exists()
