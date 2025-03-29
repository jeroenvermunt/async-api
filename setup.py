from setuptools import setup

if __name__ == "__main__":
    setup(
        package_data={
<<<<<<< HEAD
            'pysdk': [
                'method_template.jinja',
                'import_template.jinja',
                'body_template.jinja'
            ],
=======
            "pysdk": [
                "templates/body_template.jinja",
                "templates/method_template.jinja",
                "templates/import_template.jinja",
            ]
>>>>>>> d04e59e (black formatting)
        }
    )
