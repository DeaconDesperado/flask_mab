Caveats
=======

* At present, this is very, very young code in an alpha state.  If you encounter issues, please file an issue at `GitHub <http://github.com/deacondesperado/flask_mab/issues>`_.
* At present, only one storage backend is available that persists to a JSON file.  More implementations (MongoDB, ZODB) are planned.
* Because of the way the bandit configuration is persisted to file, if you change your bandit setup in your app, be sure to delete your json storage file.
  This **will reset** your bandit counters, so manually change them back if needed.  If you do lose your counters don't worry, it'll only be matter of time before the 
  bandits coverge to the winner again =)
