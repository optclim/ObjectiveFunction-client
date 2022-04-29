import logging
from typing import Mapping
from pathlib import Path

from .proxy import Proxy
from .parameter import Parameter


class ObjectiveFunction:
    """class maintaining a lookup table for an objective function

    :param appname: appname for connecting to objfun server
    :type appname: str
    :param secret: password for connecting to objfun server
    :type secret: str
    :param study: the name of the study
    :type study: str
    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    :param scenario: name of the default scenario
    :type scenario: str
    :param prelim: when True failed parameter look up raises a
                   PreliminaryRun exception otherwise a
                   NewRun exception is raised. Default=True
    :type prelim: bool
    :param url_base: base URL for ObjectiveFunction server API,
                     defaults to 'http://localhost:5000/api/'
    """

    def __init__(self, appname: str, secret: str,
                 study: str, basedir: Path,  # noqa C901
                 parameters: Mapping[str, Parameter],
                 scenario=None, prelim=True,
                 url_base='http://localhost:5000/api/'):
        """constructor"""

        self._proxy = Proxy(appname, secret, url_base=url_base)

        if len(parameters) == 0:
            raise RuntimeError('no parameters given')

        self._parameters = parameters
        self._constant_parameters = {}
        self._active_parameters = {}
        for p in self.parameters:
            if self.parameters[p].constant:
                self._constant_parameters[p] = self.parameters[p]
            else:
                self._active_parameters[p] = self.parameters[p]
        self._paramlist = tuple(
            sorted(list(self.parameters.keys())))
        self._active_paramlist = tuple(
            sorted(list(self.active_parameters.keys())))
        self._log = logging.getLogger(
            f'ObjectiveFunction.{self.__class__.__name__}')
        self._basedir = basedir
        self._prelim = prelim
        self._study = study

        response = self._proxy.get('studies/' + study)
        if response.status_code == 404:
            response = self._proxy.post('create_study',
                                        json={'name': self.study})
            if response.status_code != 201:
                raise RuntimeError(f'creating study {study}')

    @property
    def basedir(self):
        """the basedirectory"""
        return self._basedir

    @property
    def study(self):
        return self._study

    @property
    def prelim(self):
        return self._prelim

    @property
    def num_params(self):
        """the number of parameters"""
        return len(self._parameters)

    @property
    def num_active_params(self):
        """the number of parameters"""
        return len(self._active_parameters)

    @property
    def parameters(self):
        """dictionary of parameters"""
        return self._parameters

    @property
    def active_parameters(self):
        """the constant parameters"""
        return self._active_parameters

    @property
    def constant_parameters(self):
        """the constant parameters"""
        return self._constant_parameters


if __name__ == '__main__':
    import sys
    from .parameter import ParameterFloat
    from .config import ObjFunConfig

    logging.basicConfig(level=logging.DEBUG)

    params = {'a': ParameterFloat(0, -1, 1),
              'b': ParameterFloat(1, 0, 2, 1e-7),
              'c': ParameterFloat(-2.5, -5, 0)}

    cfg = ObjFunConfig(Path(sys.argv[1]))

    objfun = ObjectiveFunction(cfg.app, cfg.secret,
                               "test_study", Path('/tmp'),
                               params, scenario="test_scenario",
                               url_base=cfg.baseurl)
