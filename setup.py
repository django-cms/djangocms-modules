import os

from setuptools import setup, find_packages

import djangocms_modules


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
    author='Divio AG',
    author_email='info@divio.ch',
    name='djangocms_modules',
    version=djangocms_modules.__version__,
    description='Adds copy/paste capabilities to groups of plugins',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='http://www.django-cms.org/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'django-parler>=1.2',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
