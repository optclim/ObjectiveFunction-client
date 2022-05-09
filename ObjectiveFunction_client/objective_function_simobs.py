__all__ = ['ObjectiveFunctionSimObs']

from typing import Mapping, Sequence
from pathlib import Path
import random
import pandas
import logging

from .parameter import Parameter
from .objective_function import ObjectiveFunction
from .common import RunType, LookupState


class ObjectiveFunctionSimObs(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the name of a file containing the residuals

    :param study: the name of the study
    :type study: str
    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    :param observationNames: a list of observation names
    :param scenario: name of the default scenario
    :type scenario: str
    :param db: database connection string
    :type db: str
    :param prelim: when True failed parameter look up raises a
                   PreliminaryRun exception otherwise a
                   NewRun exception is raised. Default=True
    :type prelim: bool
    """

    def __init__(self, appname: str, secret: str,
                 study: str, basedir: Path,  # noqa C901
                 parameters: Mapping[str, Parameter],
                 observationNames: Sequence[str],
                 scenario=None, prelim=True,
                 url_base='http://localhost:5000/api/'):
        """constructor"""

        self._obsNames = observationNames
        super().__init__(appname, secret, study, basedir,
                         parameters, scenario=scenario, prelim=prelim,
                         url_base=url_base, runtype=RunType.PATH)

    def _create_study(self, param_dict):
        super()._create_study(param_dict)

        # add observation names
        response = self._proxy.put(
            f'studies/{self.study}/observation_names',
            json={'obsnames': self.observationNames})
        if response.status_code == 404:
            raise RuntimeError(response.content)
        elif response.status_code != 201:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))

    def _load_study(self, param_dict, remote_param):
        super()._load_study(param_dict, remote_param)

        # check observation names
        response = self._proxy.get(f'studies/{self.study}/observation_names')
        if response.status_code != 200:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        obsnames = response.json()['obsnames']
        error = False
        if len(obsnames) != len(self.observationNames):
            self._log.error(
                'number of simulated observations in '
                f'{self.study} does not match')
            error = True
        else:
            for o in obsnames:
                if o not in self.observationNames:
                    self._log.error(
                        f'observation name {o} missing from configuration')
                    error = True
        if error:
            raise RuntimeError('configuration does not match database')

    @property
    def observationNames(self):
        return self._obsNames

    @property
    def num_residuals(self):
        """the number of residuals"""
        return len(self._obsNames)

    def setDefaultScenario(self, name):
        """set the default scenario

        :param name: name of scenario
        :type name: str
        """
        return super().setDefaultScenario(name, runtype=RunType.PATH)

    def _check_simobs(self, simobs):
        simobs = pandas.Series(simobs)
        error = False
        if len(simobs) != self.num_residuals:
            self._log.error("length of observations does not match")
            error = True
        for n in self.observationNames:
            if n not in simobs.index:
                self._log.error(f"observation {n} missing from simobs")
                error = True
        if error:
            raise RuntimeError("observation names do not match")
        return simobs

    def get_result(self, parameters, scenario=None):
        """look up parameters

        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        :raises NewRun: when lookup fails
        :raises Waiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: numpy.arraynd
        """

        run = super().get_result(parameters, scenario=scenario)
        if run['state'] != LookupState.COMPLETED:
            result = {}
            for n in self.observationNames:
                result[n] = random.random()
            result = pandas.Series(result)
        else:
            result = pandas.read_json(run['value'], typ='series')
            self._check_simobs(result)
        run['simobs'] = result
        return run

    def _set_data(self, scenario, run, result):
        result = self._check_simobs(result)
        fname = self.scenario_dir(scenario) / f'simobs_{run["id"]}.json'
        result.to_json(fname)
        return {'value': str(fname)}

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
        return super().__call__(x, grad=grad)['simobs']


if __name__ == '__main__':
    import sys
    from .parameter import ParameterFloat
    from .config import ObjFunConfig

    logging.basicConfig(level=logging.DEBUG)

    params = {'a': ParameterFloat(0, -1, 1),
              'b': ParameterFloat(1, 0, 2, 1e-7),
              'c': ParameterFloat(-2.5, -5, 0)}

    cfg = ObjFunConfig(Path(sys.argv[1]))

    objfun = ObjectiveFunctionSimObs(
        cfg.app, cfg.secret, "test_study", Path('/tmp'),
        params, ['simA', 'simB', 'simC'],
        scenario="test_scenario_simobs",
        url_base=cfg.baseurl)

    pset1 = {'a': 0, 'b': 1, 'c': -2}
    pset2 = {'a': 0.5, 'b': 1, 'c': -2}
    print(objfun.get_result(pset1))
    print('call', objfun(list(pset1.values())))
    print(objfun.get_new())
