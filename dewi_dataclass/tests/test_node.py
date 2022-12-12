# Copyright 2018-2022 Laszlo Attila Toth
# Distributed under the terms of the Apache License, Version 2.0

import unittest

import yaml

import dewi_dataclass
from dewi_dataclass.node import Node, NodeList, frozen


class N1(Node):
    x: int
    y: int

    def __init__(self):
        self.x = 0
        self.y = None


class N2(Node):
    list_of_n1s: list[N1]
    title: str
    count: int

    def __init__(self):
        self.list_of_n1s = NodeList(N1)
        self.title = None
        self.count = 100


NODE_TEST_RESULT = """count: 100
list_of_n1s:
- x: 0
  y: null
- x: 0
  y: 42
title: null
"""

NODE_EMPTY_RESULT = """count: 100
list_of_n1s: []
title: null
"""


class NodeAndNodeListTest(unittest.TestCase):
    def setUp(self):
        self.tested = N2()
        self.tested.list_of_n1s.append(N1())

        node = N1()
        node.y = 42
        self.tested.list_of_n1s.append(node)

    def test_empty_object(self):
        self.assertEqual(NODE_EMPTY_RESULT, yaml.dump(N2()))
        self.tested = N2()
        self.assertEqual(NODE_EMPTY_RESULT, yaml.dump(self.tested))

    def test_yaml_dump(self):
        self.assertEqual(NODE_TEST_RESULT, yaml.dump(self.tested))

    def test_load_from_dict(self):
        self.tested = N2()
        self.assertEqual(NODE_EMPTY_RESULT, yaml.dump(self.tested))
        self.tested.load_from(dict(list_of_n1s=[dict(x=0, y=None), dict(x=0, y=42)], title=None))
        self.assertEqual(NODE_TEST_RESULT, yaml.dump(self.tested))

    def test_load_from_yaml(self):
        self.tested = N2()
        self.assertEqual(NODE_EMPTY_RESULT, yaml.dump(self.tested))
        self.tested.load_from(yaml.load(NODE_TEST_RESULT, Loader=yaml.SafeLoader))
        self.assertEqual(NODE_TEST_RESULT, yaml.dump(self.tested))

    def test_size_of_empty_object(self):
        self.assertEqual(3, len(N2()))

    def test_size_of_filled_object(self):
        self.assertEqual(3, len(self.tested))

    def test_size_of_node_list_equals_item_count(self):
        self.assertEqual(2, len(self.tested.list_of_n1s))

    def test_contains_known_members(self):
        self.assertIn('list_of_n1s', self.tested)

    def test_additional_members_can_be_added(self):
        self.assertNotIn('as_member', self.tested)
        self.tested.as_member = 123
        self.assertIn('as_member', self.tested)
        self.assertNotIn('as_key', self.tested)
        self.tested['as_key'] = 4
        self.assertIn('as_key', self.tested)

    def test_that_get_unknown_member_raises_attribute_error(self):
        self.assertRaises(AttributeError, lambda: self.tested.a_member)
        self.assertRaises(AttributeError, lambda: self.tested['another_member'])

    def test_that_key_can_be_invalid_identifier(self):
        self.assertNotIn('a-value', self.tested)
        self.assertFalse(hasattr(self.tested, 'a-value'))
        self.tested['a-value'] = 44
        self.assertEqual(44, self.tested['a-value'])
        self.assertEqual(44, getattr(self.tested, 'a-value'))

    def test_that_in_checks_annotations(self):
        class T(Node):
            x: int

        tested = T()
        self.assertIn('x', tested)

    def test_annotations_only_member(self):
        class T(Node):
            x: int
            y: list[str]

        tested = T()
        self.assertEqual(0, tested.x)
        self.assertEqual(list(), tested.y)

    def test_that_class_level_default_value_can_be_set(self):
        class T(Node):
            x: int = 42

        tested = T()
        self.assertIn('x', tested)
        self.assertEqual(42, tested.x)

    def test_that_class_level_default_value_can_be_overriden(self):
        class T(Node):
            x: int = 42

        tested = T()
        tested.x = 43
        self.assertEqual(42, T.x)
        self.assertEqual(43, tested.x)

    def test_that_non_frozen_node_can_be_extended(self):
        class T(Node):
            x: int

            def __init__(self):
                self.x = 0

        tested = T()
        self.assertNotIn('as_member', tested)
        tested.as_member = 123
        self.assertIn('as_member', tested)
        self.assertEqual(123, tested.as_member)

    def test_that_frozen_node_cannot_be_extended(self):
        @frozen
        class T(Node):
            x: int

            def __init__(self):
                self.x = 0

        tested = T()
        self.assertNotIn('as_member', tested)
        with self.assertRaises(AttributeError) as ctx:
            tested.as_member = 123
        self.assertEqual('as_member', ctx.exception.args[0])

    def test_frozen_allows_inheritance(self):
        @frozen
        class Point(Node):
            x: int
            y: int

            def __init__(self):
                self.x = 1

        class Point3D(Point):
            z: float

            def __init__(self):
                super().__init__()
                self.z = 12

        tested = Point3D()
        self.assertEqual(1, tested.x)
        self.assertEqual(0, tested.y)
        self.assertEqual(12, tested.z)
        self.assertNotIn('as_member', tested)
        with self.assertRaises(AttributeError) as ctx:
            tested.as_member = 123
        self.assertEqual('as_member', ctx.exception.args[0])

    def test_that_frozen_node_init_must_use_annotations_members(self):
        with self.assertRaises(AttributeError) as ctx:
            @frozen
            class Point(Node):
                x: int

                # y is missing here

                def __init__(self):
                    self.y = 1

            _ = Point()

        self.assertEqual('y', ctx.exception.args[0])

    def test_create_node_with_partial_args(self):
        n = N1.create(x=1)
        self.assertEqual(1, n.x)
        self.assertIsNone(n.y)

        n = N1.create(y=4)
        self.assertEqual(0, n.x)
        self.assertEqual(4, n.y)

    def test_create_node_with_complete_arg_list(self):
        n = N1.create(x=1, y=4)
        self.assertEqual(1, n.x)
        self.assertEqual(4, n.y)

    def test_create_node_accepts_only_known_args(self):
        with self.assertRaises(AttributeError) as ctx:
            N1.create(x=1, y=4, unknown_member_name=6)

        self.assertEqual('unknown_member_name', ctx.exception.args[0])


class DataClassModuleTest(unittest.TestCase):

    def test_that_data_class_is_the_node(self):
        self.assertEqual(dewi_dataclass.DataClass, Node, 'DataClass should be the Node class')

    def test_that_data_list_is_the_node_list(self):
        self.assertEqual(dewi_dataclass.DataList, NodeList, 'DataList should be the NodeList class')

    def test_that_frozen_is_available(self):
        self.assertEqual(dewi_dataclass.frozen, frozen)