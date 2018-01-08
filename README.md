Sleep
=====
The Sleep block will delay signals from being emitted for a configured interval of time.

Properties
----------
- **backup_interval**: An interval of time that specifies how often persisted data is saved.
- **interval**: How long to wait before emitting signals.
- **load_from_persistence**: If `True`, the block’s state will be saved when the block is stopped, and reloaded once the block is restarted.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Same list of signals after specified time 'interval'.

Commands
--------
None

Dependencies
------------
None

