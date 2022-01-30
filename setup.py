"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""


import codecs
import os.path

import setuptools


def read(*parts: str) -> str:
    """Read a file in this repository."""
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, *parts), "r") as file_:
        return file_.read()


ENTRY_POINTS = {"console_scripts": ["botd = botd.__main__:main"]}


if __name__ == "__main__":
    setuptools.setup(
        name="botd",
        description="IRC Bot",
        long_description=read("README.rst"),
        long_description_content_type="text/x-rst",
        author="David Tucker",
        author_email="david@tucker.name",
        license="LGPLv2+",
        url="https://pypi.org/project/botd",
        project_urls={
            "Code": "https://github.com/dmtucker/botd",
            "Documentation": "https://dmtucker.github.io/botd",
            "Issues": "https://github.com/dmtucker/botd/issues",
        },
        package_dir={"": "src"},
        packages=setuptools.find_packages("src"),
        include_package_data=True,
        setup_requires=["setuptools_scm[toml] >= 6.0"],
        python_requires=">= 3.9",
        install_requires=[
            "passlib >= 1.7",
            "twisted[tls] >= 22.1",
        ],
        entry_points=ENTRY_POINTS,
        classifiers=[
            "Intended Audience :: End Users/Desktop",
            "Programming Language :: Python :: 3.9",
        ],
    )
