from setuptools import setup

if __name__ == "__main__":
    setup(
        package_data={
            "pysdk": [
                "templates/body_template.jinja",
                "templates/method_template.jinja",
                "templates/import_template.jinja",
            ]
        }
    )
