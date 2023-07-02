import asyncio
from pysdk import ApiSDK


class Cats(ApiSDK):

    endpoints = {
        'image': 'https://http.cat/{status_code}'
    }


class Dogs(ApiSDK):

    endpoints = {
        'image': 'https://http.dog/{status_code}.jpg'
    }


async def main(status_code):

    cats = Cats()
    dogs = Dogs()

    # use taskgroup to run multiple requests concurrently, requires python 3.11
    async with asyncio.TaskGroup() as tg:
        cat_image = tg.create_task(
            cats.image(status_code, return_type='image'))

        dog_image = tg.create_task(
            dogs.image(status_code, return_type='image'))

    # save images to examples.images
    with open(f'examples/images/cat_{status_code}.jpg', 'wb') as f:
        f.write(cat_image.result())

    with open(f'examples/images/dog_{status_code}.jpg', 'wb') as f:
        f.write(dog_image.result())

if __name__ == '__main__':
    asyncio.run(main(102))
