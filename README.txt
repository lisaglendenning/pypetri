Python library for petri nets.

To install:

python setup.py install

KNOWN ISSUES:

Maintain rules that create arcs between vertices don't seem to work. They are run multiple times and it looks like they are not properly rolled back (end up with duplicate arcs). For now, create arcs in rules that only run once.
