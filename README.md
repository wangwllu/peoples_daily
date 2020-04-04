# People's Daily PDF

A Python script for generating a PDF file for People's Daily.

## Usage

```
usage: python peoples_daily.py [-h] [-d DATE] [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  the date, e.g., 2020-03-07
  -o OUTPUT, --output OUTPUT
                        the path to output the paper file, e.g., ./paper.pdf
```

## Examples

Generate today's People's Daily:

```bash
python peoples_daily.py
```

Generate People's Daily for a particular date (2020-03-07) and save it to `paper.pdf`:

```bash
python peoples_daily.py -d 2020-03-07 -o paper.pdf
```
