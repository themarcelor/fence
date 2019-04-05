from setuptools import setup, find_packages

setup(
    name="fence",
    version="0.2.0",
    scripts=["bin/fence-create"],
    packages=find_packages(),
)
