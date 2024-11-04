import abc
import logging
from urllib.parse import ParseResult, urlparse
import datetime as dt

import httpx
import re

from event_worker.util import extend_url_path
from event_worker.streamelements.meta import MOCK_URL, Endpoints, ActivityKinds


class Endpoint(abc.ABC):
    def __init__(self, api_url: ParseResult | str, jwt: str, mock: bool = False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mock = mock

        if self.mock:
            self.logger.debug(f"Overwriting api_url with {MOCK_URL}")
            api_url = MOCK_URL

        if not isinstance(api_url, (ParseResult, str)):
            raise TypeError("Url must be supplied as 'str' or 'urllib.parse.ParseResult'")

        if isinstance(api_url, str):
            # drop trailing slash in url
            api_url = api_url[:-1] if api_url[-1] == "/" else api_url
            api_url = urlparse(api_url)

        self._api_url = api_url

        if jwt is None:
            raise ValueError("JWT Token must be supplied")
        self._jwt = jwt

        self.logger.info(f"Constructed API endpoint: {self.url}")

    @property
    def url(self) -> ParseResult:
        return self._api_url._replace(path=self._api_url.path + f"/{self.endpoint}")

    @property
    def headers(self) -> dict:
        headers = {"Accept": "application/json; charset=utf-8",
                   "Authorization": f"Bearer {self._jwt}"}
        if self.mock:
            headers["Prefer"] = "code=200, dynamic=true"
        return headers

    @property
    @abc.abstractmethod
    def endpoint(self) -> str:
        raise NotImplementedError


class GuidEndpoint(Endpoint, abc.ABC):
    _guid = None

    def __init__(self, api_url: ParseResult | str, jwt: str, guid: str, mock: bool = False):
        super().__init__(api_url, jwt, mock=mock)
        self.guid = guid

    @property
    def guid(self) -> str:
        return self._guid

    @guid.setter
    def guid(self, value):
        if re.match("^[0-9a-fA-F]{24}$", value) is None:
            raise ValueError("Guid does not match /^[0-9a-fA-F]{24}$/")
        self._guid = value


class Channels(Endpoint):
    def me(self):
        url = extend_url_path(self.url, "me")
        self.logger.debug(f"Constructed url: {url}")
        response = httpx.get(url=url.geturl(), headers=self.headers)
        response.raise_for_status()
        return response.json()

    @property
    def endpoint(self) -> str:
        return Endpoints.CHANNELS.lower()


class Tips(GuidEndpoint):
    @property
    def endpoint(self) -> str:
        return Endpoints.TIPS.lower()


class Activities(GuidEndpoint):
    @property
    def endpoint(self) -> str:
        return Endpoints.ACTIVITIES.lower()

    def channel(self, after: dt.datetime, before: dt.datetime, limit: int,
                mincheer: int = 0, minhost: int = 0, minsub: int = 0, mintip: int = 0,
                origin: str = "twitch", types: list[ActivityKinds] = None) -> dict:
        url = extend_url_path(self.url, self.guid)
        if types is None:
            types = [type_ for type_ in list(ActivityKinds)]
        types = [type_.value if isinstance(type_, ActivityKinds) else type_
                 for type_ in types]

        params = {
            "after": after.isoformat(),
            "before": before.isoformat(),
            "limit": limit,
            "mincheer": mincheer,
            "minhost": minhost,
            "minsub": minsub,
            "mintip": mintip,
            "origin": origin,
            "types": types
        }

        self.logger.debug(f"Requesting channel activities: {params}")

        response = httpx.get(url.geturl(), headers=self.headers, params=params)
        response.raise_for_status()

        return response.json()

