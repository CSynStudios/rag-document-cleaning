import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from clean_documents import MAX_BYTES, source_id

SOURCES = {
    "csv.html": "https://docs.python.org/3.12/library/csv.html",
    "json.html": "https://docs.python.org/3.12/library/json.html",
    "textwrap.html": "https://docs.python.org/3.12/library/textwrap.html",
    "python-docs.license": "https://docs.python.org/3.12/license.html",
}


def fetch_sample(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Destination already exists; use a new directory to preserve the previous sample.")
    downloads = []
    for filename, url in SOURCES.items():
        request = Request(url, headers={"User-Agent": "VeyraPortfolioSample/0.1"})
        with urlopen(request, timeout=30) as response:
            if response.headers.get_content_type() != "text/html":
                raise ValueError("Expected an HTML response from the documentation source.")
            payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("A documentation page exceeds the sample size limit.")
        payload.decode("utf-8-sig")
        downloads.append((filename, url, payload))
    destination.mkdir(parents=True)
    manifest = []
    for filename, url, payload in downloads:
        (destination / filename).write_bytes(payload)
        manifest.append(
            {
                "filename": filename,
                "source_id": source_id(filename),
                "url": url,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
            }
        )
    (destination / "sources.json").write_text(
        json.dumps({"downloaded_at": datetime.now(timezone.utc).isoformat(), "sources": manifest}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(downloads) - 1} documentation pages and a license page.")


def main():
    parser = argparse.ArgumentParser(description="Download three official Python documentation pages for a local demo.")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        fetch_sample(arguments.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Sample download failed: {error}\n")


if __name__ == "__main__":
    main()
