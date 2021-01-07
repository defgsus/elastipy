from copy import copy, deepcopy
from typing import Sequence, Mapping, Optional, Union

from .query import Query, QueryInterface, factory
from .generated_classes import _Bool


class Bool(_Bool):

    def _map_parameters(self, params: Mapping) -> dict:
        params = super()._map_parameters(params)
        for key, value in params.items():
            # wrap a single query into a list
            if not isinstance(value, Sequence):
                params[key] = [value]

            for v in params[key]:
                if not isinstance(v, (Query, Mapping)):
                    raise TypeError(f"{self.__class__.__name__} parameter '{key}' has invalid type {type(v).__name__}"
                                    f", must be Query or dict")
        return params

    @property
    def must(self):
        return self._get_bool_param("must")

    @must.setter
    def must(self, value):
        self._set_bool_param("must", value)

    @property
    def must_not(self):
        return self._get_bool_param("must_not")

    @must_not.setter
    def must_not(self, value):
        self._set_bool_param("must_not", value)

    @property
    def should(self):
        return self._get_bool_param("should")

    @should.setter
    def should(self, value):
        self._set_bool_param("should", value)

    @property
    def filter(self):
        return self._get_bool_param("filter")

    @filter.setter
    def filter(self, value):
        self._set_bool_param("filter", value)

    def _get_bool_param(self, name):
        return self.parameters.get(name) or []

    def _set_bool_param(self, name, value):
        if value == self._optional_parameters.get(name):
            self.parameters.pop(name, None)
        else:
            assert isinstance(value, Sequence), f"Failed in {self} with {name}:{value}"
            self.parameters[name] = value

    def add_query(self, name, **params) -> 'Bool':
        return self & factory(name, **params)

    def __and__(self, other) -> 'Bool':
        self_ = self
        if not isinstance(self_, Bool):
            self_, other = other, self_

        if not isinstance(other, Bool):
            q = copy(self_)
            q.must += [other]
            return q

        else:
            q = copy(self_)
            for key in ("must", "must_not", "should", "filter"):
                for o in getattr(other, key):
                    if o not in getattr(self_, key):
                        setattr(q, key, getattr(q, key) + [o])
            return q

    def __or__(self, other):
        self_ = self
        if not isinstance(self_, Bool):
            self_, other = other, self_

        if not isinstance(other, Bool):
            q = copy(self)
            if q.should:
                if not q.must and not q.must_not and not q.filter:
                    q.should += [other]
                    return q

        return super().__or__(other)
