"""pytest 9 dropped the private ``_nodeid`` attribute. mutmut 3.8 still reads it."""

from _pytest.nodes import Item

if not hasattr(Item, "_nodeid"):
    Item._nodeid = property(lambda self: self.nodeid)
