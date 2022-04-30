import argparse
from pathlib import Path

from .config import ObjFunConfig
from .proxy import Proxy


def studies(proxy):
    """get a list of runs
    """

    response = proxy.get('studies')
    if response.status_code != 200:
        raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
            response.status_code, response.content))
    return response.json()['data']


def scenarios(proxy, study):

    response = proxy.get(f'studies/{study}/scenarios')
    if response.status_code != 200:
        raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
            response.status_code, response.content))
    return response.json()['data']


def runs(proxy, study, scenario):

    response = proxy.get(f'studies/{study}/scenarios/{scenario}/runs')
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
    parser.add_argument('-c', '--config', type=Path,
                        help="config file to read")
    parser.add_argument('-s', '--study',
                        help="get all scenarios for a particular study")
    parser.add_argument('-S', '--scenario',
                        help="get all runs for a particular scenario")
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

    proxy = Proxy(app, password, url_base=baseurl)

    if args.study is not None:
        if args.scenario:
            for r in runs(proxy, args.study, args. scenario):
                print(r)
        else:
            for s in scenarios(proxy, args.study):
                print(s)
    else:
        for s in studies(proxy):
            print(s)


if __name__ == '__main__':
    main()
