import asyncio
# import inspect
from pysdk import ApiSDK
from pysdk import return_types
from pydantic import BaseModel, field_validator


# define a pydantic model for the body of our post request
class Amount(BaseModel):

    currency: str = 'EUR'
    value: str  # no default value, meaning it is required to be passed

    @field_validator('value', mode='before')
    def two_decimals(cls, v):
        """
        transforms value into format accepted by mollie
        api with 2 decimals and dot as separator
        """
        return f'{v:.2f}'

    # this might be useful later for generation of a file
    # _classline_ = inspect.currentframe().f_code.co_firstlineno
    # _thisline_ = inspect.currentframe().f_lineno


class BuyMeACoffee(ApiSDK):

    base_url = 'https://api.mollie.com/v2'
    authorization = 'Bearer test_hhPcGuBTrpgezB7UcuKhVnUVBe66yD'

    headers = {
        'Content-Type': 'application/json'
    }

    # define endpoints, notice we can use the pydantic model in the body
    endpoints = {
        'buy_me_a_coffee': {
            'method': 'POST',
            'endpoint': '/payment-links',
            'body': {
                'amount': Amount,
                'description': 'Buy me a coffee',
            },
        },
        'buy_me_another_coffee': {
            'method': 'POST',
            'endpoint': '/payment-links',
            'body': {
                'amount': {
                    'currency': 'EUR',
                    'value': '{amount}'
                },
                'description': 'Buy me a coffee',
            },
        }
    }

    return_type = return_types.JSON

    async def small(self):
        return await self.buy_me_a_coffee(value=2.5)

    async def medium(self):
        return await self.buy_me_a_coffee(value=5)

    async def large(self):
        return await self.buy_me_a_coffee(value=7.5)

    async def custom_size(self, value: float):
        return await self.buy_me_a_coffee(value=value)

    async def another_coffee(self, amount: str):
        return await self.buy_me_another_coffee(amount=amount)


async def buy_me_a_coffee():
    """
    buy me a coffee using the BuyMeACoffee class
    """
    bmac = BuyMeACoffee()

    async with asyncio.TaskGroup() as tg:
        link_small_coffee = tg.create_task(
            bmac.small())

        link_medium_coffee = tg.create_task(
            bmac.medium())

        link_large_coffee = tg.create_task(
            bmac.large())

        link_custom_coffee = tg.create_task(
            bmac.custom_size(100))

    print(link_small_coffee.result())
    print(link_medium_coffee.result())
    print(link_large_coffee.result())
    print(link_custom_coffee.result())

    # another_coffee = await bmac.another_coffee('10.00')
    # # uncomment to see error
    # another_coffee = await bmac.another_coffee(10)
    # another_coffee = await bmac.another_coffee('10')


if __name__ == '__main__':

    asyncio.run(buy_me_a_coffee())

    # Amount(value=2.5)
    # Amount(value=5)
