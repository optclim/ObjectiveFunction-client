from ObjectiveFunction_client.proxy import Proxy


def test_proxy(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl)
    assert p._token == 'some_token'


def test_proxy_url(request_token, baseurl):
    p = Proxy('test', 'test_secret', url_base=baseurl)
    url = 'some/string'
    assert p.url(url) == baseurl + url
