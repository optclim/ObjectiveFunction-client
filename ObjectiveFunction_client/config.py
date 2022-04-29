__all__ = ['ObjFunConfig']

import logging
from configobj import ConfigObj, flatten_errors
from validate import Validator
from pathlib import Path
from os.path import expandvars
from io import StringIO


class ObjFunConfig:
    """handle ObjectiveFunction configuration

    :param fname: the name of the configuration file
    :type fname: Path
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

    def __init__(self, fname: Path) -> None:
        self._log = logging.getLogger('ObjectiveFunction.config')

        if not fname.is_file():
            msg = f'no such configuration file {fname}'
            self._log.error(msg)
            raise RuntimeError(msg)

        self._basedir = None
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

        self._secret = None

    def expand_path(self, path):
        return (self._path / path).absolute()

    @property
    def defaultCfgStr(self):
        return self.setupCfgStr

    @property
    def cfg(self):
        """a dictionary containing the configuration"""
        return self._cfg

    @property
    def baseurl(self):
        return self.cfg['setup']['baseurl']

    @property
    def app(self):
        return self.cfg['setup']['app']

    @property
    def secret(self):
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


if __name__ == '__main__':
    import sys
    from pprint import pprint
    cfg = ObjFunConfig(Path(sys.argv[1]))

    print(cfg.baseurl)
    print(cfg.app)
    print(cfg.secret)
