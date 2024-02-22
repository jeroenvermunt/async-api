from setuptools import setup


if __name__ == '__main__':
    setup(
        package_data={
            'pysdk': [
                'method_template.jinja',
                'import_template.jinja',
                'body_template.jinja'
            ],
        }
    )
