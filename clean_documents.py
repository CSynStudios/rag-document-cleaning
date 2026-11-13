import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup
from datasketch import MinHash, MinHashLSH

MAX_BYTES = 2_000_000
MAX_DOCUMENTS = 200
CHUNK_WORDS = 180
OVERLAP_WORDS = 30
SIMILARITY_THRESHOLD = 0.90
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE)
PHONE = re.compile(
    r"(?<!\w)(?:\+63[ .-]?9\d{2}[ .-]?\d{3}[ .-]?\d{4}"
    r"|09\d{2}[ .-]?\d{3}[ .-]?\d{4}"
    r"|\+1[ .-]?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4})(?!\d)"
)


def source_id(relative_path):
    return "src-" + hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:16]


def extract_text(content, suffix):
    if suffix in {".html", ".htm"}:
        soup = BeautifulSoup(content, "html.parser")
        for element in soup.select(
            "script, style, noscript, nav, header, footer, aside, head, "
            "[hidden], [aria-hidden='true'], .sphinxsidebar, .related, .headerlink"
        ):
            element.decompose()
        section = soup.select_one("main, [role='main'], article") or soup.body or soup
        content = section.get_text(" ", strip=True)
    return " ".join(unicodedata.normalize("NFC", content).split())


def redact_contacts(text):
    text, email_count = EMAIL.subn("[EMAIL]", text)
    text, phone_count = PHONE.subn("[PHONE]", text)
    return text, {"email": email_count, "phone": phone_count}


def word_shingles(text):
    words = re.findall(r"\w+", text.casefold())
    width = min(5, len(words))
    if not width:
        return set()
    return {" ".join(words[start : start + width]) for start in range(len(words) - width + 1)}


def chunk_text(text):
    words = text.split()
    for start in range(0, len(words), CHUNK_WORDS - OVERLAP_WORDS):
        end = min(start + CHUNK_WORDS, len(words))
        yield {"word_start": start, "word_end": end, "text": " ".join(words[start:end])}
        if end == len(words):
            break


def clean_documents(input_directory, output_directory):
    input_directory = Path(input_directory).resolve()
    output_directory = Path(output_directory).resolve()
    if not input_directory.is_dir():
        raise ValueError("Input must be an existing directory.")
    if output_directory.is_relative_to(input_directory) or input_directory.is_relative_to(output_directory):
        raise ValueError("Input and output directories must be separate, without nesting.")
    if output_directory.exists():
        raise ValueError("Output directory already exists; choose a new run directory.")
    paths = []
    for path in input_directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".htm", ".txt"}:
            if path.is_symlink():
                raise ValueError("Symbolic-link inputs are not supported.")
            paths.append(path)
            if len(paths) > MAX_DOCUMENTS:
                raise ValueError(f"This milestone supports at most {MAX_DOCUMENTS} documents per run.")
    if not paths:
        raise ValueError("No HTML or text files were found.")

    retained_documents = []
    chunks = []
    decisions = []
    exact_matches = {}
    shingle_sets = {}
    lsh = MinHashLSH(threshold=0.80, num_perm=128)
    redaction_totals = Counter({"email": 0, "phone": 0})

    for path in sorted(paths):
        identifier = source_id(path.relative_to(input_directory).as_posix())
        decision = {"source_id": identifier}
        with path.open("rb") as stream:
            payload = stream.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            decisions.append({**decision, "status": "rejected_too_large"})
            continue
        try:
            content = payload.decode("utf-8-sig")
        except UnicodeDecodeError:
            decisions.append({**decision, "status": "rejected_encoding"})
            continue
        if "\x00" in content:
            decisions.append({**decision, "status": "rejected_binary"})
            continue
        text = extract_text(content, path.suffix.lower())
        if not text:
            decisions.append({**decision, "status": "rejected_empty"})
            continue
        decision["cleaned_characters"] = len(text)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in exact_matches:
            decisions.append({**decision, "status": "exact_duplicate", "duplicate_of": exact_matches[digest]})
            continue

        shingles = word_shingles(text)
        signature = MinHash(num_perm=128, seed=42)
        for shingle in sorted(shingles):
            signature.update(shingle.encode("utf-8"))
        duplicate = None
        if shingles:
            for candidate in sorted(lsh.query(signature)):
                candidate_shingles = shingle_sets[candidate]
                similarity = len(shingles & candidate_shingles) / len(shingles | candidate_shingles)
                if similarity >= SIMILARITY_THRESHOLD:
                    duplicate = {"duplicate_of": candidate, "jaccard": round(similarity, 6)}
                    break
        if duplicate:
            decisions.append({**decision, "status": "near_duplicate", **duplicate})
            continue

        exact_matches[digest] = identifier
        if shingles:
            shingle_sets[identifier] = shingles
            lsh.insert(identifier, signature)
        redacted_text, redactions = redact_contacts(text)
        redaction_totals.update(redactions)
        document_chunks = list(chunk_text(redacted_text))
        retained_documents.append(
            {"source_id": identifier, "text": redacted_text, "redactions": redactions}
        )
        for index, chunk in enumerate(document_chunks):
            chunks.append({"chunk_id": f"{identifier}-{index:04d}", "source_id": identifier, **chunk})
        decisions.append(
            {**decision, "status": "retained", "redactions": redactions, "chunks": len(document_chunks)}
        )

    report = {
        "schema_version": 1,
        "settings": {
            "chunk_words": CHUNK_WORDS,
            "overlap_words": OVERLAP_WORDS,
            "near_duplicate_jaccard": SIMILARITY_THRESHOLD,
            "lsh_candidate_threshold": 0.80,
            "minhash_permutations": 128,
            "minhash_seed": 42,
            "shingle_words": 5,
            "redaction_scope": ["email", "PH mobile", "US phone with +1 prefix"],
        },
        "summary": {
            "input_documents": len(paths),
            "retained_documents": len(retained_documents),
            "chunks": len(chunks),
            "statuses": dict(sorted(Counter(entry["status"] for entry in decisions).items())),
            "redactions_in_retained_documents": dict(redaction_totals),
        },
        "documents": decisions,
    }
    output_directory.mkdir(parents=True)
    for filename, records in (("documents.jsonl", retained_documents), ("chunks.jsonl", chunks)):
        with (output_directory / filename).open("w", encoding="utf-8", newline="\n") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    (output_directory / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description="Clean local UTF-8 HTML/text into redacted, deduplicated chunks.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        report = clean_documents(arguments.input, arguments.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cleaning failed: {error}\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
