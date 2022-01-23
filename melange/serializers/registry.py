import logging
from functools import reduce
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

import funcy
from toolz import dicttoolz, itertoolz

from melange.serializers.interfaces import Serializer
from melange.serializers.json import JsonSerializer
from melange.serializers.pickle import PickleSerializer

logger = logging.getLogger(__name__)

default_settings = {
    "serializers": {"json": JsonSerializer, "pickle": PickleSerializer},
    "serializer_bindings": {Dict: "json"},
    "default": "pickle",
}

ClassSerializer = Tuple[Type, Type[Serializer]]


class SerializerRegistry:
    """
    This serializer registry tries to match the interface of akka:
    https://github.com/akka/akka/blob/main/akka-actor/src/main/scala/akka/serialization/Serialization.scala

    Explanations: https://doc.akka.io/docs/akka/current/serialization.html
    """

    def __init__(self, config: Dict):
        self._config_serializers: Dict[str, Type[Serializer]] = config["serializers"]
        self._config_bindings: Dict[Type, str] = config["serializer_bindings"]

        self._serializer_map: Dict[Type, Type[Serializer]] = dicttoolz.valmap(
            lambda v: self._config_serializers[v], self._config_bindings
        )

        # The bindings are sorted by specifity (meaning the lower the types
        # in the hierarchy occupy the first positions)
        self._bindings = list(sort((k, v) for k, v in self._serializer_map.items()))

        self._default_serializer: Optional[Type[Serializer]]
        try:
            self._default_serializer = self._config_serializers[config["default"]]
        except Exception:
            self._default_serializer = None

        self._serializers_by_id: Dict[int, Type[Serializer]] = {
            v.identifier(): v for k, v in self._config_serializers.items()  # type: ignore
        }
        self._quickserializer_by_identity: List[Optional[Type[Serializer]]] = [
            None
        ] * 1024

        for k, v in self._serializers_by_id.items():
            self._quickserializer_by_identity[k] = v

    def get_serializer_by_id(self, id: int) -> Type[Serializer]:
        if id < 1024:
            serializer = self._quickserializer_by_identity[id]
            if not serializer:
                raise Exception(f"Serializer with ID {id} not found")
            return serializer
        else:
            return self._serializers_by_id[id]

    def get_serializer_by_name(self, name: str) -> Type[Serializer]:
        return self._config_serializers[name]

    def deserialize_with_serializerid(
        self, data: str, serializer_id: int, manifest: Optional[str]
    ) -> Any:
        serializer = self.get_serializer_by_id(serializer_id)()
        return serializer.deserialize(data, manifest)

    def deserialize_with_class(
        self, data: str, klass: Type, manifest: Optional[str]
    ) -> Any:
        serializer = self.serializer_for(klass)()
        return serializer.deserialize(data, manifest)

    def serialize(self, obj: Any) -> str:
        serializer = self.find_serializer_for(obj)
        data = serializer.serialize(obj)
        return data

    def find_serializer_for(self, obj: Any) -> Serializer:
        return self.serializer_for(type(obj))()

    def serializer_for(self, type: Type) -> Type[Serializer]:
        if self._serializer_map.get(type):
            return self._serializer_map[type]
        else:
            # Check if the type is a subclass of any of the defined serializers
            possible_bindings = funcy.lfilter(
                lambda t: issubclass(type, t), self._bindings
            )
            if len(possible_bindings) == 0:
                # No serializer found. Return the default serializer
                if self._default_serializer:
                    return self._default_serializer
                else:
                    raise Exception(f"No serializer could be found for the type {type}")
            elif len(possible_bindings) == 1:
                return possible_bindings[0][1]
            else:
                logger.warning(
                    f"More than one serializer found for type {type}. "
                    "Choosing the first one."
                )
                return itertoolz.first(possible_bindings)[1]


def sort(list_items: Iterable[ClassSerializer]) -> Iterable[ClassSerializer]:
    """
    Sort so that subtypes always precede their supertypes, but without
    obeying any order between unrelated subtypes (insert sort).
    """

    def _(
        buffer: List[ClassSerializer], type_tuple: ClassSerializer
    ) -> List[ClassSerializer]:
        t = type_tuple[0]

        index = next((i for i, v in enumerate(buffer) if issubclass(t, v[0])), None)
        if index is None:
            buffer.append(type_tuple)
        else:
            buffer.insert(index, type_tuple)

        return buffer

    init: List[ClassSerializer] = []
    return reduce(_, list(list_items), init)  # type: ignore
