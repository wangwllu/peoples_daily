# -*- coding:utf-8 -*-

import requests
import os
import glob
import argparse
import warnings
from PyPDF2 import PdfFileMerger
from datetime import date
from shutil import rmtree


class Paper:

    base_url = 'http://paper.people.com.cn/rmrb/page/'

    def __init__(self, year, month, date):
        self.year = f'{year:04d}'
        self.month = f'{month:02d}'
        self.date = f'{date:02d}'
        self.page_dir = f'__{self.year}{self.month}{self.date}'
        self.paper_name = f'人民日报-{self.year}{self.month}{self.date}.pdf'

        if not os.path.exists(self.page_dir):
            os.mkdir(self.page_dir)

    def merge_pages(self):
        pages = sorted(glob.glob(os.path.join(self.page_dir, '*.pdf')))
        if len(pages) == 0:
            warnings.warn('Failed! Check if the date is legitimate!')

        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                merger = PdfFileMerger(strict=False)
                for page in pages:
                    merger.append(page)
                with open(self.paper_name, 'wb') as file:
                    merger.write(file)

    def save_pages(self):
        page_nb = 0
        while self.save_page(page_nb + 1):
            page_nb += 1
        return page_nb

    def clean_pages(self):
        if os.path.exists(self.page_dir):
            rmtree(self.page_dir)

    def save_page(self, page_nb):
        page_path = os.path.join(self.page_dir, f'{page_nb:02d}.pdf')
        page_url = self.generate_url(page_nb)
        response = requests.get(page_url)
        if response.ok:
            with open(page_path, 'wb') as file:
                file.write(response.content)
        return response.ok

    def generate_url(self, page_nb):
        return (
            f'{self.base_url}{self.year}-{self.month}/{self.date}/'
            + f'{page_nb:02d}/rmrb{self.year}{self.month}{self.date}'
            + f'{page_nb:02d}.pdf'
        )


def parse_date(date):
    year = int(date[:4])
    month = int(date[4:6])
    date = int(date[6:])
    return year, month, date


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--date', default=date.today().strftime('%Y%m%d'),
        help='the date, e.g., 20200307'
    )
    args = parser.parse_args()

    year, month, date = parse_date(args.date)

    paper = Paper(year, month, date)
    paper.save_pages()
    paper.merge_pages()
    paper.clean_pages()
