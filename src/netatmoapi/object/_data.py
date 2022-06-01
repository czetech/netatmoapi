from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, time, timedelta, tzinfo
from math import copysign
from typing import Any, Generator, Iterable, Optional, Tuple

from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError
from pytz.tzinfo import DstTzInfo

from ._common import (
    HomeObject,
    MappingObject,
    ModuleObject,
    ObjectError,
    ObjectIdError,
    RoomObject,
    SequenceObject,
)


def _dt_add_days(dt, days):
    return _dt_localize(
        datetime.combine(dt.date() + timedelta(days=days), dt.time()), dt.tzinfo
    )


def _dt_localize(dt, tz):
    if isinstance(tz, DstTzInfo):
        return tz.localize(dt)
    else:
        return dt.replace(tzinfo=tz)


class HomesData(SequenceObject):
    """List of *home data* objects.

    :param homes_data: Source list of *home data* items.
    """

    def __init__(self, homes_data: Sequence[Any]) -> None:
        super().__init__(homes_data)

    def get_id(self, home_id: bytes) -> Optional[HomeData]:
        """Get *home data* by ID.

        :param home_id: *Home data* ID.
        """
        for home_data in (HomeData(item) for item in self):
            if home_data.id == home_id:
                return home_data


class HomeData(HomeObject):
    """*Home data* object.

    :param home_data: Source *home data* dict.
    """

    def __init__(self, home_data: Mapping[str, Any]) -> None:
        super().__init__(home_data)

    @property
    def name(self) -> Optional[str]:
        """*Home* name."""
        return self._get_str("name")

    @property
    def timezone(self) -> Optional[DstTzInfo]:
        """*Home* time zone."""
        try:
            timezone_value = self._get_str("timezone")
            return None if timezone_value is None else timezone(timezone_value)
        except UnknownTimeZoneError:
            raise ObjectError(f"Unknown time zone '{timezone_value}'") from None

    @property
    def rooms(self) -> RoomsData:
        """*Home* rooms."""
        return RoomsData(self.get("rooms", []))

    @property
    def modules(self) -> ModulesData:
        """*Home* modules."""
        return ModulesData(self.get("modules", []))

    @property
    def therm_schedules(self) -> Schedules:
        """*Home* therm schedules."""
        return Schedules(self.get("therm_schedules", []), self.timezone)

    @property
    def schedules(self) -> Schedules:
        """*Home* schedules."""
        return Schedules(self.get("schedules", []), self.timezone)


class RoomsData(SequenceObject):
    """List of *room data* objects.

    :param rooms_data: Source list of *room data* items.
    """

    def __init__(self, rooms_data: Sequence[Any]) -> None:
        super().__init__(rooms_data)

    def get_id(self, room_id: int) -> Optional[HomeData]:
        """Get *room data* by ID.

        :param room_id: *Room* ID.
        """
        for room_data in self:
            room_data = RoomData(room_data)
            if room_data.id == room_id:
                return room_data


class RoomData(RoomObject):
    """*Room data* object.

    :param room_data: Source *room data* dict.
    """

    def __init__(self, room_data: Mapping[str, Any]) -> None:
        super().__init__(room_data)

    @property
    def name(self) -> Optional[str]:
        """*Room* name."""
        return self._get_str("name")


class ModulesData(SequenceObject):
    """List of *module data* objects.

    :param modules_data: Source list of *module data* items.
    """

    def __init__(self, modules_data: Sequence[Any]) -> None:
        super().__init__(modules_data)

    def get_id(self, module_id: bytes) -> Optional[HomeData]:
        """Get *module data* by ID.

        :param module_id: *Module* ID.
        """
        for module_data in self:
            module_data = ModuleData(module_data)
            if module_data.id == module_id:
                return module_data


class ModuleData(ModuleObject):
    """*Module data* object.

    :param module_data: Source *module data* dict.
    """

    def __init__(self, module_data: Mapping[str, Any]) -> None:
        super().__init__(module_data)

    @property
    def name(self) -> Optional[str]:
        """*Module* name."""
        return self._get_str("name")

    @property
    def room_id(self) -> Optional[int]:
        """*Module* room ID."""
        return self._get_int("room_id")


class Schedules(SequenceObject):
    """List of *schedule* objects.

    :param schedules: Source list of *schedule* items.
    :param timezone: Time zone of parent *home* object.
    """

    def __init__(self, schedules: Sequence[Any], timezone: tzinfo) -> None:
        super().__init__(schedules)
        self._timezone = timezone

    def get_id(self, schedule_id: bytes) -> Optional[Schedule]:
        """Get *schedule* by ID.

        :param schedule_id: *Schedule* ID.
        """
        for schedule in self:
            schedule = Schedule(schedule, self._timezone)
            if schedule.id == schedule_id:
                return schedule


class Schedule(MappingObject):
    """*Schedule* object.

    :param schedule: Source *schedule* dict.
    :param timezone: Time zone of parent *home* object.
    """

    def __init__(self, schedule: Mapping[str, Any], timezone: tzinfo) -> None:
        super().__init__(schedule)
        self._timezone = timezone

    @property
    def id(self) -> bytes:
        """*Schedule* ID as bytes."""
        try:
            return bytes.fromhex(self._get_str("id"))
        except ValueError:
            raise ObjectIdError(self) from None

    @property
    def timetable(self) -> Timetable:
        return Timetable(self.get("timetable", []), self._timezone)

    @property
    def zones(self) -> Zones:
        return Zones(self.get("zones", []))

    @property
    def name(self) -> Optional[str]:
        """*Schedule* name."""
        return self._get_str("name")

    @property
    def selected(self) -> Optional[bool]:
        """*Schedule* selected."""
        return self._get_bool("selected")

    @property
    def type(self) -> Optional[str]:
        """*Schedule* type."""
        return self._get_str("type")

    def get_zone_by_datetime(self, dt: datetime) -> Optional[Zone]:
        timepoint = self.get_timepoint_by_datetime(dt)
        return self.get_zone_by_id(timepoint.zone_id) if timepoint else None

    def get_week(
        self, week: datetime, home_tz: bool = False
    ) -> Tuple[Tuple[datetime, Zone]]:
        for datetime_, timepoint in self.get_week_timepoints(week, home_tz):
            yield (datetime_, self.get_zone_by_id(timepoint.zone_id))

    def get_period(
        self,
        dt_from: datetime = datetime.min,
        dt_to: datetime = datetime.max,
        count_max: Optional[int] = None,
        home_tz: bool = False,
    ) -> Generator[Tuple[datetime, Zone], None, None]:
        for datetime_, timepoint in self.get_period_timepoints(
            dt_from, dt_to, count_max, home_tz
        ):
            yield (datetime_, self.get_zone_by_id(timepoint.zone_id))


class Timetable(SequenceObject):
    """*Timetable* object.

    :param timetable: Source *timetable* list.
    """

    def __init__(self, timetable: Sequence[Any], timezone: tzinfo) -> None:
        super().__init__(timetable)
        self._timezone = timezone

    def get_index(self, timepoint_index: int) -> Optional[Timepoint]:
        """Get *timepoint* by index.

        :param timepoint_index: *Timepoint* index.
        """
        try:
            return Timepoint(self[timepoint_index], self._timezone)
        except IndexError:
            return None

    def get_by_datetime(self, dt: datetime) -> Optional[Timepoint]:
        if dt.tzinfo is None:
            raise ValueError("Datetime must be aware")
        week_timepoints = self.get_week_timepoints(dt)
        timepoint_previous = None
        for datetime_, timepoint in week_timepoints:
            if datetime_ > dt:
                return timepoint_previous or week_timepoints[-1][1]
            timepoint_previous = timepoint
        return timepoint_previous

    def get_week(
        self, week: datetime, home_tz: bool = False
    ) -> Tuple[Tuple[datetime, Timepoint]]:
        if week.tzinfo is None:
            raise ValueError("week must be aware datetime")
        week_timepoints = [
            (timepoint.get_datetime(week, home_tz), timepoint)
            for timepoint in self.timetable
        ]
        # Do not use first timepoint if it is considered a slot (if schedule
        # is therm or cooling type) and points to the same zone as the last
        # timepoint. It practically means that the last Sunday zone continues
        # Monday after midnight.
        if self.type in ("therm", "cooling"):
            if not week_timepoints:
                ValueError("Schedule has invalid timetable")
            if week_timepoints[0][1].zone_id == week_timepoints[-1][1].zone_id:
                del week_timepoints[0]
        week_timepoints.sort(key=lambda x: x[0])
        return tuple(week_timepoints)

    def get_period(
        self,
        dt_from: datetime = datetime.min,
        dt_to: datetime = datetime.max,
        count_max: Optional[int] = None,
        home_tz: bool = False,
    ) -> Generator[Tuple[datetime, Timepoint], None, None]:
        if dt_from.tzinfo is None or dt_to.tzinfo is None:
            raise ValueError("dt_from and dt_to must be aware datetimes")
        week = dt_from
        count = 0
        while True:
            for datetime_, timepoint in self.get_week_timepoints(week, home_tz):
                if count == count_max or datetime_ > dt_to:
                    return
                if datetime_ < dt_from:
                    continue
                yield (datetime_, timepoint)
                count += 1
            if not count:
                return
            week = _dt_add_days(week, 7)


class Timepoint(MappingObject):
    """*Timepoint* object.

    :param timepoint: Source *timepoint* dict.
    :param timezone: Time zone of parent *home* object.
    """

    def __init__(self, timepoint: Mapping[str, Any], timezone: tzinfo) -> None:
        super().__init__(timepoint)
        self._timezone = timezone

    @property
    def zone_id(self) -> Optional[int]:
        """*Timepoint* zone ID."""
        return self._get_int("zone_id")

    @property
    def m_offset(self) -> Optional[int]:
        """*Timepoint* minute offset."""
        return self._get_int("m_offset")

    def get_timedelta(self) -> timedelta:
        """*Timepoint* timedelta since the start of the week."""
        return timedelta(minutes=self.m_offset)

    def get_datetime(self, week: datetime, home_timezone: bool = False) -> datetime:
        """Datetime of the *timepoint* in the desired week.

        The beginning and end of the week is determined by the time zone of the *home*.

        :param week: Desired week (it can be any aware datetime in a given week).
        :param home_timezone: True for the returned datetime in the *home* time zone,
            otherwise the time zone of the week is used.
        """
        if week.tzinfo is None:
            raise ValueError("Week must be aware datetime")
        week_timezone = week.tzinfo
        week = week.astimezone(self._timezone)
        # The beginning of the desired week.
        week_start = _dt_localize(
            datetime.combine(week.date() + timedelta(days=-week.weekday()), time()),
            week.tzinfo,
        )
        td = self.get_timedelta()
        # Timepoint's naive datetime in desired week. Timepoint's offset is
        # naive so DST cannot be taken into account there.
        dt = datetime.combine(
            week_start.date() + timedelta(days=td.days),
            time(hour=td.seconds // 3600, minute=td.seconds // 60 % 60),
        )
        # Convert datetime to aware in local (home) timezone with support
        # for pytz timezones.
        dt = _dt_localize(dt, self._timezone)
        # Move datetime that comes out of the desired week due to different
        # timezone.
        # if dt < week_start:
        #    dt = _dt_add_days(dt, 7)
        # elif dt > week_end:
        #    dt = _dt_add_days(dt, -7)
        return dt if home_timezone else dt.astimezone(week_timezone)


class Zones(SequenceObject):
    """List of *zone* objects.

    :param zones: Source list of *zone* items.
    """

    def __init__(self, zones: Sequence[Any]) -> None:
        super().__init__(zones)

    def get_id(self, zone_id: int) -> Optional[Zone]:
        """Get *zone* by ID.

        :param zone_id: *Zone* ID.
        """
        for zone in self:
            zone = Zone(zone)
            if zone.id == zone_id:
                return zone


class Zone(MappingObject):
    """*Zone* object.

    :param zone: Source *zone* dict.
    """

    def __init__(self, zone: Mapping[str, Any]) -> None:
        super().__init__(zone)

    @property
    def id(self) -> int:
        """*Zone* ID as integer."""
        try:
            return self._get_int("id")
        except ValueError:
            raise ObjectIdError(self) from None

    @property
    def name(self) -> Optional[str]:
        """*Zone* name."""
        return self._get_str("name")
