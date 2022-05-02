import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.auth import HTTPBasicAuth


class Proxy:
    """proxy class for calling ObjectiveFunction server API

    :param appname: appname for connecting to objfun server
    :type appname: str
    :param secret: password for connecting to objfun server
    :type secret: str
    :param url_base: base URL for ObjectiveFunction server API,
                     defaults to 'http://localhost:5000/api/'
    """

    def __init__(self, appname, secret,
                 url_base='http://localhost:5000/api/'):
        """constructor"""
        self._url_base = url_base
        if self._url_base[-1] != '/':
            self._url_base += '/'
        self._tauth = None
        self._session = requests.Session()

        # setup session
        # from: https://www.peterbe.com/plog/best-practice-with-retries-with-requests  # noqa E501
        retries = 10
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 503, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount(url_base, adapter)

        # get a token
        response = self.session.get(
            self.url('token'), auth=HTTPBasicAuth(appname, secret))

        if response.status_code != 200:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        self._token = response.json()['token']

    def url(self, url):
        """construct URL to call
        :param url: url end point
        :type url: str
        :returns: full URL
        :rtype: str
        construct full URL by appending url to url_base
        """
        return '{0}{1}'.format(self._url_base, url)

    @property
    def session(self):
        """the request session"""
        return self._session

    @property
    def token_auth(self):
        """the auth token"""
        if self._tauth is None:
            self._tauth = HTTPBasicAuth(self._token, '')
        return self._tauth

    def get(self, url, **kwds):
        response = self.session.get(
            self.url(url), **kwds, auth=self.token_auth)
        return response

    def post(self, url, **kwds):
        response = self.session.post(
            self.url(url), **kwds, auth=self.token_auth)
        return response

    def put(self, url, **kwds):
        response = self.session.put(
            self.url(url), **kwds, auth=self.token_auth)
        return response

    def delete(self, url, **kwds):
        response = self.session.delete(
            self.url(url), **kwds, auth=self.token_auth)
        return response
