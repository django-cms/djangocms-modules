==================
django CMS Modules
==================

|pypi| |build| |coverage|

**django CMS Modules** adds copy/paste capabilities to groups of plugins.

This addon is compatible with `Divio Cloud <http://divio.com>`_ and is also available on the
`django CMS Marketplace <https://marketplace.django-cms.org/en/addons/browse/djangocms-modules/>`_
for easy installation.

.. image:: preview.gif


Contributing
============

This is a an open-source project. We'll be delighted to receive your
feedback in the form of issues and pull requests. Before submitting your
pull request, please review our `contribution guidelines
<http://docs.django-cms.org/en/latest/contributing/index.html>`_.

We're grateful to all contributors who have helped create and maintain this package.
Contributors are listed at the `contributors <https://github.com/divio/djangocms-modules/graphs/contributors>`_
section.

One of the easiest contributions you can make is helping to translate this addon on
`Transifex <https://www.transifex.com/projects/p/djangocms-modules/>`_.


Documentation
=============

See ``REQUIREMENTS`` in the `setup.py <https://github.com/divio/djangocms-modules/blob/master/setup.py>`_
file for additional dependencies:

|python| |django| |djangocms|


Installation
------------

For a manual install:

* run ``pip install djangocms-modules``
* add ``djangocms_modules`` to your ``INSTALLED_APPS`` **before** ``cms``
* run ``python manage.py migrate djangocms_modules``

In addition, djangocms-modules requires your base template to render the
*Modules* section. By default we assume it is ``base.html``. If you use
a different template structure please adapt `djangocms_modules/base.html <https://github.com/divio/djangocms-modules/blob/master/djangocms_modules/templates/djangocms_modules/base.html#L1>`_
accordingly.


Running Tests
-------------

You can run tests by executing::

    virtualenv env
    source env/bin/activate
    pip install -r tests/requirements.txt
    python setup.py test


.. |pypi| image:: https://badge.fury.io/py/djangocms-modules.svg
    :target: http://badge.fury.io/py/djangocms-modules
.. |build| image:: https://travis-ci.org/divio/djangocms-modules.svg?branch=master
    :target: https://travis-ci.org/divio/djangocms-modules
.. |coverage| image:: https://codecov.io/gh/divio/djangocms-modules/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/divio/djangocms-modules

.. |python| image:: https://img.shields.io/badge/python-2.7%20%7C%203.4+-blue.svg
    :target: https://pypi.org/project/djangocms-modules/
.. |django| image:: https://img.shields.io/badge/django-1.11%20%7C%202.0%20%7C%202.1-blue.svg
    :target: https://www.djangoproject.com/
.. |djangocms| image:: https://img.shields.io/badge/django%20CMS-3.5%2B-blue.svg
    :target: https://www.django-cms.org/
