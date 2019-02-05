# RouteViews

The version of python used for the `routechanges` and `test` modules is
**python 3.6.5**. These modules also attempt to follow the [PEP8][pep8] style
guide.

[pep8]: https://www.python.org/dev/peps/pep-0008/


## Testing

Testing is done using the `unittest` module from the python standard library.
To run all tests use the next command from the **project root folder**:

	python -m unittest

To run a specific test file, for example `test_change_detector.py` use:

	python -m unittest test/test_change_detector.py

Find more information [here][unittest]

[unittest]: https://docs.python.org/3.6/library/unittest.html


## routechanges module

Every library used in the `routechanges` module comes from the python standard
library.

The `routechanges` package contains the `change_detector` module that has
the `detect_changes()` function, which is explained below.

The `change_detector` module also contains two additional useful functions,
these are `get_rows()` and `aggregate_routes()`, the first returns an iterator
to obtain the rows of a BGP routes file and the second function allows to
reduce the number of rows of a BGP file printing the result or returning
a list with the rows.

**To use any of the functions listed below the BGP files must have their
position set to 0.** 


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

**For files of size around 60 MB the execution time of the function should be
around 1 minute or less.**

Here is an example on how to use the `detect_changes()` function:

```python
from routechanges import change_detector
f1 = open("path/to/bgp_file_t1.txt")
f2 = open("path/to/bgp_file_t2.txt")
change_detector.detect_changes(f1, f2)  # Print changes to stdout
```

#### Explanation for algorithm used in `detect_changes()`

The `detect_changes()` function follows the next algorithm:

* Aggregate the routes in file_t1 and file_t2.
* Merge the lists obtained in the previous step into merged_routes
* Build a tree for the networks using merged_routes, doing this we can
  get a forest because there might be completely separated top networks.
* Go over the tree/forest using an iterative version of DFS taking into
  account:
  * When we get to a node mark it as visited but don't unstack it till the
    next time we get to it (when we return from its children).
  * Spread the paths of the current node to its children so if any child node
    does not have its path specified then it is covered by its parent.
  * Once we get to a node that is marked as visited, unstack it, detect if the
    path was changed and verify this is the most specific network where the
    change originated by searching in the changes for its children, if nothing
    is found print the change. Make the parent of the node inherit the changes
    occurred till this point.

### change_detector.aggregate_routes(bgp_file, return_list=False, output_file=None)

Aggregate BGP routes in `bgp_file`. The output of the function is ordered by
network from lowest to highest ip and mask. If `return_list` is set to `True`
the function will return a list of 2-tuples where for each tuple the first
element will be an `IPv4Network` object and the second element will be the
string of the path for that network. If `return_list` is `False` the output
will be printed to `output_file` where each row of the output is formatted
with the first column having a width of 18 characters and containing the
network left aligned, then comes a space and the second column that contains
the path for that network. The second column has variable width depending on
the path and ends with a newline character. If `output_file` is None
`sys.stdout` will be used. This function does not modify the given file.

This function uses the `get_rows()` function internally.


### change_detector.get_rows(bgp_file)

Returns an iterator over the rows of the `bgp_file` containing only the information
about network and path. The element returned for each iteration is a 2 element
list with the first element as the string for the network and the second
element the string for the path of AS's. The nodes i and ? are excluded from
the path.

Here is an example on how to use the `get_rows()` function:

```python
from routechanges import change_detector
bgp_file = open("path/to/bgp_file.txt")
iterator = change_detector.get_rows(bgp_file)
for row in iterator:
	net_str = row[0]
	path_str = row[1]
	print(net_str)
	print(path_str)
```
