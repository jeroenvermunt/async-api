import asyncio
import random
from pysdk import ApiSDK
from pysdk import return_types


class Cats(ApiSDK):

    endpoints = {
        'image': 'https://http.cat/{status_code}'
    }

    return_type = return_types.IMAGE


class Dogs(ApiSDK):

    endpoints = {
        'image': 'https://http.dog/{status_code}.jpg'
    }

    return_type = return_types.IMAGE


async def cat_and_dog(status_code):

    cats = Cats()
    dogs = Dogs()

    # use taskgroup to run multiple requests concurrently, requires python 3.11
    async with asyncio.TaskGroup() as tg:
        cat_image = tg.create_task(
            cats.image(status_code))

        dog_image = tg.create_task(
            dogs.image(status_code))

    # save images to examples.images
    with open(f'examples/images/cat_{status_code}.jpg', 'wb') as f:
        f.write(cat_image.result())

    with open(f'examples/images/dog_{status_code}.jpg', 'wb') as f:
        f.write(dog_image.result())


async def three_cats():
    
    def random_status_code():
        return random.choice([
            100, 101, 102, 103, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226,
            300, 301, 302, 303, 304, 305, 306, 307, 308, 400, 401, 402, 403, 404,
            405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418,
            421, 422, 423, 424, 425, 426, 428, 429, 431, 451, 500, 501, 502, 503,
            504, 505, 506, 507, 508, 510, 511
        ])

    cats = Cats()

    # use taskgroup to run multiple requests concurrently, requires python 3.11
    async with cats:
        async with asyncio.TaskGroup() as tg:
            cat_one = tg.create_task(
                cats.image(code_1 := random_status_code()))
            
            cat_two = tg.create_task(
                cats.image(code_2 := random_status_code()))
            
            cat_three = tg.create_task(
                cats.image(code_3 := random_status_code()))

    # save images to examples.images
    with open(f'examples/images/cat_{code_1}.jpg', 'wb') as f:
        f.write(cat_one.result())
    
    with open(f'examples/images/cat_{code_2}.jpg', 'wb') as f:
        f.write(cat_two.result())
    
    with open(f'examples/images/cat_{code_3}.jpg', 'wb') as f:
        f.write(cat_three.result())
    
if __name__ == '__main__':
    asyncio.run(cat_and_dog(102))
    asyncio.run(three_cats())
