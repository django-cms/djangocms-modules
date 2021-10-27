==================
django CMS Modules
==================

|pypi| |build| |coverage|

**django CMS Modules** adds copy/paste capabilities to groups of plugins.

.. note:: 
        
        This project is endorsed by the `django CMS Association <https://www.django-cms.org/en/about-us/>`_.
        That means that it is officially accepted by the dCA as being in line with our roadmap vision and development/plugin policy. 
        Join us on `Slack <https://www.django-cms.org/slack/>`_.

.. image:: preview.gif

*******************************************
Contribute to this project and win rewards
*******************************************

Because this is a an open-source project, we welcome everyone to
`get involved in the project <https://www.django-cms.org/en/contribute/>`_ and
`receive a reward <https://www.django-cms.org/en/bounty-program/>`_ for their contribution. 
Become part of a fantastic community and help us make django CMS the best CMS in the world.   

We'll be delighted to receive your
feedback in the form of issues and pull requests. Before submitting your
pull request, please review our `contribution guidelines
<http://docs.django-cms.org/en/latest/contributing/index.html>`_.

We're grateful to all contributors who have helped create and maintain this package.
Contributors are listed at the `contributors <https://github.com/django-cms/djangocms-modules/graphs/contributors>`_
section.

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

.. |python| image:: https://img.shields.io/badge/python-3.5+-blue.svg
    :target: https://pypi.org/project/djangocms-modules/
.. |django| image:: https://img.shields.io/badge/django-2.2,%203.0,%203.1-blue.svg
    :target: https://www.djangoproject.com/
.. |djangocms| image:: https://img.shields.io/badge/django%20CMS-3.7%2B-blue.svg
    :target: https://www.django-cms.org/
