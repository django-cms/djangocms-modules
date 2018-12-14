#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

from djangocms_modules import __version__


REQUIREMENTS = [
    'django-cms>=3.4.5',
]


CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
]

setup(
    name='djangocms-modules',
    version=__version__,
    author='Divio AG',
    author_email='info@divio.ch',
    url='https://github.com/divio/djangocms-modules',
    license='BSD',
    description=('Adds copy/paste capabilities to groups of plugins'),
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    classifiers=CLASSIFIERS,
    test_suite='tests.settings.run',
)
