__all__ = ['ObjFunConfig']

import logging
from configobj import ConfigObj, flatten_errors
from validate import Validator
from pathlib import Path
from os.path import expandvars
from io import StringIO
from functools import partial
import pandas

from .objective_function_misfit import ObjectiveFunctionMisfit
from .objective_function_residual import ObjectiveFunctionResidual
from .objective_function_simobs import ObjectiveFunctionSimObs
from .parameter import ParameterFloat, ParameterInt


class ObjFunConfig:
    """handle ObjectiveFunction configuration

    :param fname: the name of the configuration file
    :type fname: Path
    :param app: the application name
    :type app: str
    :param baseurl: base URL for ObjectiveFunction server API
    :type baseurl: str
    :param secret: the secret associated with the app name
    :type secret: str

    The keyword arguments app, baseurl and secret override the values that
    may be in the configuration file
    """

    setupCfgStr = """
    [setup]
      app = string() # the name of ObjectiveFunction app
      # the URL of the ObjectiveFunction server
      baseurl = string(default=http://localhost:5000/api/)
      study = string() # the name of the study
      scenario = string() # the name of the scenario
      basedir = string() # the base directory
      objfun = string(default=misfit)
    """

    parametersCfgStr = """
    [parameters]
      [[float_parameters]]
        [[[__many__]]]
          value = float() # the default value
          min = float() # the minimum value allowed
          max = float() # the maximum value allowed
          resolution = float(default=1e-6) # the resolution of the parameter
          constant = boolean(default=False) # if set to True the parameter is
                                             # not optimised for
      [[integer_parameters]]
        [[[__many__]]]
          value = integer() # the default value
          min = integer() # the minimum value allowed
          max = integer() # the maximum value allowed
          constant = boolean(default=False) # if set to True the parameter is
                                            # not optimised for
    """

    targetsCfgStr = """
    [targets]
      __many__ = float
    """

    def __init__(self,
                 fname: Path = None,
                 app: str = None,
                 baseurl: str = None,
                 secret: str = None) -> None:
        self._log = logging.getLogger('ObjectiveFunction.config')

        self._basedir = None
        self._path = Path.cwd()
        self._cfg = None
        self._params = None
        self._optimise_params = None
        self._values = None
        self._objfun = None
        self._obsNames = None
        self._proxy = None

        if fname is not None:
            self._read(fname)
        self._app = app
        self._baseurl = baseurl
        self._secret = secret

    def _read(self, fname: Path) -> None:
        if not fname.is_file():
            msg = f'no such configuration file {fname}'
            self._log.error(msg)
            raise RuntimeError(msg)

        self._path = fname.parent

        # read config file into string
        cfgData = fname.open('r').read()
        # expand any environment variables
        cfgData = expandvars(cfgData)

        # populate the default  config object which is used as a validator
        objfunDefaults = ConfigObj(self.defaultCfgStr.split('\n'),
                                   list_values=False, _inspec=True)
        validator = Validator()

        self._cfg = ConfigObj(StringIO(cfgData), configspec=objfunDefaults)

        res = self._cfg.validate(validator, preserve_errors=True)
        errors = []
        # loop over any configuration errors
        for section, key, error in flatten_errors(self.cfg, res):
            section = '.'.join(section)
            if key is None:
                # missing section
                errors.append(f'section {section} is missing')
            else:
                if error is False:
                    errors.append(
                        f'{key} is missing in section {section}')
                else:
                    errors.append(
                        f'{key} in section {section}: {error}')
        if len(errors) > 0:
            msg = f'could not read configuration file {fname}'
            self._log.error(msg)
            for e in errors:
                self._log.error(e)
            raise RuntimeError(msg)

    def expand_path(self, path):
        return (self._path / path).absolute()

    @property
    def defaultCfgStr(self):
        return self.setupCfgStr + '\n' \
            + self.parametersCfgStr + '\n' \
            + self.targetsCfgStr

    def _get_params(self):
        self._params = {}
        self._values = {}

        PARAMS = {'float_parameters': ParameterFloat,
                  'integer_parameters': ParameterInt}

        for t in PARAMS:
            for p in self.cfg['parameters'][t]:
                value = self.cfg['parameters'][t][p]['value']
                minv = self.cfg['parameters'][t][p]['min']
                maxv = self.cfg['parameters'][t][p]['max']
                extra = {}
                extra['constant'] = self.cfg['parameters'][t][p]['constant']
                if t == 'float':
                    extra['resolution'] = \
                        self.cfg['parameters'][t][p]['resolution']
                try:
                    self._params[p] = PARAMS[t](value, minv, maxv, **extra)
                except Exception as e:
                    msg = f'problem with parameter {p}: {e}'
                    self._log.error(msg)
                    raise RuntimeError(msg)
                self._values[p] = self.cfg['parameters'][t][p]['value']

    @property
    def cfg(self):
        """a dictionary containing the configuration"""
        if self._cfg is None:
            raise RuntimeError('no configuration file loaded')
        return self._cfg

    @property
    def baseurl(self):
        """base URL for ObjectiveFunction server API"""
        if self._baseurl is None:
            self._baseurl = self.cfg['setup']['baseurl']
        return self._baseurl

    @property
    def app(self):
        """the application name"""
        if self._app is None:
            self._app = self.cfg['setup']['app']
        return self._app

    @property
    def secret(self):
        """the secret associated with the app name"""
        if self._secret is None:
            pwname = '.objfun_secrets'
            for p in [self.expand_path(pwname), Path.home() / pwname]:
                if p.is_file():
                    self._log.debug(f'reading secret from {p}')
                    secret = ConfigObj(p.open('r'))
                    if self.app in secret:
                        if 'secret' in secret[self.app]:
                            self._secret = secret[self.app]['secret']
                            break
                        else:
                            self._log.warning(
                                f'could not find secret in [{self.app}] '
                                f'in {p}')
                    else:
                        self._log.warning(
                            f'could not find {self.app} in {p}')
            else:
                self._log.error(f'no secret found for {self.app}')
                raise RuntimeError('no secret found')
        return self._secret

    @property
    def values(self):
        """a dictionary of the parameter values"""
        if self._values is None:
            self._get_params()
        return self._values

    @property
    def parameters(self):
        """a dictionary of parameters"""
        if self._params is None:
            self._get_params()
        return self._params

    @property
    def optimise_parameters(self):
        """a dictionary of parameters that should be optimised"""
        if self._optimise_params is None:
            self._optimise_params = {}
            for p in self.parameters:
                if not self.parameters[p].constant:
                    self._optimise_params[p] = self.parameters[p]
        return self._optimise_params

    @property
    def basedir(self):
        """the base directory"""
        if self._basedir is None:
            self._basedir = self.expand_path(
                Path(self.cfg['setup']['basedir']))
            if not self._basedir.exists():
                self._log.info(f'creating base directory {self._basedir}')
                self._basedir.mkdir(parents=True)
        return self._basedir

    @property
    def study(self):
        """the name of the study"""
        return self.cfg['setup']['study']

    @property
    def scenario(self):
        """the name of the scenario"""
        return self.cfg['setup']['scenario']

    @property
    def objfunType(self):
        """the objective function type"""
        return self.cfg['setup']['objfun']

    @property
    def objectiveFunction(self):
        """intantiate a ObjectiveFunction object from config object"""
        if self._objfun is None:
            if self.objfunType == 'misfit':
                objfun = ObjectiveFunctionMisfit
            elif self.objfunType == 'residual':
                objfun = ObjectiveFunctionResidual
            elif self.objfunType == 'simobs':
                if len(self.targets) == 0:
                    msg = 'targets required for simobs'
                    self._log.error(msg)
                    raise RuntimeError(msg)
                objfun = partial(ObjectiveFunctionSimObs,
                                 observationNames=self.observationNames)
            else:
                msg = 'wrong type of objective function: ' + self.objfunType
                self._log.error(msg)
                raise RuntimeError(msg)
            self._objfun = objfun(self.app, self.secret,
                                  self.study, self.basedir,
                                  self.parameters,
                                  scenario=self.scenario,
                                  url_base=self.baseurl)
        return self._objfun

    @property
    def observationNames(self):
        """the name of the observations"""
        if self._obsNames is None:
            self._obsNames = sorted(list(self.cfg['targets'].keys()))
        return self._obsNames

    @property
    def targets(self):
        """the targets"""
        return pandas.Series(self.cfg['targets'])


if __name__ == '__main__':
    import sys
    from pprint import pprint
    cfg = ObjFunConfig(Path(sys.argv[1]))
    pprint(cfg.cfg)

    print(cfg.baseurl)
    print(cfg.app)
    print(cfg.secret)
