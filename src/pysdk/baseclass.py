import asyncio
import json
import logging
import urllib
from pprint import pformat
from typing import Optional, Union

import aiohttp

from pysdk.metaclass import ApiMetaclass
from pysdk.restricted_parameters import return_types
from pysdk.utils import format_trace, xray


class MaxRetriesError(Exception):
    pass


class ApiBase(metaclass=ApiMetaclass):
    """base class for async api calls

    feature: add decorator which calls the correct endpoint
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 10,
        retry_delay: int = 1,
        verbose: bool = True,
        log_level: Optional[Union[str, int]] = None,
        **client_kwargs,
    ):
        self.n_retries = 0
        self.max_retries = max_retries
        self.verbose = verbose
        self.session = None
        self.open_contexts = 0
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(self.__class__.__name__)

        if verbose and not log_level:
            log_level = logging.INFO

        if log_level:
            # ch = logging.StreamHandler()
            # ch.setLevel(log_level)
            # self.logger.addHandler(ch)
            self.logger.setLevel(log_level)

        timeout = aiohttp.ClientTimeout(
            # default value is 5 minutes, set to `None` for unlimited
            total=timeout,
            # How long to wait before an open socket allowed to connect
            sock_connect=timeout,
            # How long to wait with no data being read before timing out
            sock_read=timeout,
        )

        self.client_args = dict(trust_env=True, timeout=timeout, **client_kwargs)

        if not hasattr(self, "headers"):
            self.headers: dict = {}

        if not hasattr(self, "return_type"):
            self.return_type: str = ""

    def __enter__(self):
        raise NotImplementedError("Use async context manager instead")

    def __exit__(self, exc_type, exc, tb):
        raise NotImplementedError("Use async context manager instead")

    async def __aenter__(self):
        self.open_contexts = self.open_contexts + 1
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(**self.client_args)
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        self.open_contexts = self.open_contexts - 1
        if self.open_contexts == 0:
            await self.session.close()

    async def handle_error(self, e, request_func, *args, **kwargs):
        # check exception type
        match e.__class__:
            case aiohttp.ClientConnectorCertificateError():
                # raise certificate error, no use to retry
                raise e

            case aiohttp.ClientError():
                pass
            case asyncio.TimeoutError():
                pass

            # if no match (unexpected), raise the exception
            case _:
                raise e

        if self.n_retries < self.max_retries:
            self.n_retries += 1
            await asyncio.sleep(self.retry_delay)
            return await request_func(*args, **kwargs)

        else:
            raise MaxRetriesError("Max retries reached")

    async def _send_request(
        self,
        method: str,
        url: str,
        *,
        params: dict = None,
        data: dict = None,
        allow_redirects: bool = True,
        **kwargs,
    ):
        """send a async request to the api,

        performs:
            - url encoding
            - retries
            - error handling
            - response parsing
            - opens/closes a session if not already open,
              only use when sending one request at a time
              with this class

        Args:
            url: Url to call
            params: Query parameters to be added to the url

        Returns:
            output of self.parse_response:
        """

        # encode query parameters into the url
        if params:
            query_string = urllib.parse.urlencode(params)

            if "?" in url:
                url += "&" + query_string
            else:
                url += "?" + query_string

        self.logger.debug(format_trace("Method", method.upper()))
        self.logger.debug(xray(url))

        print(data)

        # open a session if not already open and send request
        try:
            async with (
                self as s,
                getattr(s, method)(
                    url,
                    data=json.dumps(data) if data else None,
                    headers=self.headers,
                    allow_redirects=allow_redirects,
                ) as r,
            ):
                return await self.parse_response(r, **kwargs)

        # catch all exceptions and parse in handle_error
        except Exception as e:
            return await self.handle_error(e, getattr(self, method), url, **kwargs)

    async def get(
        self, url: str, *, allow_redirects: bool = True, params: dict = None, **kwargs
    ):
        return await self._send_request(
            "get", url, params=params, allow_redirects=allow_redirects, **kwargs
        )

    async def post(self, url: str, *, data: dict = None, params: dict = None, **kwargs):
        return await self._send_request("post", url, data=data, params=params, **kwargs)

    async def put(self, url: str, *, data: dict = None, params: dict = None, **kwargs):
        return await self._send_request("put", url, data=data, params=params, **kwargs)

    async def delete(self, url: str, *, params: dict = None, **kwargs):
        return await self._send_request("delete", url, params=params, **kwargs)

    async def head(
        self, url: str, *, allow_redirects: bool = False, params: dict = None, **kwargs
    ):
        return await self._send_request(
            "head", url, allow_redirects=allow_redirects, params=params, **kwargs
        )

    async def options(
        self, url: str, *, allow_redirects: bool = True, params: dict = None, **kwargs
    ):
        return await self._send_request(
            "options", url, allow_redirects=allow_redirects, params=params, **kwargs
        )

    async def patch(
        self, url: str, *, data: dict = None, params: dict = None, **kwargs
    ):
        return await self._send_request(
            "patch", url, data=data, params=params, **kwargs
        )

    async def parse_response(self, response, return_type=None):
        """

        TODO: Handle aiohttp.client_exceptions.ContentTypeError

        Args:
            response (_type_): _description_
            return_type (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """

        # use class default if type is not specified in request
        if not return_type:
            return_type = self.return_type

        self.logger.info(xray(response.status))
        self.logger.info(xray(response.reason))

        if return_type == return_types.JSON or return_type == "json":
            self.logger.info("Returning response as json")
            response = await response.json()
            self.logger.debug(format_trace("Response", pformat(response)))
            return response

        elif return_type == return_types.IMAGE or return_type == "image":
            self.logger.info("Returning response as image")
            return await response.read()

        if self.verbose:
            self.logger.info("Returning response as aiohttp response object")

        return response
