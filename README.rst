DEWI dataclass
==============

A Python dataclass implementation based on MutableDict. It shares some features
with builtin ``typing.TypedDict``, but can be extended. It's extendable
by default. The other inspiration is the ``attrs`` pip package, especially
the ``@frozen`` decorator.

Compared to other implementations strongly typed tree hierachy works
out of the box, which inspires the class name, ``Node``, like a tree's node,
and its alias, ``DataClass``.

Unlike in a simple ``dict`` a missing entry causes ``AttributeError``
instead of ``KeyError``.


Basic Usage
-----------

The most basic usage is to use as an enhanced dict:

.. code-block:: python

    from dewi_dataclass import DataClass

    val = DataClass()

    # use as regular dict
    val['key1'] = 42
    # use as class member
    print(val.key1)   # 42

    # missing item raises AttributeError
    print(val['missing'])
    print(val.missing)

Usage
-----

The class' features come live when a subclass is created.


create() and creation
~~~~~~~~~~~~~~~~~~~~~

It has a factory method, ``create`` which checks if
the members are valid, already known or not:

.. code-block:: python

    class Point(DataClass):
        x: int

        def __init__(self):
            self.y = 4


    print(Point.create(x=3))
    print(Point.create(x=3, y=22))

    # and raises AttributeError if the field is unknown
    print(Point.create(z=1))

If the member type's constructor (or no-arg ``__init__`` method) is just fine,
the data class' ``__init__`` is not needed at all:

.. code-block:: python

    class Data(DataClass):
        x: int
        y: list[str]


    d = Data()
    print(d.y)  # []

    # but d.x is not yet set as it's not yet read.


DataList: ist of DataClass objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A specialized list type is also provided for lists of DataClass objects.

.. code-block:: python

    from data_class import DataClass, DataList

    class Modules(DataClass):
       # details are omitted
       pass

    class Params(DataClass):
       modules: DataList[Modules]  # and not list[Modules]


DataList (or NodeList) is useful when a JSON or YAML file is loaded and
its content should be loaded into a data class in a typesafe way.


load_from(): load from a ``dict`` hierarchy, like YAML
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class Params(DataClass):
        ...

    params = Params()
    params.load_from(yaml.safe_load(...))


The above example can be shortened if the variable can be created
at the same time:

.. code-block:: python

    params = Params.create(**yaml.safe_load(...))


Frozen types
~~~~~~~~~~~~
Any data class can be frozen, new members cannot be defined even
in the ``__init__()`` method, only via annotations or ``create()``,
but the class can be extended via inheritance in a sublcass.

.. code-block:: python

    @frozen
    class Point(DataClass):
        x: float
        y: float

        def __init__(self)
           self.z = 42   # ❌ doesn't work, raises AttributeError

    class Point3D(Point):
        def __init__(self):
            self.z = 0.0   # ✅ OK

    class Point3Dv2(Point):
        z: float  # ✅ OK

    point = Point()
    point.z = 0.0       # ❌ doesn't work, raises AttributeError


as_dict(): convert to core Python types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For YAML / JSON serialization either the types should be registered
or in this case a dedicated method is required to convert the dict-like
and list-like objects to actual dicts and lists.

As the top-level data structure is a specialized dictionary, ``as_dict()`` can be used:

.. code-block:: python

    from dewi_dataclass import DataClass, as_dict

    class Point(DataClass):
        ...

    point = Point()

    print(point.as_dict())
    # or
    print(as_dict(point))
