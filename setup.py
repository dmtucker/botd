#!/usr/bin/env python2
# coding: utf-8

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    README = readme_file.read()

with open('requirements.txt') as requirements_file:
    REQUIREMENTS = requirements_file.read().splitlines()

setup(
    name='botd',
    version='0.1.0',
    description='IRC Bot',
    long_description=README,
    author='David Tucker',
    author_email='david.michael.tucker@gmail.com',
    license='GPLv2+',
    url='https://github.com/dmtucker/botd',
    packages=find_packages(),
    include_package_data=True,
    entry_points={'console_scripts': ['botd = botd.__main__:main']},
    keywords='IRC bot',
    install_requires=REQUIREMENTS,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
