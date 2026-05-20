import os
import argparse
import base64
import datetime
import tempfile
from unittest.mock import patch
from urllib.parse import urljoin
import pytest
from peoples_daily import Paper, PaperDownloadError, main, parse_date


def test_generate_today_pdf():
    with tempfile.TemporaryDirectory() as tmpfile:
        file_path = os.path.join(tmpfile, 'paper.pdf')
        date = datetime.date.today()
        paper = Paper(date)
        expected_first_url = (
            'https://paper.people.com.cn/rmrb/pc/PDF/'
            f"{date:%Y%m}/{date:%d}/rmrb{date:%Y%m%d}01.pdf"
        )
        minimal_pdf = base64.b64decode(
            'JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyAz'
            'IDAgUiBdCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9Qcm9kdWNlciAoUHlQREYyKQovTmVlZEFwcGVh'
            'cmFuY2VzIHRydWUKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAxIDAg'
            'UgovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAgMCA1OTUgODQyIF0KPj4KZW5kb2JqCjQg'
            'MCBvYmoKPDwKL1R5cGUgL0NhdGFsb2cKL1BhZ2VzIDEgMCBSCi9BY3JvRm9ybSAyIDAgUgo+Pgpl'
            'bmRvYmoKeHJlZgowIDUKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAw'
            'MDAwMDAwNzQgMDAwMDAgbiAKMDAwMDAwMDEzNiAwMDAwMCBuIAowMDAwMDAwMjI2IDAwMDAwIG4g'
            'CnRyYWlsZXIKPDwKL1NpemUgNQovUm9vdCA0IDAgUgovSW5mbyAyIDAgUgo+PgpzdGFydHhyZWYK'
            'MjkxCiUlRU9GCg=='
        )

        def fake_get(url, timeout):
            class DummyResponse:
                def __init__(self, ok, content=b''):
                    self.ok = ok
                    self.content = content
                    self.headers = {}

            if url == expected_first_url:
                return DummyResponse(True, minimal_pdf)
            return DummyResponse(False)

        class DummySession:
            def get(self, url, timeout):
                return fake_get(url, timeout)

        with patch.object(paper, '_iter_sessions', return_value=[DummySession()]):
            with patch.object(
                paper,
                '_resolve_pdf_url',
                side_effect=lambda serial: (
                    expected_first_url if serial == 1 else None
                ),
            ):
                paper(file_path)
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0


def test_generate_today_pdf_with_compression():
    with tempfile.TemporaryDirectory() as tmpfile:
        file_path = os.path.join(tmpfile, 'paper.pdf')
        date = datetime.date.today()
        paper = Paper(date, compress=True)
        expected_first_url = (
            'https://paper.people.com.cn/rmrb/pc/PDF/'
            f"{date:%Y%m}/{date:%d}/rmrb{date:%Y%m%d}01.pdf"
        )
        minimal_pdf = base64.b64decode(
            'JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyAz'
            'IDAgUiBdCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9Qcm9kdWNlciAoUHlQREYyKQovTmVlZEFwcGVh'
            'cmFuY2VzIHRydWUKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAxIDAg'
            'UgovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAgMCA1OTUgODQyIF0KPj4KZW5kb2JqCjQg'
            'MCBvYmoKPDwKL1R5cGUgL0NhdGFsb2cKL1BhZ2VzIDEgMCBSCi9BY3JvRm9ybSAyIDAgUgo+Pgpl'
            'bmRvYmoKeHJlZgowIDUKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAw'
            'MDAwMDAwNzQgMDAwMDAgbiAKMDAwMDAwMDEzNiAwMDAwMCBuIAowMDAwMDAwMjI2IDAwMDAwIG4g'
            'CnRyYWlsZXIKPDwKL1NpemUgNQovUm9vdCA0IDAgUgovSW5mbyAyIDAgUgo+PgpzdGFydHhyZWYK'
            'MjkxCiUlRU9GCg=='
        )

        def fake_get(url, timeout):
            class DummyResponse:
                def __init__(self, ok, content=b''):
                    self.ok = ok
                    self.content = content
                    self.headers = {}

            if url == expected_first_url:
                return DummyResponse(True, minimal_pdf)
            return DummyResponse(False)

        class DummySession:
            def get(self, url, timeout):
                return fake_get(url, timeout)

        with patch.object(paper, '_compress', wraps=paper._compress) as compress_spy:
            with patch.object(paper, '_iter_sessions', return_value=[DummySession()]):
                with patch.object(
                    paper,
                    '_resolve_pdf_url',
                    side_effect=lambda serial: (
                        expected_first_url if serial == 1 else None
                    ),
                ):
                    paper(file_path)

        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
        compress_spy.assert_called_once()


def test_generate_today_pdf_without_compression():
    with tempfile.TemporaryDirectory() as tmpfile:
        file_path = os.path.join(tmpfile, 'paper.pdf')
        date = datetime.date.today()
        paper = Paper(date, compress=False)
        expected_first_url = (
            'https://paper.people.com.cn/rmrb/pc/PDF/'
            f"{date:%Y%m}/{date:%d}/rmrb{date:%Y%m%d}01.pdf"
        )
        minimal_pdf = base64.b64decode(
            'JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyAz'
            'IDAgUiBdCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9Qcm9kdWNlciAoUHlQREYyKQovTmVlZEFwcGVh'
            'cmFuY2VzIHRydWUKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAxIDAg'
            'UgovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAgMCA1OTUgODQyIF0KPj4KZW5kb2JqCjQg'
            'MCBvYmoKPDwKL1R5cGUgL0NhdGFsb2cKL1BhZ2VzIDEgMCBSCi9BY3JvRm9ybSAyIDAgUgo+Pgpl'
            'bmRvYmoKeHJlZgowIDUKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAw'
            'MDAwMDAwNzQgMDAwMDAgbiAKMDAwMDAwMDEzNiAwMDAwMCBuIAowMDAwMDAwMjI2IDAwMDAwIG4g'
            'CnRyYWlsZXIKPDwKL1NpemUgNQovUm9vdCA0IDAgUgovSW5mbyAyIDAgUgo+PgpzdGFydHhyZWYK'
            'MjkxCiUlRU9GCg=='
        )

        def fake_get(url, timeout):
            class DummyResponse:
                def __init__(self, ok, content=b''):
                    self.ok = ok
                    self.content = content
                    self.headers = {}

            if url == expected_first_url:
                return DummyResponse(True, minimal_pdf)
            return DummyResponse(False)

        class DummySession:
            def get(self, url, timeout):
                return fake_get(url, timeout)

        with patch.object(paper, '_compress', wraps=paper._compress) as compress_spy:
            with patch.object(paper, '_iter_sessions', return_value=[DummySession()]):
                with patch.object(
                    paper,
                    '_resolve_pdf_url',
                    side_effect=lambda serial: (
                        expected_first_url if serial == 1 else None
                    ),
                ):
                    paper(file_path)

        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
        compress_spy.assert_not_called()


def test_compress_uses_ghostscript_when_available():
    date = datetime.date.today()
    paper = Paper(date)
    original = b'original'
    optimized = b'ghost'

    with patch.object(paper, '_compress_with_ghostscript', return_value=optimized) as gs_mock:
        result = paper._compress(original)

    assert result == optimized
    gs_mock.assert_called_once_with(original)


def test_compress_returns_original_when_ghostscript_unavailable():
    date = datetime.date.today()
    paper = Paper(date)
    original = b'original'

    with patch.object(paper, '_compress_with_ghostscript', return_value=None) as gs_mock:
        result = paper._compress(original)

    assert result == original
    gs_mock.assert_called_once_with(original)


def test_resolve_pdf_url_from_layout():
    date = datetime.date(2024, 7, 1)
    paper = Paper(date)
    layout_url = next(paper._layout_urls(1))
    html = (
        '<html><body><a href="../../pc/PDF/202407/01/rmrb2024070101.pdf">PDF</a>'
        '</body></html>'
    )

    class DummyResponse:
        def __init__(self, text):
            self.ok = True
            self.text = text

    class DummySession:
        def get(self, url, timeout):
            assert url == layout_url
            return DummyResponse(html)

    with patch.object(paper, '_iter_sessions', return_value=[DummySession()]):
        resolved_url = paper._resolve_pdf_url(1)

    assert resolved_url == urljoin(layout_url, '../../pc/PDF/202407/01/rmrb2024070101.pdf')


def test_fetch_page_rejects_non_pdf_content():
    date = datetime.date.today()
    paper = Paper(date)

    class DummyResponse:
        ok = True
        content = b'<html>not a pdf</html>'
        headers = {'Content-Type': 'text/html'}

    class DummySession:
        def get(self, url, timeout):
            return DummyResponse()

    with patch.object(paper, '_iter_sessions', return_value=[DummySession()]):
        with patch.object(paper, '_resolve_pdf_url', return_value='https://example.test/page.pdf'):
            with pytest.raises(PaperDownloadError, match='non-PDF'):
                paper._fetch_page(1)


def test_load_pages_raises_when_intermediate_pdf_download_fails():
    date = datetime.date.today()
    paper = Paper(date)

    class DummyResponse:
        def __init__(self, ok, content=b'%PDF-1.4\n'):
            self.ok = ok
            self.content = content
            self.headers = {}

    class DummySession:
        def get(self, url, timeout):
            return DummyResponse(not url.endswith('/2.pdf'))

    with patch.object(paper, '_iter_sessions', return_value=[DummySession()]):
        with patch.object(
            paper,
            '_resolve_pdf_url',
            side_effect=lambda serial: (
                f'https://example.test/{serial}.pdf' if serial <= 3 else None
            ),
        ):
            with pytest.raises(PaperDownloadError, match='page 2'):
                paper._load_pages()


def test_parse_date_rejects_invalid_date():
    with pytest.raises(argparse.ArgumentTypeError, match='invalid date'):
        parse_date('2025-02-30')


def test_main_reports_download_errors_without_traceback(capsys):
    with patch('sys.argv', ['peoples_daily.py', '-d', '2025-10-15']):
        with patch.object(Paper, '__call__', side_effect=PaperDownloadError('download failed')):
            with pytest.raises(SystemExit) as exc_info:
                main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert 'error: download failed' in captured.err
    assert 'Traceback' not in captured.err
