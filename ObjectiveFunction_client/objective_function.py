import logging
from typing import Mapping
from pathlib import Path
import numpy

from .proxy import Proxy
from .parameter import Parameter
from .common import RunType, LookupState
from .common import PreliminaryRun, NewRun, Waiting, NoNewRun
from .cache import ObjFunCache


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

    RESULT_TYPE = "real"

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
            self._create_study(param_dict)
        elif response.status_code == 200:
            remote_param = response.json()
            self._load_study(param_dict, remote_param)
        else:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))

        self._cache = {}

        self._lb = None
        self._ub = None

        self._scenario = None
        self._runtype = runtype
        if scenario is not None:
            self.setDefaultScenario(scenario)

    def _create_study(self, param_dict):
        self._log.debug(f'creating study {self.study}')
        response = self._proxy.post('create_study',
                                    json={
                                        'name': self.study,
                                        'parameters': param_dict})
        if response.status_code != 201:
            raise RuntimeError(f'creating study {self.study}')

    def _load_study(self, param_dict, remote_param):
        self._log.debug(f'loading study {self.study}')
        error = False
        if self.num_params != len(remote_param):
            self._log.error(
                f'number of parameters in {self.study} does not match')
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

    @property
    def basedir(self):
        """the basedirectory"""
        return self._basedir

    def scenario_name(self, scenario=None):
        """return scenario name"""
        if scenario is None:
            scenario = self._scenario
        if scenario is None:
            raise RuntimeError('no scenario selected')
        name = ''
        for c in scenario:
            if c.isalnum():
                name += c
            else:
                name += '_'
        return name

    def scenario_dir(self, scenario=None):
        sdir = self.basedir / self.scenario_name(scenario)
        if not sdir.exists():
            sdir.mkdir()
        return sdir

    def cache(self, scenario=None):
        name = self.scenario_name(scenario)
        if name not in self._cache:
            self._cache[name] = ObjFunCache(
                self.scenario_dir(scenario) / 'cache.sqlite',
                self.parameters.keys(), self.RESULT_TYPE)
        return self._cache[name]

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

    def setDefaultScenario(self, name, runtype=None):
        """set the default scenario

        :param name: name of scenario
        :type name: str
        :param runtype: the type of the run
        """
        if runtype is None:
            runtype = self._runtype

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

    def get_run_by_id(self, runid, scenario=None):
        """get a run with a particular ID

        :param runid: the run ID
        :param scenario: the name of the scenario
        """
        if scenario is None:
            scenario = self._scenario

        response = self._proxy.get(
            f'studies/{self.study}/scenarios/{scenario}/runs/{runid}')
        if response.status_code != 200:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        return response.json()

    def getState(self, runid, scenario=None):
        """get state of a particular run

        :param runid: the run ID
        :param scenario: the name of the scenario
        """
        if scenario is None:
            scenario = self._scenario
        response = self._proxy.get(
            f'studies/{self.study}/scenarios/{scenario}/runs/{runid}/state')
        if response.status_code == 404:
            raise LookupError(f'no run with ID {runid}')
        elif response.status_code != 200:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        result = response.json()['state']
        return LookupState.__members__[result]

    def setState(self, runid, state, scenario=None):
        """set the state of run
        :param runid: ID of run
        :param state: the new state
        :param scenario: the name of the scenario
        """
        if scenario is None:
            scenario = self._scenario
        response = self._proxy.put(
            f'studies/{self.study}/scenarios/{scenario}/runs/{runid}/state',
            json={'state': state.name})
        if response.status_code == 404:
            raise LookupError(f'no run with ID {runid}')
        elif response.status_code != 201:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))

    def _transform_parameters(self, parameters):
        """transform parameters to integers

        :param parmeters: dictionary containing parameter values
        """
        transformed_params = {}
        for p in self.parameters:
            if self.parameters[p].constant:
                v = self.parameters[p].value
            else:
                v = parameters[p]
            transformed_params[p] = self.parameters[p].transform(v)
        return transformed_params

    def _inv_transform_parameters(self, parameters):
        """transform parameters from integers

        :param parmeters: dictionary containing parameter values
        """
        transformed_params = {}
        for p in parameters:
            transformed_params[p] = self.parameters[p].inv_transform(
                parameters[p])
        return transformed_params

    def get_with_state(self, state, scenario=None, with_id=False,
                       new_state=None):
        """get a set of parameters in a particular state
        :param state: find run in state
        :param scenario: the name of the scenario
        :param with_id: when set to True also return run ID
        :param new_state: when not None set the state of the run to new_state
        Get a set of parameters for a run in a particular state. Optionally
        the run transitions to new_state.
        :return: dictionary of parameter values for which to compute the model
        :raises LookupError: if there is no parameter set in specified state
        """
        if scenario is None:
            scenario = self._scenario
        data = {'state': state.name}
        if new_state is not None:
            data['new_state'] = new_state.name
        response = self._proxy.post(
            f'studies/{self.study}/scenarios/{scenario}/runs/with_state',
            json=data)
        if response.status_code == 404:
            raise LookupError(f'no parameter set in state {state.name}')
        elif response.status_code != 201:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        results = response.json()
        values = self._inv_transform_parameters(results['values'])
        if with_id:
            return results['id'], values
        else:
            return values

    def get_new(self, scenario=None, with_id=False):
        """get a set of parameters that are not yet processed
        :param scenario: the name of the scenario
        :param with_id: when set to True also return run ID
        The parameter set changes set from new to active
        :return: dictionary of parameter values for which to compute the model
        :raises NoNewRun: if there is no new parameter set
        """
        res = None
        try:
            res = self.get_with_state(LookupState.NEW, scenario=scenario,
                                      with_id=with_id,
                                      new_state=LookupState.ACTIVE)
        except LookupError:
            pass
        if res is None:
            raise NoNewRun('no new parameter sets')

        return res

    def get_run(self, parameters, scenario=None):
        """get a run with a particular parameter set

        :param parmeters: dictionary containing parameter values
        :param scenario: the name of the scenario
        """
        if scenario is None:
            scenario = self._scenario

        transformed_params = self._transform_parameters(parameters)

        try:
            run = self.cache(scenario)[transformed_params]
            return run
        except LookupError:
            pass

        response = self._proxy.post(
            f'studies/{self.study}/scenarios/{scenario}/get_run',
            json={'parameters': transformed_params})
        if response.status_code != 201:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        run = response.json()
        run['state'] = LookupState.__members__[run['state']]
        if run['state'] == LookupState.COMPLETED:
            self.cache(scenario)[transformed_params] = run
        return run

    def lookup_run(self, parameters, scenario=None):
        """look up parameters

        :param parmeters: dictionary containing parameter values
        :param scenario: the name of the scenario
        """

        if scenario is None:
            scenario = self._scenario

        transformed_params = self._transform_parameters(parameters)

        try:
            run = self.cache(scenario)[transformed_params]
            return run
        except LookupError:
            pass

        response = self._proxy.post(
            f'studies/{self.study}/scenarios/{scenario}/lookup_run',
            json={'parameters': transformed_params})
        if response.status_code != 201:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))
        run = response.json()
        if 'state' in run:
            run['state'] = LookupState.__members__[run['state']]
            if run['state'] == LookupState.COMPLETED:
                self.cache(scenario)[transformed_params] = run
        return run

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

        run = self.lookup_run(parameters, scenario=scenario)

        if 'status' in run:
            if run['status'] == 'waiting':
                raise Waiting
            elif run['status'] == 'provisional':
                raise PreliminaryRun
            elif run['status'] == 'new':
                raise NewRun
            else:
                raise RuntimeError(f'unknown status {run["status"]}')

        return run

    def _set_data(self, scenario, run, result):
        raise NotImplementedError  # pragma: no cover

    def set_result(self, parameters, result, scenario=None, force=False):
        """set the result for a paricular parameter set
        :param parameters: dictionary of parameters
        :param result: result value to set
        :param scenario: the name of the scenario
        :param force: force setting results irrespective of state
        """
        if scenario is None:
            scenario = self._scenario
        run = self.get_run(parameters, scenario=scenario)

        state = run['state']
        if (state.value > LookupState.CONFIGURED.value
            and state != LookupState.COMPLETED) or force:  # noqa W503
            pass
        else:
            raise RuntimeError(
                f'parameter set is in wrong state {state}')

        data = self._set_data(scenario, run, result)
        data['force'] = force
        response = self._proxy.put(
            f'studies/{self.study}/scenarios/{scenario}/runs/'
            f'{run["id"]}/value',
            json=data)
        if response.status_code == 403:
            raise RuntimeError(response.content)
        elif response.status_code != 201:
            raise RuntimeError('[HTTP {0}]: Content: {1}'.format(
                response.status_code, response.content))

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
        if grad is not None and grad.size > 0:
            raise RuntimeError(
                'ObjectiveFunction only supports derivative '
                'free optimisations')
        return self.get_result(self.values2params(x))


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

    pset1 = {'a': 0, 'b': 1, 'c': -2}
    pset2 = {'a': 0.5, 'b': 1, 'c': -2}
    pset3 = {'a': 0.5, 'b': 1.5, 'c': -2}
    #print(objfun.get_result(pset1))
    print(objfun.get_result(pset2))
    print('get_run', objfun.get_run(pset2))
    #print('get_run_id', objfun.get_run_by_id(1))
    print('call', objfun(list(pset2.values())))
    print('get_state', objfun.getState(1))
    print('get_with_state', objfun.get_with_state(LookupState.NEW))
    print('get_with_state', objfun.get_with_state(LookupState.NEW,
                                                  with_id=True))
    print('get_new', objfun.get_new())
    #objfun.setState(1, LookupState.COMPLETED)
    #print('get_state', objfun.getState(1))
    #print(objfun.get_run(pset3))
