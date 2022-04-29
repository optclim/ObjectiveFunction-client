import argparse
import requests
from requests.auth import HTTPBasicAuth


def studies(appname, password, url_base='http://localhost:5000/api/'):
    """get a list of runs
    :param appname: appname for connecting to taskfarm server
    :type appname: str
    :param password: password for connecting to taskfarm server
    :type password: str
    :param url_base: base URL for taskfarm server API,
                     defaults to 'http://localhost:5000/api/'
    :type url_base: str
    :return: list of runs
    :rtype: dict
    """

    auth = HTTPBasicAuth(appname, password)
    response = requests.get(url_base + 'studies', auth=auth)
    if response.status_code != 200:
        raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
            response.status_code, response.content))
    return response.json()['data']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--baseurl',
                        default="http://localhost:5000/api/", help='API url')
    parser.add_argument('-a', '--app',
                        help="the ObjectiveFunction app")
    parser.add_argument('-p', '--password',
                        help="the password for the app")
    args = parser.parse_args()

    for s in studies(args.app, args.password, args.baseurl):
        print(s)


if __name__ == '__main__':
    main()
