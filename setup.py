"""
Flask-MAB
-------------

An implementation of the multi-armed bandit optimization pattern as a Flask extension
If you can pass it, we can test it
"""
from setuptools import setup

setup(
    name='Flask-MAB',
    version='0.9.2',
    url='http://github.com/deacondesperado/flask-mab',
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

