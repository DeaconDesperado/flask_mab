.. flask_mab documentation master file, created by
   sphinx-quickstart on Mon Oct 28 17:57:57 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to flask_mab's documentation!
=====================================

Flask-MAB is an implementation of multi-armed bandit test pattern as a flask middleware.

It can be used to test the effectiveness of virtually any parts of your app using user signals.

If you can pass it, we can test it!

Multi-armed what?!
------------------

A multi-armed bandit is essentially an online alternative to classical A/B testing.  Whereas 
A/B testing is generally split into extended phases of execution and analysis, Bandit algorithms
continually adjust to user feedback and optimize between experimental states.  Bandits typically
require very little curation and can in fact be left running indefinitely if need be.

The curious sounding name is drawn from the "one-armed bandit", an colloquialism for casino
slot machines.  Bandit algorithms can be thought of along similar lines as a eager slot player:
if one were to play many slot machines continously over many thousands of attempts, one would eventually
be able to determine which machines were hotter than others.  A multi-armed bandit is merely an algorithm 
that performs exactly this determination, using your user's interaction as its "arm pulls".  Extracting winning
patterns becomes a fluid part of interacting with the application.

John Myles White has an awesome treatise on Bandit implementations in his book `Bandit Algorithms for Website Optimization <http://shop.oreilly.com/product/0636920027393.do>`_.

How does it work? 
-----------------

Flask-MAB can be configured with several different bandit strategies for anything you'd like to test. You
can define your tests using the :mod:`flask_mab.bandits` classes.  The different states you'd like to test for are
represented as the "arms" on the bandit.  You can define endpoints that will assign "arms" to users as well as ones that
will register how much "reward" the arm has paid.  The Bandit strategy you select will use these two scalars to adjust its
strategy for assigning arms to new users.  These values are persisted to the client so users can keep a consistent
state between requests (because an app that changed noticeably between requests would be pretty jarring!)

Common examples of good use cases for Bandits include

* Splitting user traffic between different APIs or algorithms (recommender systems)
* Optimizing UI elements for best user experience, such as button colors or navigation placement
* Changing ad copy wording or help text to see if it increases click throughput

.. toctree::
   :maxdepth: 4

   flask_mab


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

