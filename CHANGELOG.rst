=========
Changelog
=========

v1.0.3
------
- update dependencies
- update readme
- update links to repo in docs

v1.0.2 
------
- fix bug in logging imports 

v1.0.1
------
- more robust pump initialization

v1.0.0
------
- now has a full test suite! 🎉
- can now initialize a :code:`NextGenPump` instance using either a pre-existing :code:`Serial` instance (new behavior), OR by passing in a string for the port to open a :code:`Serial` instance at (old behavior)
- bundled data retrieval methods such as :code:`current_conditions` or :code:`pump_info` now return custom typed :code:`dataclass`es instead of :code:`dict`s (this is a breaking change)
- fixed an elusive bug that would sometimes cause :code:`NextGenPumpBase`'s :code:`identify` to fail

v0.1.7
------
- minor code cleanup / improvement to packaging

v0.1.6
------
- Yet another minor performance improvement to write operations
- Minor performance improvement to read operations
- Cleaning up some code comments

v0.1.5
------
- Minor performance improvement to pump's write operation

v0.1.4
------
- Improved read/write instructions and pump identification

v0.1.3
------
- Improved debug logging
- Improved documentation

v0.1.2
------
- Changed the faulty :code:`leak_mode` property to a write-only :code:`set_leak_mode` instance method
- Improved documentation

v0.1.1
------
Fixed some bad imports, improved documentation

v0.1.0
------
Initial release
