import argparse
from pathlib import Path

from .config import ObjFunConfig
from .proxy import Proxy


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

    proxy = Proxy(appname, password, url_base=url_base)
    response = proxy.get('studies')
    return response.json()['data']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--baseurl',
                        default="http://localhost:5000/api/", help='API url')
    parser.add_argument('-a', '--app',
                        help="the ObjectiveFunction app")
    parser.add_argument('-p', '--password',
                        help="the password for the app")
    parser.add_argument('-c', '--config', type=Path,
                        help="config file to read")
    args = parser.parse_args()

    app = None
    password = None
    baseurl = None
    if args.config is not None:
        cfg = ObjFunConfig(args.config)
        app = cfg.app
        password = cfg.secret
        baseurl = cfg.baseurl
    if args.app is not None:
        app = args.app
    if args.password is not None:
        password = args.password
    if args.baseurl is not None:
        baseurl = args.baseurl

    for s in studies(app, password, baseurl):
        print(s)


if __name__ == '__main__':
    main()
