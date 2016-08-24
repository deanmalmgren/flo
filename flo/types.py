import collections
import six


class FrozenDict(collections.Mapping):
    """FrozenDict makes the equivalent of an immutable dictionary for the
    purpose of memoization.

    adapted from http://stackoverflow.com/a/2705638/564709
    """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        return hash(tuple(sorted(six.iteritems(self._d))))


class UniqueOrderedList(list):
    # keeps elements in the same ordered as master_list but only has
    # them in the list ONCE

    def __init__(self, master_list):
        self.master_list = master_list

    def sort(self):
        # no sense in sorting an empty list
        if not self:
            return
        obj_index = dict((obj, i) for i, obj in enumerate(self.master_list))
        decorated = [(obj_index[obj], obj) for obj in self]
        decorated.sort()
        self[:] = list(zip(*decorated)[1])

    def add(self, obj):
        if obj not in self:
            self.append(obj)
            self.sort()

    def update(self, obj_iterator):
        for obj in obj_iterator:
            self.add(obj)

    def clear(self):
        while self:
            self.pop()

    def difference(self, that_list):
        this_set = set(self)
        that_set = set(that_list)
        ordered_difference = UniqueOrderedList(self.master_list)
        ordered_difference.update(this_set.difference(that_set))
        ordered_difference.sort()
        return ordered_difference
