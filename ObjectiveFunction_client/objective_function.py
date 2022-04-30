import logging
from typing import Mapping
from pathlib import Path
import numpy

from .proxy import Proxy
from .parameter import Parameter
from .common import RunType


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
    :param runtype: the type of the run
    :type runtype: RunType
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
                 scenario=None, runtype=RunType.MISFIT, prelim=True,
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

        param_dict = {}
        for p in parameters:
            param_dict[p] = parameters[p].to_dict

        response = self._proxy.get(f'studies/{study}/parameters')
        if response.status_code == 404:
            self._log.debug(f'creating study {study}')
            response = self._proxy.post('create_study',
                                        json={
                                            'name': self.study,
                                            'parameters': param_dict})
            if response.status_code != 201:
                raise RuntimeError(f'creating study {study}')
        elif response.status_code == 200:
            self._log.debug(f'loading study {study}')
            remote_param = response.json()
            error = False
            if self.num_params != len(remote_param):
                self._log.error(
                    f'number of parameters in {study} does not match')
                error = True
            else:
                for p in remote_param:
                    if p not in param_dict:
                        self._log.error(
                            f'parameter {p} missing from configuration')
                        error = True
                        continue
                    for k in remote_param[p]:
                        if k not in param_dict[p]:
                            self._log.error(
                                f'key {k} missing from configuration'
                                f' of parameter {p}')
                            error = True
                            continue
                        if param_dict[p][k] != remote_param[p][k]:
                            self._log.error(
                                f'key {k} of parameter {p} does not match')
                            error = True
                if error:
                    raise RuntimeError('configuration does not match database')

        self._lb = None
        self._ub = None

        self._scenario = None
        self._runtype = runtype
        if scenario is not None:
            self.setDefaultScenario(scenario, runtype)

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

    def getLowerBounds(self):
        """an array containing the lower bounds"""
        if self._lb is None:
            self._lb = []
            for p in self._active_paramlist:
                self._lb.append(self.parameters[p].minv)
            self._lb = numpy.array(self._lb)
        return self._lb

    def getUpperBounds(self):
        """an array containing the upper bounds"""
        if self._ub is None:
            self._ub = []
            for p in self._active_paramlist:
                self._ub.append(self.parameters[p].maxv)
            self._ub = numpy.array(self._ub)
        return self._ub

    @property
    def lower_bounds(self):
        """an array containing the lower bounds"""
        return self.getLowerBounds()

    @property
    def upper_bounds(self):
        """an array containing the upper bounds"""
        return self.getUpperBounds()

    def values2params(self, values):
        """create a dictionary of parameter values from list of values
        :param values: a list/tuple of values
        :return: a dictionary of parameters
        """
        params = {}
        if len(values) == len(self.parameters):
            for i, p in enumerate(self._paramlist):
                params[p] = values[i]
        elif len(values) == len(self.active_parameters):
            for i, p in enumerate(self._active_paramlist):
                params[p] = values[i]
            for p in self.constant_parameters:
                params[p] = self.constant_parameters[p].value
        else:
            raise RuntimeError('Wrong number of parameters')

        return params

    def params2values(self, params, include_constant=True):
        """create an array of values from a dictionary of parameters
        :param params: a dictionary of parameters
        :param include_constant: set to False to exclude constant parameters
        :return: a array of values
        """
        values = []
        for p in self._paramlist:
            if self.parameters[p].constant:
                if include_constant:
                    values.append(self.parameters[p].value)
            else:
                values.append(params[p])
        return numpy.array(values)

    def setDefaultScenario(self, name, runtype):
        """set the default scenario

        :param name: name of scenario
        :type name: str
        :param runtype: the type of the run
        """
        response = self._proxy.post(f'studies/{self.study}/create_scenario',
                                    json={'name': name,
                                          'runtype': runtype.name})
        if response.status_code == 201:
            self._log.debug(f'created scenario {name}')
        elif response.status_code == 409:
            self._log.debug(f'found scenario {name}')
        else:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        self._scenario = name
        self._runtype = runtype


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