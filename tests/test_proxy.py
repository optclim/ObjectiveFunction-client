import pytest

from ObjectiveFunction_client.proxy import Proxy


@pytest.fixture
def request_token(requests_mock, baseurl):
    requests_mock.register_uri(
        'GET', baseurl + 'token', json={'token': 'some_token'})


def test_proxy(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl)
    assert p._token == 'some_token'


def test_proxy_url(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl)
    url = 'some/string'
    assert p.url(url) == baseurl + url
