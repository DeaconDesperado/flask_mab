"""
Flask-MAB
-------------

An implementation of the multi-armed bandit optimization pattern as a Flask extension
If you can pass it, we can test it
"""
from setuptools import setup

setup(
    name='Flask-MAB',
    version='2.0.0',
    url='http://github.com/deacondesperado/flask_mab',
    license='BSD',
    author='Mark Grey',
    author_email='mark.asperia@gmail.com',
    description='Multi-armed bandits for flask',
    long_description=__doc__,
    packages=['flask_mab'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask'
    ],
    setup_requires = [
        'nose>=1.2.0',
        'coverage>=3.7.0',
        'mock>=1.0.0'
    ],
    test_suite='nose.collector',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

