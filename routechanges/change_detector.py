import sys
import re
from ipaddress import IPv4Network


def _calculate_regexp(header_line):
    """Returns a regular expression and a list of integers. The regular
    expression will help to parse the columns for each row of the table,
    and the list will contain the widths of the columns except for the
    last one which is the path column that has undefined length.
    """
    header = header_line[0:-1]  # Remove newline character
    header = header.replace("Next Hop", "Next_Hop")
    header = re.split(r' [a-zA-Z]', header)
    # First column only loses one character unlike the others that lose
    # the first and last character.
    header[0] = header[0][0:-1]
    column_lengths = []
    regex = []  # List of regexp for each column
    for column in header:
        # Last column is the path, so it has undefined length.
        if column == header[-1]:
            regex.append("(.+)")
            break
        # Create regexp for a column based on the number of
        # characters it has.
        c_lenght = len(column)+2
        column_lengths.append(c_lenght)
        regex.append("(.{%s})" % str(c_lenght))

    # Return complete regexp and list of widths
    return ''.join(regex), column_lengths


def get_rows(file):
    """ Returns an iterator over the rows of the file containing only
    the information about network and path. The element returned for
    each itaration is a 2 element list with the first element as the 
    string for the network and the second element the string for the
    path of AS's.
    """
    # Skip first 5 lines of the file header.
    for _ in range(5):
        file.readline()

    # Calculate regex to parse rows.
    header = file.readline()
    regex, column_lengths = _calculate_regexp(header)
    first_three = sum(column_lengths[0:3])
    all_col = sum(column_lengths)  # Row length till path column

    for line in file:
        if line == "\n":
            break  # There are no more rows
        line = line[0:-1]  # Remove newline character
        if len(line) < first_three:  # The line is not complete
            # Remove first column and newline character to only get
            # the network.
            net = line[column_lengths[0]:len(line)]
            next_line = file.readline()
            # Remove every row before the path and remove newline
            # character.
            path = next_line[all_col:-1]
            row = [net, path]
        else:
            row = re.findall(regex, line)
            row = row[0]
            row = [row[1].strip(), row[6]]

        if row[1][-1] == "?" or row[1][-1] == "i":
            # Remove last node that does not help when comparing paths.
            row[1] = row[1][0:-1]
        row[1] = row[1].strip()  # Remove aditional spaces
        yield row


def aggregate_routes(file, return_list=False, output_file=None):
    """Aggregate BGP routes in file.
    The output of the function is ordered by network from lowest to
    highest ip and mask.
    If return_list is set to True the function will return a list of
    2-tuples where for each tuple the first element will be an
    IPv4Network object and the second element will be the string of the
    path for that network.
    If return_list is False the output will be printed to output_file
    where each row of the output is formatted with the first column
    having a width of 18 characters and containing the network left
    aligned, then comes a space and the second column that contains the
    path for that network. The second column has variable width
    depending on the path and ends with a newline character. If
    output_file is None sys.stdout will be used.
    This function does not modify the given file. 
    """
    if output_file == None:
        output_file = sys.stdout

    net = 0  # Network index in a row array
    path = 1  # Path index
    row_list = {}  # Rows to be displayed

    row_iterator = get_rows(file)
    default_present = False
    first_row = next(row_iterator)
    if first_row[net] == "0.0.0.0":
        # Skip default route in first row.
        # Add mask to be coherent with ipaddress library.
        first_row[net] = "0.0.0.0/32"
        default_present = True
        second_row = next(row_iterator)
        second_row[net] = IPv4Network(second_row[net], False)
        row_list[second_row[path]] = {second_row[net]}
    else:
        row_list[first_row[path]] = {IPv4Network(first_row[net], False)}

    # For each row of the table find if it can be aggregated and
    # aggregate it, otherwise add the network to the corresponding
    # set for its path in row_list.
    for row in row_iterator:
        row[net] = IPv4Network(row[net], False)
        current_path = row[path]
        current_net = row[net]
        if current_path in row_list:
            # Try to aggregate the net.
            while True:
                supernet = current_net.supernet()
                if supernet != current_net:
                    if supernet in row_list[current_path]:
                        # There is no need to add this net, because
                        # its supernet has the same path.
                        break

                    # Get sibling net.
                    n1, n2 = supernet.subnets()
                    if n1 == current_net:
                        sibling_net = n2
                    else:
                        sibling_net = n1

                    if sibling_net in row_list[current_path]:
                        row_list[current_path].discard(sibling_net)
                        # As the two nets have the same path we only
                        # need the supernet.
                        # Continue trying to aggregate the supernet.
                        current_net = supernet
                        continue

                # The net couldn't be aggregated.
                row_list[current_path].add(current_net)
                break
        else:
            row_list[current_path] = {current_net}

    final_list = []

    if default_present:
        if return_list:
            final_list = [(IPv4Network(first_row[net]), first_row[path])]
        else:
            # Print default route.
            print("{0:18} {1}".format(first_row[net], first_row[path]),
                  file=output_file)

    # Prepare to output rows ordered by network.
    for path, net_set in row_list.items():
        for network in net_set:
            final_list.append((network, path))

    final_list.sort(key=lambda pair: pair[0])

    if return_list:
        return final_list

    # Show aggregated routes.
    for network, path in final_list:
        print("{0:18} {1}".format(str(network), path), file=output_file)


def _merge_tables(routes_t1, routes_t2):
    """routes_t1 and routes_t2 must be lists of 2-tuples where the first
    element of a tuple is an IPv4Network object and the second is the
    string for the path of that network. The lists must be ordered by
    network from lowest to highest ip and mask.

    Returns a list of 3-tuples where the first element is an IPv4Network
    object, the second is the path for time t1 and the third is the path
    for time t2. If a path is not present the correponding element in
    the tuple will be None.
    The returned list is ordered by network from lowest to highest ip
    and mask.
    """
    # Net and path indexes for a tuple in routes_t1 or routes_t2.
    net = 0
    path = 1
    i = 0  # Index for routes_t1
    j = 0  # Index for routes_t2
    merged_table = []
    len_t1 = len(routes_t1)
    len_t2 = len(routes_t2)

    # Merge tables.
    while i < len_t1 and j < len_t2:
        row_t1 = routes_t1[i]
        row_t2 = routes_t2[j]
        if row_t1[net] < row_t2[net]:
            merged_table.append((row_t1[net], row_t1[path], None))
            i += 1
        elif row_t1[net] == row_t2[net]:
            merged_table.append((row_t1[net], row_t1[path], row_t2[path]))
            i += 1
            j += 1
        else:  # row_t1[net] > row_t2[net]
            merged_table.append((row_t2[net], None, row_t2[path]))
            j += 1

    # Add remaining elements.
    if i < len_t1:
        while i < len(routes_t1):
            merged_table.append((routes_t1[i][net], routes_t1[i][path], None))
            i += 1
    if j < len_t2:
        while j < len(routes_t2):
            merged_table.append((routes_t2[j][net], None, routes_t2[j][path]))
            j += 1

    return merged_table


def _build_tree(routes):
    """routes is a list of 3-tuples where the first element of a tuple
    is an IPv4Network object and the second and third elements are the
    strings for the paths for times t1 and t2 respectively. routes
    must be ordered by network from lowest to highest ip and mask.

    Returns three elements:
    The first element is a dict object as an adjacency list where each 
    key-value pair is an IPv4Network object and the list of IPv4Network
    ojects that are direct children of that network. For each network
    its list is ordered from lowest to highest ip and mask.
    The second element is the ordered list of top IPv4Network objects
    that are not children of any other network.
    The third element is the routes list converted into a dict object
    where each key-value pair is the IPv4Network object and the
    corresponding 2-tuple that has the path for time t1 as first element
    and the path for time t2 as second element.
    """
    # Net and paths indexes for a tuple.
    net = 0
    path_t1 = 1
    path_t2 = 2

    tree = {}
    top_networks = []
    routes_dict = {}
    stack = []
    for row in routes:
        routes_dict[row[net]] = (row[path_t1], row[path_t2])
        tree[row[net]] = []

        # Unstack while the current net is not children of net
        # in top of the stack.
        while len(stack) != 0 and not row[net].overlaps(stack[-1]):
            stack.pop()

        # If there is no network above the current one add the net
        # to top_networks.
        if len(stack) == 0:
            stack.append(row[net])
            top_networks.append(row[net])
            continue

        # Here row[net].overlaps(stack[-1]) is True, then add the net
        # to the parent network list.
        tree[stack[-1]].append(row[net])
        stack.append(row[net])

    return tree, top_networks, routes_dict


def detect_changes(file_t1, file_t2, output_file=None):
    """Find changes in routes of file_t2 repect to file_t1 and print
    them to output_file, if output_file is None then sys.stdout will be
    used. The changes are printed in order by network from highest to
    lowest ip and mask, where for every change detected the format is
    the next: first comes the network in a single line, next the old
    path and then the new path each in a single line, then come the
    lines for the next detected change. If the old path for a network
    is unspecified, meaning its path was the default route, then the
    string "DEF" will be printed in the corresponding line instead of
    the path, the same goes for an unspecified new path. 
    """
    if output_file is None:
        output_file = sys.stdout

    routes_t1 = aggregate_routes(file_t1, return_list=True)
    routes_t2 = aggregate_routes(file_t2, return_list=True)
    merged_tables = _merge_tables(routes_t1, routes_t2)
    tree, top_networks, routes = _build_tree(merged_tables)

    # Indexes of paths for time t1 and t2 in a tuple from routes.
    t1 = 0
    t2 = 1

    # Use DFS to detect changes
    stack = top_networks  # Initialize the stack with top_networks
    # The next 4 dict objects will have networks as keys.
    visited = {}
    children_paths = {}  # Stores changes in paths for children nodes
    parent_node = {}
    # path_till_node will store the path available from the less
    # specific network that covers the network related to the key
    path_till_node = {}

    for net in routes:
        visited[net] = False
        children_paths[net] = (set(), set())
        parent_node[net] = None
        path_till_node[net] = (None, None)

    while len(stack) != 0:
        current_node = stack[-1]
        path_t1 = routes[current_node][t1]
        path_t2 = routes[current_node][t2]
        if visited[current_node]:
            stack.pop()
            parent = parent_node[current_node]

            # Path not specified for t1.
            if path_t1 == None:
                # Use path from less specific network.
                path_t1 = path_till_node[current_node][t1]

                # If there is a change:
                if path_t1 != path_t2:
                    # Make sure this is the more specific change.
                    if path_t2 not in children_paths[current_node][t2]:
                        path_str = "DEF" if path_t1 == None else path_t1
                        text = "{0}\n{1}\n{2}".format(str(current_node),
                                                      path_str, path_t2)
                        print(text, file=output_file)
                        if parent != None:
                            # Add the change to the sets of changes.
                            children_paths[parent][t1].add(path_t1)
                            children_paths[parent][t2].add(path_t2)
                    if parent != None:
                        # Make the parent inherit the sets of changes
                        # from its children.
                        ch_paths_t1 = children_paths[current_node][t1]
                        ch_paths_t2 = children_paths[current_node][t2]
                        children_paths[parent] = (
                            children_paths[parent][t1].union(ch_paths_t1),
                            children_paths[parent][t2].union(ch_paths_t2))

            # Path not specified for t2.
            elif path_t2 == None:
                # Use path from less specific network.
                path_t2 = path_till_node[current_node][t2]

                # If there is a change:
                if path_t2 != path_t1:
                    # Make sure this is the more specific change.
                    if path_t1 not in children_paths[current_node][t1]:
                        path_str = "DEF" if path_t2 == None else path_t2
                        text = "{0}\n{1}\n{2}".format(str(current_node),
                                                      path_t1, path_str)
                        print(text, file=output_file)
                        if parent != None:
                            # Add the change to the sets of changes.
                            children_paths[parent][t1].add(path_t1)
                            children_paths[parent][t2].add(path_t2)
                    if parent != None:
                        # Make the parent inherit the sets of changes
                        # from its children.
                        ch_paths_t1 = children_paths[current_node][t1]
                        ch_paths_t2 = children_paths[current_node][t2]
                        children_paths[parent] = (
                            children_paths[parent][t1].union(ch_paths_t1),
                            children_paths[parent][t2].union(ch_paths_t2))

            # Both paths are specified but they are different.
            elif path_t1 != path_t2:
                # Make sure this is the more specific change.
                if path_t2 not in children_paths[current_node][t2]:
                    text = "{0}\n{1}\n{2}".format(str(current_node), path_t1,
                                                  path_t2)
                    print(text, file=output_file)
                    if parent != None:
                        # Add the change to the sets of changes.
                        children_paths[parent][t1].add(path_t1)
                        children_paths[parent][t2].add(path_t2)
                if parent_node[current_node] != None:
                    # Make the parent inherit the sets of changes from
                    # its children.
                    ch_paths_t1 = children_paths[current_node][t1]
                    ch_paths_t2 = children_paths[current_node][t2]
                    children_paths[parent] = (
                        children_paths[parent][t1].union(ch_paths_t1),
                        children_paths[parent][t2].union(ch_paths_t2))

        else:  # visited[current_node] = False
            visited[current_node] = True
            # Get the paths that are propagated to the children nodes.
            if path_t1 == None:
                next_path_t1 = path_till_node[current_node][t1]
            else:
                next_path_t1 = path_t1

            if path_t2 == None:
                next_path_t2 = path_till_node[current_node][t2]
            else:
                next_path_t2 = path_t2

            # Set the propagated paths and stack children nodes.
            for net in tree[current_node]:
                stack.append(net)
                parent_node[net] = current_node
                path_till_node[net] = (next_path_t1, next_path_t2)
