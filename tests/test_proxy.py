import pytest

from ObjectiveFunction_client.proxy import Proxy


def test_proxy_fail(requests_mock, baseurl):
    requests_mock.register_uri(
        'GET', baseurl + 'token', status_code=400)
    with pytest.raises(RuntimeError):
        Proxy('test', 'test_secret', url_base=baseurl)


def test_proxy(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl)
    assert p._token == 'some_token'


def test_proxy_url(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl)
    url = 'some/string'
    assert p.url(url) == baseurl + url


def test_proxy_url_without(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl[:-1])
    url = 'some/string'
    assert p.url(url) == baseurl + url
