# -*- coding:utf-8 -*-

import os
import io
import argparse
import warnings
import datetime

import re

import requests
from urllib.parse import urljoin

from PyPDF2 import PdfMerger
from typing import Iterator, List, Optional


class Paper:

    def __init__(self, date: datetime.date, verbose: bool = False):
        self.date = date
        self.verbose = verbose
        self._session = self._build_session(trust_env=True)
        self._fallback_session = (
            self._build_session(trust_env=False)
            if self._proxies_configured
            else None
        )

    def __call__(self, file_path):
        pages = self._load_pages()
        self._check_integrity(pages)
        merger = self._merge(pages)
        self._save(merger, file_path)

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

    def _merge(self, pages: List[bytes]) -> PdfMerger:

        merger = PdfMerger(strict=False)
        for page in pages:
            merger.append(io.BytesIO(page))
        return merger

    def _save(self, merger: PdfMerger, file_path: str):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with open(file_path, 'wb') as file:
                merger.write(file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--date',
        default=datetime.date.today().strftime('%Y-%m-%d'),
        help='the date, e.g., 2020-03-07'
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
    args = parser.parse_args()

    date = datetime.date.fromisoformat(args.date)

    if args.output == '':
        file_path = default_file_path(date)
    else:
        file_path = args.output
    paper = Paper(date, args.verbose)
    paper(file_path)


def default_file_path(date: datetime.date) -> str:
    return '人民日报_{}.pdf'.format(
        date.isoformat()
    )


if __name__ == '__main__':
    main()
