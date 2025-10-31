# People's Daily PDF

Generate a single PDF of People's Daily by fetching and stitching the official page PDFs.

## Requirements

- Python 3.12 or newer
- `requests`, `pypdf`, `pytest` (development) — install with:

  ```bash
  pip install -r requirements.txt
  ```

- Optional: [Ghostscript](https://ghostscript.com/) if you plan to use `--compress` for file-size reduction.

## Usage

```bash
python peoples_daily.py [-h] [-d DATE] [-o OUTPUT] [-v] [--compress]
```

| Flag | Description | Default |
| ---- | ----------- | ------- |
| `-d`, `--date` | Issue date (YYYY-MM-DD). | today |
| `-o`, `--output` | Output filename. | `人民日报_<date>.pdf` |
| `-v`, `--verbose` | Print progress + warning details. | off |
| `--compress` | Run Ghostscript to shrink the merged PDF. | off |

## Examples

Fetch today's paper:

```bash
python peoples_daily.py
```

Show CLI help and available options:

```bash
python peoples_daily.py -h
```

Save the 2025-10-15 issue to a custom file with verbose logging:

```bash
python peoples_daily.py -d 2025-10-15 -o paper.pdf -v
```

Produce a compressed version (requires Ghostscript on PATH):

```bash
python peoples_daily.py -d 2025-10-15 --compress
```

## Notes

- Compression uses Ghostscript with the `/ebook` profile. The script skips compression automatically if Ghostscript is not available.
- Verbose mode surfaces upstream PDF parsing warnings that are hidden by default.
