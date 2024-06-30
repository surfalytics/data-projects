from setuptools import find_packages, setup


test_packages = [
    "pytest<7,>=5",
    "pytest-timeout",
]

setup(
    name="ml-logs-transformer",
    version="1.0.0",
    author="Devskiller.com",
    author_email="support@devskiller.com",
    packages=find_packages(),
    install_requires=[
        "pyspark==3.0.0",
        "pyspark-stubs==3.0.0.post1",
        "importlib_resources>=5.12, <6.0",
    ],
    tests_require=test_packages,
    setup_requires=["pytest-runner"],
    extras_require={"dev": ["black"]},
)
