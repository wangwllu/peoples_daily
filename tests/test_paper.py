import os
import datetime
import tempfile
from peoples_daily import Paper


def test_paper_call():
    with tempfile.TemporaryDirectory() as tmpfile:
        file_path = os.path.join(tmpfile, 'paper.pdf')
        paper = Paper(datetime.date.fromisoformat('2019-06-27'))
        paper(file_path)
        assert os.path.exists(file_path)
