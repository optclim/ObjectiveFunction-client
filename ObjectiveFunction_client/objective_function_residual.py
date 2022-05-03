__all__ = ['ObjectiveFunctionResidual']

import numpy.random
import numpy
from typing import Mapping
from pathlib import Path
import logging

from .objective_function import ObjectiveFunction
from .parameter import Parameter
from .common import RunType, LookupState


class ObjectiveFunctionResidual(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the name of a file containing the residuals

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
    :param db: database connection string
    :type db: str
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

        super().__init__(appname, secret, study, basedir,
                         parameters, scenario=scenario, prelim=prelim,
                         url_base=url_base, runtype=RunType.PATH)

        self._num_residuals = None

    @property
    def num_residuals(self):
        """the number of residuals"""
        if self._num_residuals is None:
            return 50
        else:
            return self._num_residuals

    def setDefaultScenario(self, name):
        """set the default scenario

        :param name: name of scenario
        :type name: str
        """
        return super().setDefaultScenario(name, runtype=RunType.PATH)

    def get_result(self, parameters, scenario=None):
        """look up parameters
        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        :raises PreliminaryRun: when lookup fails
        :raises NewRun: when preliminary run has been called again
        :raises Waiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        """

        run = super().get_result(parameters, scenario=scenario)
        if run['state'] != LookupState.COMPLETED:
            run['residual'] = numpy.random.rand(self.num_residuals)
        else:
            with open(run['path'], 'rb') as f:
                run['residual'] = numpy.load(f)
            if self._num_residuals is None:
                self._num_residuals = run['residual'].size
        return run

    def _set_data(self, run, result):
        fname = self.basedir / f'residuals_{run["id"]}.npy'
        with open(fname, 'wb') as f:
            numpy.save(f, result)
        if self._num_residuals is None:
            self._num_residuals = result.size
        return {'path': str(fname)}

    def __call__(self, x, grad=None):
        """look up parameters
        :param x: vector containing parameter values
        :param grad: vector of length 0
        :type grad: numpy.ndarray
        :raises NewRun: when lookup fails
        :raises Waiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: float
        """
        return super().__call__(x, grad=grad)['residual']


if __name__ == '__main__':
    import sys
    from .parameter import ParameterFloat
    from .config import ObjFunConfig

    logging.basicConfig(level=logging.DEBUG)

    params = {'a': ParameterFloat(0, -1, 1),
              'b': ParameterFloat(1, 0, 2, 1e-7),
              'c': ParameterFloat(-2.5, -5, 0)}

    cfg = ObjFunConfig(Path(sys.argv[1]))

    objfun = ObjectiveFunctionResidual(
        cfg.app, cfg.secret, "test_study", Path('/tmp'),
        params, scenario="test_scenario_residual",
        url_base=cfg.baseurl)

    pset1 = {'a': 0, 'b': 1, 'c': -2}
    pset2 = {'a': 0.5, 'b': 1, 'c': -2}
    print(objfun.get_result(pset1))
    print('call', objfun(list(pset1.values())))
    print(objfun.get_new())
    objfun.set_result(pset1, numpy.arange(10))
    print(objfun.get_result(pset1))
    #print(objfun.get_result(pset2))
