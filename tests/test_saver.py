import pandas as pd
import os

from tablescraper import saver


def test_save_to_csv(tmp_path):
    df = pd.DataFrame({'a': [1, 2], 'b': ['x', 'y']})
    p = tmp_path / 'out.csv'
    saver.save_to_file(df, str(p))
    assert p.exists()
    read = pd.read_csv(str(p))
    assert list(read.columns) == ['a', 'b']


def test_save_to_json(tmp_path):
    df = pd.DataFrame({'a': [1, 2]})
    p = tmp_path / 'out.json'
    saver.save_to_file(df, str(p))
    assert p.exists()


def test_save_to_excel(tmp_path):
    df = pd.DataFrame({'a': [1, 2]})
    p = tmp_path / 'out.xlsx'
    saver.save_to_file(df, str(p))
    assert p.exists()
    # read back
    read = pd.read_excel(str(p), engine='openpyxl')
    assert list(read.columns) == ['a']
