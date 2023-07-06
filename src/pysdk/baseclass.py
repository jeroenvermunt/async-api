
import json
import aiohttp
import asyncio
import urllib
from pysdk.metaclass import ApiMetaclass


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
        verbose: bool = True
    ):

        self.n_retries = 0
        self.max_retries = max_retries
        self.verbose = verbose

        timeout = aiohttp.ClientTimeout(
                # default value is 5 minutes, set to `None` for unlimited
                total=timeout,
                # How long to wait before an open socket allowed to connect
                sock_connect=timeout,
                # How long to wait with no data being read before timing out
                sock_read=timeout
            )

        self.client_args = dict(
            trust_env=True,
            timeout=timeout
        )

    async def handle_error(self, e, request_func, *args, **kwargs):

        # check exception type
        match e.__class__:
            case aiohttp.ClientConnectorCertificateError:
                raise e
            case aiohttp.ClientError:
                pass
            case asyncio.TimeoutError:
                pass

        if self.n_retries < self.max_retries:
            self.n_retries += 1
            await asyncio.sleep(1)
            return await request_func(*args, **kwargs)

        else:
            raise MaxRetriesError('Max retries reached')     

    async def get(self, url: str, params: dict = None, **kwargs):

        # encode params into string
        if params:
            query_string = urllib.parse.urlencode(params)
            url += '?' + query_string

        try:
            async with (
                aiohttp.ClientSession(**self.client_args) as s,
                s.get(url, headers=self.headers) as r,
            ):
                return await self.parse_response(r, **kwargs)

        except Exception as e: 
            return await self.handle_error(e, self.get, url, **kwargs)

    async def post(self, url, data: dict, **kwargs):

        try:
            async with (
                aiohttp.ClientSession(**self.client_args) as s,
                s.post(url, headers=self.headers, data=json.dumps(data)) as r,
            ):
                return await self.parse_response(r, **kwargs)

        except Exception as e: 
            return await self.handle_error(e, self.get, url, **kwargs)

    async def put(self, url, data: dict, **kwargs):

        try:
            async with (
                aiohttp.ClientSession(**self.client_args) as s,
                s.put(url, headers=self.headers, data=json.dumps(data)) as r,
            ):
                print(r.status)
                return await self.parse_response(r, **kwargs)

        except Exception as e: 
            return await self.handle_error(e, self.get, url, **kwargs)

    async def parse_response(self, response, return_type=None):

        if self.verbose:
            print(response.status)
            print(response.reason)

        if return_type == 'json':
            print('Returning response as json')
            return await response.json()

        elif return_type == 'image':
            print('Returning response as image')
            return await response.read()

        if self.verbose:
            print('Returning response as aiohttp response object')

        return response
