import copy
import pickle

import pytest

from schematics.datastructures import *


def test_data_object_basics():

    d = DataObject({'x': 1, 'y': 2})

    assert d == d
    assert d == DataObject(x=1, y=2)
    assert d != DataObject(x=2, y=1)
    assert d != {'x': 1, 'y': 2}

    assert DataObject({'f': DataObject({'g': {'x': 1, 'y': 2}})}) \
        != {'f': {'g': {'x': 1, 'y': 2}}}

    assert hasattr(d, 'x')
    assert 'x' in d
    assert not hasattr(d, 'z')
    assert 'z' not in d

    assert d.x == 1
    with pytest.raises(AttributeError):
        d.z

    assert d['x'] == 1
    with pytest.raises(KeyError):
        d['z']

    assert d._get('z') is None
    assert d._get('z', 0) == 0

    d.z = 3
    assert d.z == 3
    assert d['z'] == 3

    assert len(d) == 3

    assert set(((k, v) for k, v in d)) \
        == set(d._items()) \
        == set((('x', 1), ('y', 2), ('z', 3)))

    assert set((k for k, v in d)) \
        == set(d._keys()) \
        == set(('x', 'y', 'z'))

    x = d._pop('x')
    assert x == 1 and 'x' not in d

    d._clear()
    assert d.__dict__ == {}


def test_data_object_methods():

    d = DataObject({'x': 1})
    d._update({'y': 2})
    d._update(DataObject({'z': 3}, q=4))
    d._update(zip(('n', 'm'), (5, 6)))
    assert d == DataObject({'x': 1, 'y': 2, 'z': 3, 'q': 4, 'n': 5, 'm': 6})

    d = DataObject({'x': 1})
    assert d._setdefault('x') == 1
    a = d._setdefault('a')
    assert a is None and d.a is None
    b = d._setdefault('b', 99)
    assert b == 99 and d.b == 99
    d._setdefaults({'i': 12, 'j': 23})
    assert d.i == 12 and d.j == 23

    assert DataObject({'f': DataObject({'g': {'x': 1, 'y': 2}})})._to_dict() \
        == {'f': {'g': {'x': 1, 'y': 2}}}


def test_data_object_copy():

    d = DataObject({'f': DataObject({'g': {'x': 1, 'y': 2}})})

    d_copy = d._copy()
    assert d_copy == d
    assert id(d_copy) != id(d)
    assert id(d_copy.f) == id(d.f)

    d_deepcopy = copy.deepcopy(d)
    assert d_deepcopy == d
    assert id(d_deepcopy) != id(d)
    assert id(d_deepcopy.f) != id(d.f)


def test_context():

    class FooContext(Context):
        _fields = ('x', 'y', 'z')

    assert bool(FooContext()) is True

    c = FooContext(x=1, y=2)
    assert c._dict == dict(x=1, y=2)

    with pytest.raises(ValueError):
        FooContext(a=1)

    assert c.initialized is False
    c.x = 1
    c._seal()
    with pytest.raises(Exception):
        c.x = 0

    c.z = 3
    assert c._dict == dict(x=1, y=2, z=3)

    assert len(c) == 3

    c = FooContext._new(1, 2, 3)
    assert c._dict == dict(x=1, y=2, z=3)

    with pytest.raises(TypeError):
        FooContext._new(1, 2, 3, 4)

    d = c._branch()
    assert d is c

    d = c._branch(x=None)
    assert d is not c

    c._seal()
    d = c._branch(x=0)
    assert d is not c
    assert d._dict == dict(x=0, y=2, z=3)
    assert d.initialized is True

    e = d._branch(x=0)
    assert e is d

    c = FooContext(x=1, y=2)
    c._setdefaults(dict(x=9, z=9))
    assert c._dict == dict(x=1, y=2, z=9)

    c = FooContext(x=1, y=2)
    c._setdefaults(FooContext(x=9, z=9))
    assert c._dict == dict(x=1, y=2, z=9)

