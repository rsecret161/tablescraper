import pandas as pd
import pytest

from tablescraper import fetcher


def test_fetch_tables_success(monkeypatch):
    calls = {}

    def fake_read_html(url):
        assert url == 'http://example.com'
        return [pd.DataFrame({'a': [1, 2]})]

    monkeypatch.setattr('pandas.read_html', fake_read_html)

    tables = fetcher.fetch_tables('http://example.com')
    assert isinstance(tables, list)
    assert len(tables) == 1
    assert list(tables[0].columns) == ['a']


def test_fetch_tables_error(monkeypatch):
    def bad_read_html(url):
        raise ValueError('boom')

    monkeypatch.setattr('pandas.read_html', bad_read_html)

    with pytest.raises(RuntimeError):
        fetcher.fetch_tables('http://example.com')
