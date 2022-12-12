# Copyright 2017-2022 Laszlo Attila Toth
# Distributed under the terms of the Apache License, Version 2.0

import collections.abc

import yaml
from yaml.dumper import Dumper


def _frozen__setattr__(cls, self, key, value):
    if key not in self.__dict__ and not self.has_annotation(key):
        raise AttributeError(key)
    super(cls, self).__setattr__(key, value)


def frozen(cls):
    cls.__setattr__ = lambda self, key, value: _frozen__setattr__(cls, self, key, value)
    return cls


class _MetaNode(collections.abc.MutableMapping):

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls)

        for k, v in dct.items():
            x['k'] = v
        return x

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __iter__(self):
        return iter(self.__dict__)

    def __delitem__(self, key):
        raise RuntimeError('Unable to delete key {}'.format(key))

    def __repr__(self):
        return str(self.__dict__)

    def __contains__(self, item):
        return item in self.__dict__ or self.has_annotation(item)

    def has_annotation(self, name: str):

        if name not in self.__annotations__:
            for base in yield_bases(self.__class__):
                if name in base.__annotations__:
                    return True

            return False

        return True

    def __hash__(self):
        return hash(self.__dict__)


def yield_bases(cls):
    for base in cls.__bases__:
        if base != object and base != Node:
            yield base
            yield from yield_bases(base)


class Node(collections.abc.MutableMapping):
    """
    Base class for dict-based data objects and dict trees.

    Each member can be accessed both as regular object member
    and as dictionary key.

    Members can be set in usual __init__(), but from type annotations
    the corresponding type's default value can also be used (set).

    Example:

    >>> class A(Node):
    >>>     entry: str = 'default-value'
    >>>     another_entry: int
    >>>     node: Node
    >>>     def __init__(self):
    >>>         self.node = Node()
    >>> a = A()
    >>> print(a.entry) # default-value
    >>> print(a.another_entry) # 0

    Any Node can be frozen, so it's open to extend in subclasses
    but closed to add any new member.
    """

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            attr = self.get_annotation(key)
            if attr is None:
                raise

            self.__setitem__(key, attr())

    def __getattr__(self, key):
        try:
            return super().__getattr__(key)
        except AttributeError:
            attr = self.get_annotation(key)
            if attr is None:
                raise

            v = attr()
            self.__setitem__(key, v)
            return v

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __iter__(self):
        return iter(self.__dict__)

    def __delitem__(self, key):
        raise RuntimeError('Unable to delete key {}'.format(key))

    def __repr__(self):
        return str(self.__dict__)

    def __contains__(self, item):
        return item in self.__dict__ or self.has_annotation(item)

    def has_annotation(self, name: str):
        if name not in self.__annotations__:
            for base in yield_bases(self.__class__):
                if name in base.__annotations__:
                    return True

            return False

        return True

    def get_annotation(self, name: str):
        def yield_bases(cls):
            for base in cls.__bases__:
                if base != object and base != Node:
                    yield base
                    yield from yield_bases(base)

        if name in self.__annotations__:
            return self.__annotations__[name]
        else:
            for base in yield_bases(self.__class__):
                if name in base.__annotations__:
                    return base.__annotations__[name]

        return None

    def load_from(self, data: dict, *, raise_error: bool = False):
        load_node(self, data, raise_error=raise_error)

    @classmethod
    def create_from(cls, data: dict):
        n = cls()
        n.load_from(data)
        return n

    @classmethod
    def create(cls, /, **kwargs):
        n = cls()
        n.load_from(kwargs, raise_error=True)
        return n


class NodeList(list):
    type_: type[Node]

    def __init__(self, member_type: type[Node]):
        super().__init__()
        self.type_ = member_type

    def load_from(self, data: list):
        self.clear()
        for item in data:
            if isinstance(item, Node):
                self.append(item)
            else:
                node = self.type_()
                node.load_from(item)
                self.append(node)


def load_node(node: Node, d: dict, *, raise_error: bool = False):
    for key, value in d.items():
        if key in node and isinstance(node[key], (Node, NodeList)):
            node[key].load_from(value)
        elif key in node:
            node[key] = value
        elif not raise_error:
            if isinstance(value, dict):
                node[key] = Node()
                node[key].load_from(value)
            elif isinstance(value, (list, tuple)):
                if isinstance(value, tuple):
                    value = list(value)
                if value and isinstance(value[0], dict):
                    node[key] = NodeList(Node)
                    node[key].load_from(value)
                else:
                    node[key] = value
            else:
                node[key] = value
        else:
            raise AttributeError(key)


def represent_node(dumper: Dumper, data: Node):
    return dumper.represent_dict(data)


def represent_node_list(dumper: Dumper, data: NodeList):
    return dumper.represent_list(data)


yaml.add_multi_representer(Node, represent_node)
yaml.add_multi_representer(NodeList, represent_node_list)
