Changelog/Roadmap
=======================

Changelog
------------

1.1.1
~~~~~
* Moved references to storage off app instance
* Added support for debug toolbar
* Adopted canonical versioning

1.1.0
~~~~~
* Fixed false positive bug on routes with more than one reward or choose decorator.
* NaiveStochasticBandit
* SoftmaxBandit
* AnnealingSoftmaxBandit
* Still better test coverage

1.0.0
~~~~~
* Significant API overhaul to support the init_app pattern in Flask properly
* First major release

0.9.2
~~~~~
* Working file persistence over JSON, API improvements
* EpsilonGreedyBandit

0.9
~~~~~
* Initial prelease

Roadmap
--------

The following features are planned for the next immediate releases

* Additional storage engines (Mongo and ZODB specifically)
* "Rolling" storage engines to support building visualizations such as histograms from 
  continous log data
* An administrative endpoint with Bandit stats and graphs (probably secured by flask admin)
* UCBBandit 
