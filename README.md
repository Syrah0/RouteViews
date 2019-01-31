# RouteViews

The version of python used for the `routechanges` and `test` modules is
**python 3.6.5**. These modules also attempt to follow the [PEP8][pep8] style
guide.

[pep8]: https://www.python.org/dev/peps/pep-0008/


## Testing

Testing is done using the `unittest` module from the python standard library.
To run all tests use the next command from the project root folder:

	python -m unittest

To run a specific test file, for example `test_change_detector.py` use:

	python -m unittest test/test_change_detector.py

Find more information [here][unittest]

[unittest]: https://docs.python.org/3.6/library/unittest.html


## routechanges module

Every library used in the `routechanges` module comes from the python standard
library.

The `routechanges` package contains the `change_detector` module that has
the `detect_changes()` function, which is explained next.

### change_detector.detect_changes(file_t1, file_t2, output_file=None)

This function receives two files of BGP routes for times t1 and t2 and prints
the changes in routes of `file_t2` respect to `file_t1` to the specified
`output_file`, if output_file is `None` then `sys.stdout` will be used. The
changes are printed in order by network from highest to lowest ip and mask,
where for every change detected the format is the next: first comes the
network in a single line, next the old path and then the new path each in a
single line, then come the lines for the next detected change. If the old path
for a network is unspecified, meaning its path was the default route, then
the string **"DEF"** will be printed in the corresponding line instead of the
path, the same goes for an unspecified new path.

Here is an example on how to use the `detect_changes()` function:

```python
from routechanges import change_detector
f1 = open("path/to/bgp_file_t1.txt")
f2 = open("path/to/bgp_file_t2.txt")
change_detector.detect_changes(f1, f2)  # Print changes to stdout
```
