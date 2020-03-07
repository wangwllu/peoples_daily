# People's Daily Crawler

Generate a PDF file for People's Daily.

## Usage

```
usage: python peoples_daily.py [-h] [-d DATE]

optional arguments:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  the date, e.g., 20200307
```

## Examples

Generate today's People's Daily:

```python
python peoples_daily.py
```

Generate People's Daily for a particular date (2020-03-07):

```python
python peoples_daily.py -d 20200307
```
