from asyncio import CancelledError, Lock, Queue, create_task, sleep, wait
from copy import deepcopy
from json import dumps, loads
from logging import debug, getLogger
from ssl import SSLContext
from time import time
from typing import AsyncGenerator, Dict, Iterable, NoReturn, Optional, Union

from aiohttp import (
    ClientSession,
    ClientWebSocketResponse,
    Fingerprint,
    TCPConnector,
    WSMessage,
    request,
)
from aiohttp.client_exceptions import ClientConnectorError
from yarl import URL

from ._misc import API_URL, WEBSOCKET_APP_TYPES, WEBSOCKET_URL, logger
from .grant import BaseGrant

"""class Change:
    def __init__(
        self,
        home_data: HomeData,
        home_status: HomeStatus,
        timestamp: Optional[float] = None,
        home_data_change: Optional[HomeData] = None,
        home_status_change: Optional[HomeStatus] = None,
        event: Optional[Event] = None,
    ):
        self._home_data = home_data
        self._home_status = home_status
        self._timestamp = timestamp if timestamp is not None else time()
        self._home_data_change = home_data_change
        self._home_status_change = home_status_change
        self._event = event

    @property
    def home_data(self) -> HomeData:
        return self._home_data

    @property
    def home_status(self) -> HomeStatus:
        return self._home_status

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def home_data_change(self) -> HomeData:
        return self._home_data_change

    @property
    def home_status_change(self) -> HomeStatus:
        return self._home_status_change

    @property
    def event(self) -> Event:
        return self._event

    @property
    def alert(self) -> str:
        return self._alert"""


class Netatmo:
    """Hi-level API class."""

    def __init__(
        self,
        name: str = "",
        url: str = API_URL,
        ssl: Union[None, bool, Fingerprint, SSLContext] = True,
    ) -> None:
        self._name = name
        self._api_url = URL(url)
        # When using websockets with aiohttp, create a client
        # with a connector with the parameter enable_cleanup_closed=True.
        # See aiohttp issue
        # https://github.com/aio-libs/aiohttp/issues/2309
        # in particular see comments from May 12, 2021.
        connector = TCPConnector(ssl=ssl, enable_cleanup_closed=True)
        self._client = ClientSession(connector=connector)
        self._token = None
        # self._homes_data = HomesData([])
        self._homes_status = {}
        self._changes = Queue()

        self._auth_lock = Lock()
        self._auth_task = None
        self._poll_lock = Lock()
        self._poll_task = None
        self._ws_tasks = {}

        self._logger = logger.getChild(
            "netatmo" + (f"-{self._name}" if self._name else "")
        )

    def _url(self, url: str) -> URL:
        return self._api_url.join(URL(url))

    async def _auth_handler(self, grant: BaseGrant) -> NoReturn:
        while True:
            t0 = time()
            try:
                async with self._client.post(
                    self._url("oauth2/token"), data=dict(grant.parameters)
                ) as resp:
                    if resp.status == 200:
                        resp_json = await resp.json()
                        self._token = resp_json["access_token"]
                        expires_in = resp_json["expires_in"]
                        refresh_token = resp_json["refresh_token"]
                        self._logger.info(f"Authenticated with {repr(grant)}")
                        grant = grant.get_refresh_token_grant(refresh_token)
                        await sleep(max(t0 + expires_in - 60 - time(), 1))
                    else:
                        error = (await resp.json())["error"]
                        self._logger.warning(
                            f"Authentication with {repr(grant)} failed ({repr(error)})"
                        )
            except Exception as e:
                self._logger.error(f"Authentication error: {e}")
            await sleep(t0 + 10 - time())

    async def authenticate(self, grant: BaseGrant) -> None:
        async with self._auth_lock:
            if self._auth_task:
                self._auth_task.cancel()
                await wait((self._auth_task,))
            self._auth_task = create_task(self._auth_handler(grant))

    async def polling_start(self, cycle: float = 540) -> None:
        async with self._poll_lock:
            if self._poll_task:
                self.polling_stop()
                await wait((self._poll_task,))
            self._poll_task = create_task(self._poll_handler(cycle))
            self._logger.info(f"Polling started")

    async def _fetch_homesdata(self) -> None:
        params = {"sync_measurements": True}
        headers = {"Authorization": f"Bearer {self._token}"}
        async with self._client.post(
            self._url("api/homesdata"), json=params, headers=headers
        ) as resp:
            if resp.status == 200:
                self._homes_data = (await resp.json())["body"]["homes"]
                from json import dump

                with open("homes_data.json", "w") as f:
                    dump(self._homes_data, f, indent=4)
            else:
                pass  # TODO: something

    async def _fetch_homestatus(self, home_id: bytes) -> None:
        params = {"home_id": home_id.hex()}
        headers = {"Authorization": f"Bearer {self._token}"}
        # Control app uses endpoint syncapi/v1/homestatus and headers
        # {'app_type': 'app_magellan', 'app_version': '1.23.1.0',
        #  'device_types': ['NAPlug', 'BNS', 'NLG', 'NBG', 'TPSG', 'OTH']}
        # maybe device types is selected by current devices in home.
        # Whatever, here can be used public endpoint without selecting types.
        async with self._client.post(
            self._url("api/homestatus"), json=params, headers=headers
        ) as resp:
            if resp.status == 200:
                body = (await resp.json()).get("body")
                if body:
                    home_status = body["home"]
                else:
                    # this state is when installation is offline
                    home_status = HomeStatus({})
                self._homes_status[home_id] = home_status
            else:
                raise  # TODO: something

    async def _poll_handler(self, cycle: int) -> NoReturn:
        while True:
            t0 = time()
            await self._fetch_homesdata()
            for home_data in self._homes_data:
                await self._fetch_homestatus(home_data.id)
            await sleep(t0 + cycle - time())

    def polling_stop(self):
        if self._poll_task:
            self._poll_task.cancel()
            self._logger.info(f"Polling stopped")

    """# TODO: make as a caching method
    @property
    def homes_data(self) -> HomesData:
        return self._homes_data

    # TODO: make as a caching method
    @property
    def homes_status(self) -> Dict[bytes, HomeStatus]:
        return self._homes_status

    def websocket_open(
        self, app_types: Iterable[str] = WEBSOCKET_APP_TYPES, url: str = WEBSOCKET_URL
    ) -> None:
        self._logger.info(f"Opening websockets for {repr(app_types)} on {repr(url)}")
        for app_type in app_types:
            if app_type in self._ws_tasks:
                self._ws_tasks[app_type].cancel()
                del self._ws_tasks[app_type]
            task = create_task(self._ws_handler(app_type, self._url(url)))
            self._ws_tasks[app_type] = task

    async def _ws_handler(self, app_type: str, url: URL) -> NoReturn:
        while True:
            try:
                async with self._client.ws_connect(
                    url, timeout=1, heartbeat=7
                ) as ws:
                    self._logger.debug(f"Websocket for {repr(app_type)} connected")
                    # Legrand/Netatmo apps uses the following additional
                    # parameters:
                    # {'filter': 'silent', 'version': <app version>,
                    #  'platform': 'Android'}
                    # See more in library docs.
                    params = {
                        "access_token": self._token,
                        "app_type": app_type,
                        "action": "Subscribe",
                    }
                    await ws.send_str(dumps(params))
                    self._logger.debug(
                        f"Websocket for {repr(app_type)} subscription sent ({params})"
                    )
                    try:
                        async for msg in ws:
                            await self._ws_msg(msg)
                    finally:
                        self._logger.debug(
                            f"Websocket for {repr(app_type)} is remotely closed"
                        )
            except ClientConnectorError:
                self._logger.debug(f"Websocket for {repr(app_type)} can not connect")
            await sleep(1)

    async def _ws_msg(self, msg: WSMessage) -> None:
        msg_data = loads(msg.data)
        if msg_data.get("type") != "Websocket":
            self._logger.info((f"WS message of unknown type {msg_data}"))
            return
        push_type = msg_data["push_type"].split("-")[0]
        extra_params = msg_data["extra_params"]
        msg_data_ts = msg_data["Timestamp"]
        timestamp = msg_data_ts["sec"] + msg_data_ts["usec"] / 1000000
        if push_type == "embedded_json" or push_type == "display_change":
            home = extra_params["home"]
            # If push_type is 'display_change', modules and rooms
            # contain 'name' and 'type' keys, which do not appear to be
            # in the standard state objects
            for state_array_name in ("modules", "rooms"):
                states = home.get(state_array_name, [])
                if isinstance(states, list):
                    for state in states:
                        for delkey in ("name", "type"):
                            state.pop(delkey, None)
            # Create HomeStatus from json payload
            home_status_json = HomeStatus(home)
            # Store copy of original HomeStatus
            home_status = self.homes_status[home_status_json.id].get_copy()
            # Update self HomeStatus and create difference (which is in most cases same as home_status_json)
            home_status_change = self.homes_status[home_status.id].update_home(
                home_status_json
            )
            change = Change(
                self.homes_data.get_home_by_id(home_status.id).get_copy(),
                home_status,
                timestamp,
                home_status_change=home_status_change,
            )
        elif push_type == "home_event_changed":
            # Create HomeData from json payload
            home_data_json = HomeData(extra_params["home"])
            # Store copy of original HomeData
            home_data = self.homes_data.get_home_by_id(home_data_json.id).get_copy()
            # Update self HomeData and create difference (which is in most cases same as home_data_json)
            home_data_change = self.homes_data.get_home_by_id(home_data.id).update_home(
                home_data_json
            )
            change = Change(
                home_data,
                self.homes_status[home_data.id].get_copy(),
                timestamp,
                home_data_change,
            )
        elif push_type in ("NACamera", "NOC"):
            event = Event(extra_params)
            home_data = self.homes_data.get_home_by_id(event.home_id).get_copy()
            home_status = self.homes_status[event.home_id].get_copy()
            change = Change(home_data, home_status, timestamp, event=event)
        else:
            return
        await self._changes.put(change)

    def websocket_close(self, app_types: Optional[Iterable[str]] = None) -> None:
        if app_types is None:
            app_types = self._ws_tasks.keys()
        for app_type in app_types:
            try:
                self._ws_tasks[app_type].cancel()
            except KeyError:
                raise KeyError(f"Websocket for app_type {repr(app_type)} is not open")

    async def changes(self) -> AsyncGenerator[Change, None]:
        while True:
            yield await self._changes.get()"""
