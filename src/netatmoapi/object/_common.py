from __future__ import annotations

from copy import deepcopy
from typing import Any, Generator, Mapping, Sequence, Type, Hashable, Callable
from collections.abc import Mapping, Sequence
from functools import partial


class Object:
    """Netatmo API base class.

    Not intended for direct use, use inherited classes.
    """

    def __init__(self, _: Any) -> None:
        pass

    def _assign(self, item: Any, method: Callable[[Any], None]) -> None:
        if item is None:
            method(None)
            return
        for type_ in (bool, int, float, str):
            if isinstance(item, type_):
                method(type_(item))
                return
        if isinstance(item, Sequence):
            method(SequenceObject(item))
            return
        if isinstance(item, Mapping):
            method(MappingObject(item))
            return
        raise ObjectDataError(self, item)

    def copy(self) -> Object:
        """Return a copy of the object."""
        return deepcopy(self)


class SequenceObject(Sequence, Object):
    """Netatmo API base sequence class.

    Not intended for direct use, use inherited classes.
    """

    def __init__(self, sequence: Sequence[Any]) -> None:
        self._sequence = []
        for item in sequence:
            self._assign(item, self._sequence.append)

    def __getitem__(self, key: int) -> Any:
        return self._sequence[key]
    
    def __len__(self) -> None:
        return len(self._sequence)

    def _iter(self, type_: Type[Object]) -> Generator[Object, None, None]:
        for object_ in self:
            yield type_(object_)

    def _list(self, type_: Type[Object]) -> list[Object]:
        return list(self._iter(type_))


class MappingObject(Mapping, Object):
    """Netatmo API base mapping class.

    Not intended for direct use, use inherited classes.
    """

    def __init__(self, mapping: Mapping[Any, Any]) -> None:
        self._mapping = {}
        for key, value in mapping.items():
            self._assign(value, partial(self._mapping.__setitem__, key))

    def __getitem__(self, key: Hashable) -> Any:
        return self._mapping[key]

    def __iter__(self) -> Any:
        for key in self._mapping:
            yield key
    
    def __len__(self) -> None:
        return len(self._mapping)

    def _get_type(self, key: Any, type_: Type[Any]) -> Any:
        try:
            value = self[key]
            if not isinstance(value, type_):
                raise ObjectTypeError(self, key, value) from None
            return value  # type: ignore[no-any-return]
        except KeyError:
            raise ObjectAttributeError(self, key) from None

    def _get_str(self, key: Any) -> str:
        return self._get_type(key, str)  # type: ignore[no-any-return]

    def _get_int(self, key: Any) -> int:
        return self._get_type(key, int)  # type: ignore[no-any-return]

    def _get_bool(self, key: Any) -> bool:
        return self._get_type(key, bool)  # type: ignore[no-any-return]


class HomeObject(MappingObject):
    """*Home* base class.

    Not intended for direct use, use inherited classes.
    """

    @property
    def id(self) -> bytes:
        """*Home* ID as bytes."""
        try:
            return bytes.fromhex(self._get_str("id"))
        except ValueError:
            raise ObjectIdError(self) from None


class RoomObject(MappingObject):
    """*Room* base class.

    Not intended for direct use, use inherited classes.
    """

    @property
    def id(self) -> int:
        """*Room* ID as integer."""
        try:
            return self._get_int("id")
        except ValueError:
            raise ObjectIdError(self) from None


class ModuleObject(MappingObject):
    """*Module* base class.

    Not intended for direct use, use inherited classes.
    """

    @property
    def id(self) -> bytes:
        """*Module* ID as bytes."""  # noqa: D401
        try:
            return bytes.fromhex(self._get_str("id").replace(":", ""))
        except ValueError:
            raise ObjectIdError(self) from None


class ObjectError(Exception):
    """Invalid Netatmo API object."""

    pass


class ObjectAttributeError(ObjectError):
    """ObjectAttributeError()

    Missing attribute in Netatmo API object.
    """  # noqa: D400

    def __init__(self, obj: Object, name: str) -> None:
        super().__init__(f"{type(obj).__name__} attribute '{name}' is missing")


class ObjectDataError(ObjectError):
    """Invalid data to create Netatmo API object."""

    def __init__(self) -> None:
        super().__init__(f"{type(obj).__name__} attribute '{name}' is missing")


class ObjectIdError(ObjectError):
    """ObjectIdError()

    Invalid ID in Netatmo API object.
    """  # noqa: D400

    def __init__(self, obj: Object) -> None:
        super().__init__(f"{type(obj).__name__} ID is invalid")


class ObjectTypeError(ObjectError):
    """ObjectTypeError()

    Invalid attribute type in Netatmo API object.
    """  # noqa: D400

    def __init__(self, obj: Object, name: str, value: Any) -> None:
        super().__init__(
            (
                f"{type(obj).__name__} attribute '{name}' is invalid type: "
                f"{type(value).__name__}"
            )
        )
