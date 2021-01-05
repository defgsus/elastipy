import json
import datetime
from typing import Optional, List, Iterable, Union, Tuple, TextIO, Sequence, Mapping
from warnings import warn

from .. import make_json_compatible
from .generated_interface import AggregationInterface


class Aggregation(AggregationInterface):
    """
    Aggregation definition and response parser.

    Do not create instances yourself,
    use the Query.aggregation() and Aggregation.aggregation() variants
    """

    _factory_class_map = dict()

    def __init_subclass__(cls, **kwargs):
        if "factory" not in kwargs or kwargs["factory"]:
            Aggregation._factory_class_map[cls._agg_type] = cls

    def __init__(self, search, name, type, params):
        from ..search import Response
        AggregationInterface.__init__(self, timestamp_field=search.timestamp_field)
        self.search = search
        self.name = name
        self.type = type
        self.definition = self.AGGREGATION_DEFINITION.get(self.type) or dict()
        self.params = self._get_parameters(params)
        self._response: Optional[Response] = None
        self.parent: Optional[Aggregation] = None
        self.root: Aggregation = self
        self.children: List[Aggregation] = []

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}', '{self.type}')"

    @property
    def print(self):
        """
        Access to printing interface
        :return: PrintWrapper instance
        """
        from .print_wrapper import PrintWrapper
        return PrintWrapper(self)

    @property
    def group(self) -> str:
        """
        Returns the name of the aggregation group.
        :return: str, either "bucket", "metric" or "pipeline"
        """
        if "group" not in self.definition:
            warn(f"Aggregation '{self.name}'/{self.type} has no definition, 'group' is unknown.")
        return self.definition.get("group") or None

    def is_bucket(self):
        if "group" not in self.definition:
            warn(f"Aggregation '{self.name}'/{self.type} has no definition, is_bucket() is unknown")
        return self.definition.get("group") == "bucket"

    def is_metric(self):
        if "group" not in self.definition:
            warn(f"Aggregation '{self.name}'/{self.type} has no definition, is_metric() is unknown")
        return self.definition.get("group") == "metric"

    def is_pipeline(self):
        if "group" not in self.definition:
            warn(f"Aggregation '{self.name}'/{self.type} has no definition, is_pipeline() is unknown")
        return self.definition.get("group") == "pipeline"

    # Not defined in yamls and not used yet
    #def is_single_bucket(self):
    #    if not self.definition:
    #        warn(f"Aggregation '{self.name}'/{self.type} has no definition, is_single_bucket() is unknown")
    #    return self.definition.get("single_bucket")

    def metrics(self):
        """
        Iterate through all contained metric aggregations
        :return: generator of Aggregation
        """
        for c in self.children:
            if c.is_metric():
                yield c

    def to_body(self):
        """
        Returns the part of the elasticsearch request body
        :return: dict
        """
        params = make_json_compatible(self.params)
        if self.definition.get("parameters"):
            for key, defi in self.definition["parameters"].items():
                # convert 'ranges' lists to dict
                if defi.get("ranges") and params.get("ranges"):
                    params["ranges"] = _convert_ranges_param(self, params["ranges"])
        return params

    def aggregation(self, *aggregation_name_type, **params) -> 'Aggregation':
        """
        Interface to create sub-aggregations.

        This is the generic, undocumented version.
        Use the agg_*, metric_* and pipeline_* methods for convenience.

        :param aggregation_name_type: one or two strings, meaning either "type" or "name", "type"
        :param params: all parameters of the aggregation function
        :return: Aggregation instance
        """
        if len(aggregation_name_type) == 1:
            name = f"a{len(self.search._aggregations)}"
            aggregation_type = aggregation_name_type[0]
        elif len(aggregation_name_type) == 2:
            name, aggregation_type = aggregation_name_type
        else:
            raise ValueError(f"Need to provide (aggregation_type) or (name, aggregation_type), got {aggregation_name_type}")

        agg = factory(
            search=self.search, name=name, type=aggregation_type, params=params
        )
        agg.parent = self
        agg.root = self.root
        self.children.append(agg)
        self.search._aggregations.append(agg)
        self.search._add_body(f"{self.body_path()}.aggregations.{name}.{aggregation_type}", agg.to_body())
        return agg

    def execute(self):
        """
        Executes the whole query with all aggregations
        :return: self
        """
        self.search.execute()
        return self

    @property
    def response(self) -> dict:
        """
        Returns the response object of the aggregation

        Only available for root aggregations!
        :return: dict
        """
        if self.parent:
            raise ValueError(f"Can not get response of sub-aggregation '{self.name}' ({self.type})")
        if not self._response:
            raise ValueError(f"Can not get response of aggregation '{self.name}' ({self.type}), "
                             f"search has not been executed")
        return self._response.aggregations[self.name]

    @property
    def buckets(self) -> Union[dict, list]:
        """
        Returns the buckets of the aggregation response

        Only available for bucket root aggregations!
        :return: dict or list
        """
        if self.parent:
            raise ValueError(f"Can not get buckets of sub-aggregation '{self.name}' (type {self.type}) "
                             f"directly, use keys() and values()")
        return self.response["buckets"]

    def keys(self, key_separator=None):
        """
        Iterates through all keys of this aggregation.

        For example, a top-level date_histogram would return all timestamps.

        For a nested bucket aggregation each key is a tuple of all parent keys as well.

        :param key_separator: str, optional separator to concat multiple keys into one string
        :return: generator
        """
        from .visitor import Visitor
        return Visitor(self).keys(key_separator=key_separator)

    def values(self, default=None):
        """
        Iterates through all values of this aggregation.
        :param default: if not None any None-value will be replaced by this
        :return: generator
        """
        from .visitor import Visitor
        return Visitor(self).values(default=default)

    def items(self, key_separator=None, default=None) -> Iterable[Tuple]:
        """
        Iterates through all key, value tuples.
        :param key_separator: str, optional separator to concat multiple keys into one string
        :param default: if not None any None-value will be replaced by this
        :return: generator
        """
        yield from zip(self.keys(key_separator=key_separator), self.values(default=default))

    def dict_rows(self) -> Iterable[dict]:
        """
        Iterates through all result values from this aggregation branch.

        This will include all parent aggregations (up to the root) and all children
        aggregations (including metrics).

        :return: generator of dict
        """
        from .visitor import Visitor
        return Visitor(self).dict_rows()

    def rows(self, header=True) -> Iterable[Sequence]:
        from .visitor import Visitor
        return Visitor(self).rows(header=header)

    def to_dict(self, key_separator=None, default=None) -> dict:
        """
        Create a dictionary from all key/value pairs.
        :param key_separator: str, optional separator to concat multiple keys into one string
        :param default: if not None any None-value will be replaced by this
        :return: dict
        """
        return {
            key: value
            for key, value in self.items(key_separator=key_separator, default=default)
        }

    def key_name(self) -> str:
        """
        Return default name of the bucket key field.

        Metrics return their parent's key
        :return: str
        """
        if self.is_metric() and self.parent:
            return self.parent.key_name()
        key_name = "key"
        # TODO: this should be configurable
        if self.type == "date_histogram":
            key_name = "key_as_string"
        return key_name

    def body_path(self) -> str:
        """
        Return the dotted path of this aggregation in the request body
        :return: str
        """
        if not self.parent:
            return f"aggregations.{self.name}"
        else:
            return f"{self.parent.body_path()}.aggregations.{self.name}"

    def _get_parameters(self, params: Mapping) -> Mapping:
        """
        Convert the constructor parameters to aggregation parameters.
        It basically just removes the default parameters that are not changed.
        :return: dict
        """
        ret_params = dict()
        for key, value in params.items():

            param_key = key.replace("__", ".")
            if self.definition.get("parameters") and param_key in self.definition["parameters"]:
                param_def = self.definition["parameters"][param_key]
                # not required and matches default value
                if not param_def.get("required") and param_def.get("default") == value:
                    if param_def.get("timestamp"):
                        value = self.search.timestamp_field
                    else:
                        continue

            if "__" in key or "." in key:
                # TODO: this will break for sub-sub-keys but it's anyway not a good approach..
                root_key, sub_key = key.split("__") if "__" in key else key.split(".")
                if root_key not in ret_params:
                    ret_params[root_key] = dict()
                ret_params[root_key][sub_key] = value
            else:
                ret_params[key] = value

        if self.definition.get("parameters"):
            for name, param in self.definition["parameters"].items():
                # case when creating through generic .aggregation() function
                if param.get("timestamp") and name not in ret_params:
                    ret_params[name] = self.search.timestamp_field

        return ret_params


def factory(search, name, type, params) -> Aggregation:
    """
    Creates an instance of the matching Aggregation sub-class
    :return: instance of (derived) Aggregation class
    """
    if type in Aggregation._factory_class_map:
        klass = Aggregation._factory_class_map[type]
        try:
            return klass(search, name, type, params)
        except TypeError as e:
            raise TypeError(f"{e} in class {klass.__name__}")

    return Aggregation(search, name, type, params)


def _convert_ranges_param(agg, ranges):
    if not isinstance(ranges, Sequence):
        raise TypeError(f"{agg} 'ranges' parameter must be list or dict")

    ret = []
    prev_value = None
    for i, r in enumerate(ranges):
        if isinstance(r, Mapping):
            ret.append(r)
            if "to" in r:
                prev_value = r
        else:
            if prev_value is None:
                ret.append({"to": r})
            else:
                ret.append({"from": prev_value, "to": r})
                if i == len(ranges) - 1:
                    ret.append({"from": r})
            prev_value = r
    return ret
