# -*- coding:utf-8 -*-

import requests
import io
import argparse
import warnings
import datetime

from PyPDF2 import PdfFileMerger
from typing import List


class Paper:

    _base_url = 'http://paper.people.com.cn/rmrb/page/'

    def __init__(self, date: datetime.date):
        self.date = date

    def __call__(self, file_path):
        pages = self._load_pages()
        self._check_integrity(pages)
        merger = self._merge(pages)
        self._save(merger, file_path)

    def _load_pages(self) -> List[bytes]:

        serial_nb = 1
        pages = []
        while True:
            page_url = self._generate_url(serial_nb)

            response = requests.get(page_url)
            if response.ok:
                pages.append(response.content)
                serial_nb += 1
            else:
                break
        return pages

    def _generate_url(self, serial_nb: int) -> str:

        url_format = (
            '{b}{y:04d}-{m:02d}/{d:02d}/'
            + '{s:02d}/rmrb{y:04d}{m:02d}{d:02d}{s:02d}.pdf'
        )

        return (
            url_format.format(
                b=self._base_url,
                y=self.date.year, m=self.date.month, d=self.date.day,
                s=serial_nb
            )
        )

    def _check_integrity(self, pages: List[bytes]) -> None:
        if len(pages) == 0:
            raise Exception(
                'Failed! Check if the paper of the date'
                + ' and the network are available!'
            )

    def _merge(self, pages: List[bytes]) -> PdfFileMerger:

        merger = PdfFileMerger(strict=False)
        for page in pages:
            merger.append(io.BytesIO(page))
        return merger

    def _save(self, merger: PdfFileMerger, file_path: str):
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
    args = parser.parse_args()

    date = datetime.date.fromisoformat(args.date)

    if args.output == '':
        file_path = default_file_path(date)
    paper = Paper(date)
    paper(file_path)


def default_file_path(date: datetime.date) -> str:
    return '人民日报_{}.pdf'.format(
        date.isoformat()
    )


if __name__ == '__main__':
    main()
