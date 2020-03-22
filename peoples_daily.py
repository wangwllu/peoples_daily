# -*- coding:utf-8 -*-

import requests
import os
import glob
import argparse
import warnings
import datetime

from PyPDF2 import PdfFileMerger
from shutil import rmtree

from typing import Tuple


class Paper:

    base_url = 'http://paper.people.com.cn/rmrb/page/'

    def __init__(self, year: int, month: int, date: int):

        self.year = year
        self.month = month
        self.date = date

    def __call__(self):
        self._save_pages()
        self._merge_pages()
        self._clean_pages()

    def _save_pages(self) -> None:
        if not os.path.exists(self.page_dir):
            os.mkdir(self.page_dir)

        serial_nb = 1
        while True:
            # it is assumed that the page number is less than 100
            page_path = os.path.join(
                self.page_dir,
                '{:02d}.pdf'.format(serial_nb)
            )
            page_url = self._generate_url(serial_nb)

            response = requests.get(page_url)
            if response.ok:
                with open(page_path, 'wb') as file:
                    file.write(response.content)
                serial_nb += 1
            else:
                break

    def _generate_url(self, serial_nb: int) -> str:
        f_serial_nb = '{:02d}'.format(serial_nb)

        return (
            '{u}{y}-{m}/{d}/{s}/rmrb{y}{m}{d}{s}.pdf'.format(
                u=self.base_url,
                y=self._f_year, m=self._f_month, d=self._f_date,
                s=f_serial_nb
            )
        )

    def _merge_pages(self) -> None:
        pages = sorted(glob.glob(os.path.join(self.page_dir, '*.pdf')))
        if len(pages) == 0:
            warnings.warn(
                'Failed! Check if the date is legitimate'
                + ' and the network is available!'
            )

        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                merger = PdfFileMerger(strict=False)
                for page in pages:
                    merger.append(page)
                with open(self.file_name, 'wb') as file:
                    merger.write(file)

    def _clean_pages(self) -> None:
        if os.path.exists(self.page_dir):
            rmtree(self.page_dir)

    @property
    def _f_year(self) -> str:
        return '{:04d}'.format(self.year)

    @property
    def _f_month(self) -> str:
        return '{:02d}'.format(self.month)

    @property
    def _f_date(self) -> str:
        return '{:02d}'.format(self.date)

    @property
    def page_dir(self) -> str:
        return '人民日报-{}{}{}'.format(self._f_year, self._f_month, self._f_date)

    @property
    def file_name(self) -> str:
        return '人民日报-{}{}{}.pdf'.format(self._f_year, self._f_month, self._f_date)


def parse_date(formatted_date: str) -> Tuple[int, int, int]:
    year = int(formatted_date[:4])
    month = int(formatted_date[4:6])
    date = int(formatted_date[6:])
    return year, month, date


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--date',
        default=datetime.date.today().strftime('%Y%m%d'),
        help='the date, e.g., 20200307'
    )
    args = parser.parse_args()

    year, month, date = parse_date(args.date)
    paper = Paper(year, month, date)
    paper()


if __name__ == '__main__':
    main()
