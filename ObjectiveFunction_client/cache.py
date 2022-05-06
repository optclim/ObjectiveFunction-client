__all__ = ['ObjFunCache']

import logging
import sqlite3
from pathlib import Path
from collections.abc import MutableMapping

from .common import LookupState


class ObjFunCache(MutableMapping):
    def __init__(self, dbName, parameters, result_type: str):
        self._log = logging.getLogger(
            f'ObjectiveFunction_client.{self.__class__.__name__}')

        if result_type not in ['real', 'text']:
            raise ValueError(f'wrong result_type {result_type}')
        if len(parameters) == 0:
            raise ValueError('number of parameters must be larger than 0')

        self._parameters = tuple(sorted(parameters))

        if dbName == ':memory:' or not dbName.exists():
            self._create_cache(dbName, parameters, result_type)
        else:
            self._check_cache(dbName, parameters, result_type)

        slct = []
        insrt = [':id']
        for p in self.parameters:
            slct.append(f'{p}=:{p}')
            insrt.append(f':{p}')
        insrt.append(f':value')
        self._select_query = \
            'select id, value from lookup where ' + ' and '.join(slct) + ';'
        self._insert_query = \
            'insert into lookup values (' + ', '.join(insrt) + ')'

    @property
    def con(self):
        return self._con

    @property
    def parameters(self):
        return self._parameters

    def _create_cache(self, dbName, parameters, result_type):
        self._log.info('create db')
        self._con = sqlite3.connect(dbName)
        cur = self.con.cursor()

        cols = []
        unique = []
        for p in self.parameters:
            if not p.isalnum():
                raise ValueError(f'wrong parameter name {p}')
            cols.append(f'{p} integer')
            unique.append(p)
        cols.append(f'value {result_type}')
        cur.execute(
            "create table if not exists lookup ("
            "id integer primary key autoincrement, "
            "{0}, unique({1}));".format(
                ",".join(cols), ",".join(unique)))
        self.con.commit()

    def _check_cache(self, dbName, parameters, result_type):
        self._log.info('checking db')
        self._con = sqlite3.connect(dbName)
        # check parameter names
        # see https://stackoverflow.com/questions/7831371/is-there-a-way-to-get-a-list-of-column-names-in-sqlite
        cursor = self.con.execute('select * from lookup')
        names = list(map(lambda x: x[0], cursor.description))
        if len(names) != len(self.parameters) + 2:
            msg = "number of parameters in cache does not match"
            self._log.error(msg)
            raise RuntimeError(msg)
        error = False
        for c in self.parameters:
            if c not in names:
                self._log.error(f'parameter {c} missing from cache')
                error = True
        for c in ['id', 'value']:
            if c not in names:
                self._log.error(f'column {c} missing from cache')
                error = True
        if error:
            raise RuntimeError('columns in cache do not match')

    def _check_key(self, key):
        if self.parameters != tuple(sorted(key.keys())):
            raise KeyError(f'expected dictionary with keys {self.parameters}')

    def __getitem__(self, key):
        self._check_key(key)
        cur = self.con.cursor()
        cur.execute(self._select_query, key)
        r = cur.fetchone()
        if r is None:
            raise LookupError
        run = {'id': r[0],
               'value': r[1],
               'state': LookupState.COMPLETED}
        return run

    def __setitem__(self, key, run):
        self._check_key(key)
        values = dict(key)
        values['id'] = run['id']
        values['value'] = run['value']
        cur = self.con.cursor()
        try:
            cur.execute(self._insert_query, values)
        except sqlite3.IntegrityError:
            raise RuntimeError('entry already exists')
        self.con.commit()

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        cur = self.con.cursor()
        cur.execute("select count(*) from lookup;")
        return cur.fetchone()[0]


if __name__ == '__main__':
    cache = ObjFunCache(Path('/tmp/c.db'), ['a', 'b'], 'real')

    print(len(cache))
    print(cache._select_query)
    print(cache._insert_query)
    cache._check_key({'a': 1, 'b': 2})
    cache[{'a': 1, 'b': 2}] = {'id': 1, 'value': 10.}
    print(cache[{'a': 1, 'b': 2}])
