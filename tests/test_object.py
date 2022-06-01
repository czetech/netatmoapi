from datetime import datetime, time, timedelta
from datetime import timezone as datetime_timezone
from json import load
from pathlib import Path

from pytest import fixture, raises
from pytz import timezone, utc

from netatmoapi.object import (
    HomeData,
    HomesData,
    HomeStatus,
    ModuleData,
    ModulesData,
    ObjectError,
    ObjectIdError,
    RoomData,
    RoomsData,
    Schedule,
    Schedules,
    Timepoint,
    Timetable,
    Zone,
    Zones,
)


@fixture
def json_homes_data():
    with open(Path(__file__).with_name("homes_data.json")) as f:
        return load(f)


@fixture
def homes_data(json_homes_data):
    return HomesData(json_homes_data)


@fixture
def home_data(json_homes_data):
    return HomeData(json_homes_data[0])


@fixture
def rooms_data(json_homes_data):
    return RoomsData(json_homes_data[0]["rooms"])


@fixture
def room_data(json_homes_data):
    return RoomData(json_homes_data[0]["rooms"][0])


@fixture
def modules_data(json_homes_data):
    return ModulesData(json_homes_data[0]["modules"])


@fixture
def module_data(json_homes_data):
    return ModuleData(json_homes_data[0]["modules"][0])


@fixture
def schedules(json_homes_data):
    return Schedules(json_homes_data[0]["schedules"], timezone("Europe/Vienna"))


@fixture
def schedule(json_homes_data):
    return Schedule(json_homes_data[0]["schedules"][0], timezone("Europe/Vienna"))


@fixture
def timetable(json_homes_data):
    return Timetable(
        json_homes_data[0]["schedules"][0]["timetable"], timezone("Europe/Vienna")
    )


@fixture
def timepoint(json_homes_data):
    return Timepoint(
        json_homes_data[0]["schedules"][0]["timetable"][0], timezone("Europe/Vienna")
    )


@fixture
def zones(json_homes_data):
    return Zones(json_homes_data[0]["schedules"][0]["zones"])


@fixture
def zone(json_homes_data):
    return Zone(json_homes_data[0]["schedules"][0]["zones"][0])


@fixture
def json_home_status():
    with open(Path(__file__).with_name("home_status.json")) as f:
        return load(f)


def test_homes_data_get(homes_data):
    assert isinstance(
        homes_data.get(b"\x60\x47\x8d\x1b\xaf\x36\xee\x03\x2f\x3e\x00\x70"), HomeData
    )
    assert homes_data.get(b"\x00" * 12) is None


def test_homes_data_copy(homes_data):
    assert isinstance(homes_data.copy(), HomesData)


def test_home_data_id(home_data):
    assert home_data.id == b"\x60\x47\x8d\x1b\xaf\x36\xee\x03\x2f\x3e\x00\x70"
    del home_data["id"]
    with raises(ObjectMissingIdError):
        home_data.id
    home_data["id"] = None
    with raises(ObjectError):
        home_data.id


def test_home_data_name(home_data):
    assert home_data.name == "NetatmoAPI Lab"
    del home_data["name"]
    assert home_data.name is None
    home_data["name"] = None
    with raises(ObjectError):
        home_data.name


def test_home_data_timezone(home_data):
    assert home_data.timezone == timezone("Europe/Vienna")
    home_data["timezone"] = "Nowhere/Nowhere"
    with raises(ObjectError):
        home_data.timezone


def test_home_data_rooms(home_data):
    assert isinstance(home_data.rooms, RoomsData)


def test_home_data_modules(home_data):
    assert isinstance(home_data.modules, ModulesData)


def test_home_data_therm_schedules(home_data):
    assert isinstance(home_data.therm_schedules, Schedules)


def test_home_data_schedules(home_data):
    assert isinstance(home_data.schedules, Schedules)


def test_rooms_data_get(rooms_data):
    assert isinstance(rooms_data.get(1914591590), RoomData)
    assert rooms_data.get(0) is None


def test_room_data_id(room_data):
    assert room_data.id == 1914591590
    del room_data["id"]
    with raises(ObjectMissingIdError):
        room_data.id
    room_data["id"] = None
    with raises(ObjectError):
        room_data.id


def test_room_data_name(room_data):
    assert room_data.name == "Electrical Cabinet"


def test_modules_data_get(modules_data):
    assert isinstance(modules_data.get(b"\x00\x03\x50\xb7\x71\xbe"), ModuleData)
    assert modules_data.get(b"\x00" * 6) is None


def test_module_data_id(module_data):
    assert module_data.id == b"\x00\x03\x50\xb7\x71\xbe"
    del module_data["id"]
    with raises(ObjectMissingIdError):
        module_data.id
    module_data["id"] = None
    with raises(ObjectError):
        module_data.id


def test_module_data_name(module_data):
    assert module_data.name == "Smarther Thermostat"


def test_module_data_room_id(module_data):
    assert module_data.room_id == 2389428768
    del module_data["room_id"]
    assert module_data.room_id is None
    module_data["room_id"] = None
    with raises(ObjectError):
        module_data.room_id


def test_schedules_get(schedules):
    assert isinstance(
        schedules.get(b"\x60\x47\x90\x03\x0b\x9b\x64\x57\xa9\x5a\xc5\x4b"), Schedule
    )
    assert schedules.get(b"\x00" * 12) is None


def test_schedule_id(schedule):
    assert schedule.id == b"\x60\x47\x90\x03\x0b\x9b\x64\x57\xa9\x5a\xc5\x4b"
    del schedule["id"]
    with raises(ObjectMissingIdError):
        schedule.id
    schedule["id"] = None
    with raises(ObjectError):
        schedule.id


def test_schedule_timetable(schedule):
    assert isinstance(schedule.timetable, Timetable)


def test_schedule_zones(schedule):
    assert isinstance(schedule.zones, Zones)


def test_schedule_name(schedule):
    assert schedule.name == "Heating"


def test_schedule_selected(schedule):
    assert schedule.selected


def test_schedule_type(schedule):
    assert schedule.name == "therm"


def test_timetable_get(timetable):
    assert isinstance(timetable.get(0), Timepoint)
    assert timetable.get(26) is None


def test_timepoint_zone_id(timepoint):
    assert timepoint.zone_id == 1


def test_timepoint_m_offset(timepoint):
    assert timepoint.m_offset == 0


def test_timepoint_get_timedelta(timepoint):
    assert timepoint.get_timedelta() == timedelta(0)


def test_timepoint_get_datetime(timepoint):
    # Standard library timezone.
    dt = datetime(2022, 4, 4, tzinfo=datetime_timezone(timedelta(seconds=7200)))
    assert timepoint.get_datetime(dt) == dt

    # pytz timezone.
    dt = timezone("Europe/Vienna").localize(datetime(2022, 4, 4))
    assert timepoint.get_datetime(dt) == dt

    # Different time zones.
    assert timepoint.get_datetime(
        datetime(2022, 4, 3, 22, tzinfo=utc), True
    ) == timezone("Europe/Vienna").localize(datetime(2022, 4, 4))

    # A week in the desired week time zone differs from a week in the home time zone.
    assert timepoint.get_datetime(datetime(2022, 4, 4, tzinfo=utc)) == datetime(
        2022, 4, 3, 22, tzinfo=utc
    )
    dt = datetime(2022, 4, 3, 22, tzinfo=utc)
    assert timepoint.get_datetime(dt) == datetime(2022, 4, 4, 21, tzinfo=utc)


def test_zones_get(zones):
    assert isinstance(zones.get(0), Zone)
    assert zones.get(5) is None


def test_zone_id(zone):
    assert zone.id == 0
    del zone["id"]
    with raises(ObjectMissingIdError):
        zone.id
    zone["id"] = None
    with raises(ObjectError):
        zone.id


def test_zone_name(zone):
    assert zone.name == "Comfort"
