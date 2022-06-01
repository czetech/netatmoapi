# from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generator, Iterable, Optional, Tuple

from ._common import HomeObject, ModuleObject, RoomObject, SequenceObject


class HomeStatus(HomeObject):
    """*Home status* object.

    :param home_status: Source *home status* dict.
    """

    def __init__(self, home_status: Mapping[str, Any]) -> None:
        super().__init__(home_status)

    """def update_home(self, home_status: HomeStatus) -> HomeStatus:
        assert self.id == home_status.id
        home_status_change = HomeStatus({k: home_status[k] for k in ("id",)})
        for key, value in home_status.items():
            if key not in ("id", "rooms", "modules") and value != self.get(key):
                self[key] = value
                home_status_change[key] = value
        for module_status in home_status.modules or ():
            if self.set_module(module_status):
                home_status_change.set_module(module_status)
        for room_status in home_status.rooms or ():
            if self.set_room(room_status):
                home_status_change.set_room(room_status)
        return home_status_change

    def get_module_by_id(self, module_id: bytes) -> Optional[ModuleStatus]:
        for module_status in self.modules:
            if module_status.id == module_id:
                return module_status

    def set_module(self, module_status: ModuleStatus) -> bool:
        modules = self.setdefault("modules", [])
        for i, enum_module_status in enumerate(self.modules):
            if enum_module_status.id == module_status.id:
                if modules[i] != module_status:
                    modules[i] = module_status
                    return True
                return False
        modules.append(module_status)
        return True

    def compare_modules(
        self, modules_status: Iterable[ModuleStatus]
    ) -> Generator(Tuple[ModuleStatus, ModuleStatus, Tuple[str, ...]], None, None):
        for module_status_change in modules_status:
            module_status = self.get_module_by_id(module_status_change.id)
            if module_status and module_status != module_status_change:
                module_diffs = tuple(
                    k
                    for k, v in module_status_change.items()
                    if v != module_status.get(k)
                )
                yield (module_status, module_status_change, module_diffs)

    def get_room_by_id(self, room_id: int) -> Optional[RoomStatus]:
        for room_status in self.rooms:
            if room_status.id == room_id:
                return room_status

    def set_room(self, room_status: RoomStatus) -> bool:
        rooms = self.setdefault("rooms", [])
        for i, enum_room_status in enumerate(self.rooms):
            if enum_room_status.id == room_status.id:
                if rooms[i] != room_status:
                    rooms[i] = room_status
                    return True
                return False
        rooms.append(room_status)
        return True

    def compare_rooms(
        self, rooms_status: Iterable[RoomStatus]
    ) -> Generator(Tuple[RoomStatus, RoomStatus, Tuple[str, ...]], None, None):
        for room_status_change in rooms_status:
            room_status = self.get_room_by_id(room_status_change.id)
            if room_status and room_status != room_status_change:
                room_diffs = tuple(
                    k for k, v in room_status_change.items() if v != room_status.get(k)
                )
                yield (room_status, room_status_change, room_diffs)"""


class RoomsStatus(SequenceObject):
    """List of *room status* objects.

    :param rooms_status: Source list of *room status* items.
    """

    def __init__(self, rooms_status: Sequence[Any]) -> None:
        super().__init__(rooms_status)


class RoomStatus(RoomObject):
    """*Room status* object.

    :param room_status: Source *room status* dict.
    """

    def __init__(self, room_status: Mapping[str, Any]) -> None:
        super().__init__(room_status)


class ModulesStatus(SequenceObject):
    """List of *module status* objects.

    :param modules_status: Source list of *module status* items.
    """

    def __init__(self, modules_status: Sequence[Any]) -> None:
        super().__init__(modules_status)


class ModuleStatus(ModuleObject):
    """*Module status* object.

    :param module_status: Source *module status* dict.
    """

    def __init__(self, module_status: Mapping[str, Any]) -> None:
        super().__init__(module_status)
