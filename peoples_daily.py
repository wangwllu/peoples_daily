# -*- coding:utf-8 -*-

import os
import argparse
import io
import re
import warnings
import datetime
import subprocess
import tempfile
import shutil
import contextlib

import requests
from urllib.parse import urljoin

import logging

from pypdf import PdfReader, PdfWriter
from pypdf import _utils as pypdf_utils
from pypdf.generic import _data_structures as pypdf_data_structures
from pypdf.errors import PdfReadWarning
from typing import Iterator, List, Optional


class Paper:

    def __init__(self, date: datetime.date, verbose: bool = False, compress: bool = False):
        self.date = date
        self.verbose = verbose
        self.compress = compress
        self._session = self._build_session(trust_env=True)
        self._fallback_session = (
            self._build_session(trust_env=False)
            if self._proxies_configured
            else None
        )

    def __call__(self, file_path):
        pages = self._load_pages()
        self._check_integrity(pages)
        writer = self._merge(pages)
        self._save(writer, file_path)

    def _load_pages(self) -> List[bytes]:

        serial_nb = 1
        pages: List[bytes] = []
        while True:
            fetched = self._fetch_page(serial_nb)
            if fetched is None:
                break
            pages.append(fetched)
            serial_nb += 1

        return pages

    def _fetch_page(self, serial_nb: int) -> Optional[bytes]:
        pdf_url = self._resolve_pdf_url(serial_nb)
        if pdf_url is None:
            return None

        if self.verbose:
            print('Querying {}'.format(pdf_url))

        for session in self._iter_sessions():
            try:
                response = session.get(pdf_url, timeout=10)
            except requests.RequestException:
                continue

            if response.ok:
                return response.content

        return None

    def _iter_sessions(self) -> Iterator[requests.Session]:
        yield self._session
        if self._fallback_session is not None:
            yield self._fallback_session

    def _build_session(self, *, trust_env: bool) -> requests.Session:
        session = requests.Session()
        session.trust_env = trust_env
        session.headers.update(self._default_headers)
        return session

    @property
    def _proxies_configured(self) -> bool:
        for key in ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY'):
            if os.environ.get(key):
                return True
        return False

    @property
    def _default_headers(self) -> dict[str, str]:
        return {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0 Safari/537.36'
            ),
            'Accept': 'application/pdf,application/octet-stream;q=0.9,*/*;q=0.8',
        }

    def _resolve_pdf_url(self, serial_nb: int) -> Optional[str]:
        for layout_url in self._layout_urls(serial_nb):
            for session in self._iter_sessions():
                try:
                    response = session.get(layout_url, timeout=10)
                except requests.RequestException:
                    continue

                if not response.ok:
                    continue

                pdf_href = self._extract_pdf_href(response.text)
                if not pdf_href:
                    continue

                return urljoin(layout_url, pdf_href)

        return None

    def _layout_urls(self, serial_nb: int):
        for base in self._layout_base_urls:
            yield (
                f'{base}{self.date:%Y%m}/{self.date:%d}/'
                f'node_{serial_nb:02d}.html'
            )

    @staticmethod
    def _extract_pdf_href(html: str) -> Optional[str]:
        match = re.search(r'href=[\"\']([^"\']+\.pdf)[\"\']', html, re.IGNORECASE)
        if not match:
            return None

        return match.group(1)

    @property
    def _layout_base_urls(self) -> List[str]:
        override = os.environ.get('PEOPLES_DAILY_BASE_URLS')
        if override:
            return [
                base.strip()
                for base in override.split(',')
                if base.strip()
            ]

        return [
            'https://paper.people.com.cn/rmrb/pc/layout/',
        ]

    def _check_integrity(self, pages: List[bytes]) -> None:
        if len(pages) == 0:
            raise Exception(
                'Failed! Check if the paper of the date'
                + ' and the network are available!'
            )

    def _merge(self, pages: List[bytes]) -> PdfWriter:

        writer = PdfWriter()
        loggers = [
            logging.getLogger('pypdf'),
            logging.getLogger('pypdf.generic'),
            logging.getLogger('pypdf.generic._data_structures'),
        ]
        original_levels = [logger.level for logger in loggers]

        if self.verbose:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", category=PdfReadWarning)
                for page_bytes in pages:
                    reader = PdfReader(io.BytesIO(page_bytes), strict=False)
                    for page in reader.pages:
                        writer.add_page(page)

            for warning in caught or []:
                if isinstance(warning.message, PdfReadWarning):
                    print(f'Warning merging PDF page: {warning.message}')
        else:
            with self._suppress_pypdf_noise(loggers, original_levels):
                for page_bytes in pages:
                    reader = PdfReader(io.BytesIO(page_bytes), strict=False)
                    for page in reader.pages:
                        writer.add_page(page)
        return writer

    def _save(self, writer: PdfWriter, file_path: str):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            buffer = io.BytesIO()
            if self.verbose:
                writer.write(buffer)
            else:
                with self._suppress_pypdf_noise():
                    writer.write(buffer)

        writer.close()
        pdf_bytes = buffer.getvalue()

        if self.compress:
            pdf_bytes = self._compress(pdf_bytes)

        with open(file_path, 'wb') as file:
            file.write(pdf_bytes)

    def _compress(self, pdf_bytes: bytes) -> bytes:
        compressed = self._compress_with_ghostscript(pdf_bytes)
        if compressed is not None:
            return compressed
        return pdf_bytes

    @contextlib.contextmanager
    def _suppress_pypdf_noise(
        self,
        loggers: Optional[List[logging.Logger]] = None,
        original_levels: Optional[List[int]] = None,
    ):
        if loggers is None:
            loggers = [
                logging.getLogger('pypdf'),
                logging.getLogger('pypdf.generic'),
                logging.getLogger('pypdf.generic._data_structures'),
            ]
        if original_levels is None:
            original_levels = [logger.level for logger in loggers]

        original_logger_warning_utils = pypdf_utils.logger_warning
        original_logger_warning_structures = pypdf_data_structures.logger_warning
        previous_disable_level = logging.root.manager.disable

        try:
            pypdf_utils.logger_warning = lambda msg, src: None  # type: ignore[assignment]
            pypdf_data_structures.logger_warning = lambda msg, src: None  # type: ignore[assignment]
            for logger in loggers:
                logger.setLevel(logging.ERROR)
            logging.disable(logging.CRITICAL)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=PdfReadWarning)
                    yield
        finally:
            logging.disable(previous_disable_level)
            pypdf_utils.logger_warning = original_logger_warning_utils
            pypdf_data_structures.logger_warning = original_logger_warning_structures
            for logger, level in zip(loggers, original_levels):
                logger.setLevel(level)

    def _compress_with_ghostscript(self, pdf_bytes: bytes) -> Optional[bytes]:
        executable = (
            shutil.which('gs')
            or shutil.which('gswin64c')
            or shutil.which('gswin32c')
        )
        if executable is None:
            return None

        input_fd, input_path = tempfile.mkstemp(suffix='.pdf')
        output_fd, output_path = tempfile.mkstemp(suffix='.pdf')
        os.close(input_fd)
        os.close(output_fd)

        try:
            with open(input_path, 'wb') as input_file:
                input_file.write(pdf_bytes)

            command = [
                executable,
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/ebook',
                '-dDetectDuplicateImages=true',
                '-dDownsampleColorImages=true',
                '-dColorImageResolution=120',
                '-dReduceImageResolution=true',
                '-dCompressFonts=true',
                '-dSubsetFonts=true',
                '-dAutoRotatePages=/None',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-sOutputFile={output_path}',
                input_path,
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0:
                return None

            if not os.path.exists(output_path):
                return None

            with open(output_path, 'rb') as output_file:
                optimized = output_file.read()
        finally:
            for path in (input_path, output_path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        if optimized and len(optimized) < len(pdf_bytes):
            return optimized
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--date',
        default=datetime.date.today().strftime('%Y-%m-%d'),
        help='the date, e.g., 2025-10-15'
    )
    parser.add_argument(
        '-o', '--output',
        default='',
        help='the path to output the paper file, e.g., ./paper.pdf'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='whether print intermediate info'
    )
    parser.add_argument(
        '--compress',
        action='store_true',
        help='enable Ghostscript compression (disabled by default)'
    )
    args = parser.parse_args()

    date = datetime.date.fromisoformat(args.date)

    if args.output == '':
        file_path = default_file_path(date)
    else:
        file_path = args.output
    paper = Paper(date, args.verbose, args.compress)
    paper(file_path)


def default_file_path(date: datetime.date) -> str:
    return '人民日报_{}.pdf'.format(
        date.isoformat()
    )


if __name__ == '__main__':
    main()
