import re
from ipaddress import ip_network


def _calculate_regexp(header_line):
    """Returns a regular expression that helps to get each column in a
    row.
    """
    header = header_line[0:-1]  # Remove newline character
    header = header.replace("Next Hop", "Next_Hop")
    header = re.split(r' [a-zA-Z]', header)
    # First column only loses one character unlike the others that lose
    # the first and last character.
    header[0] = header[0][0:-1]

    regex = []  # List of regexp for each column
    for column in header:
        # Last column is the path, so it has undefined length.
        if column == header[-1]:
            regex.append("(.+)")
            break
        # Create regexp for a column based on the number of
        # characters it has.
        regex.append("(.{%s})" % str(len(column)+2))

    return ''.join(regex)  # Return complete regexp


def _get_row_values(row, regex):
    """ Returns a list that contains each column in a row. """
    row = row[0:-1]  # Remove newline character
    values = re.findall(regex, row)
    values = [x.strip() for x in values[0]]
    # Remove last node (i , e or ?) that doesn't count when
    # comparing paths.
    values[6] = values[6][0:-1]
    return values


def aggregate_routes(file):
    """Aggregate BGP routes in file and print them to stdout."""
    # Skip first 5 lines
    for _ in range(5):
        file.readline()
    header = file.readline()

    # Regex to parse row columns.
    regex = _calculate_regexp(header)

    net = 1  # Network index in a row array
    path = 6  # Path index
    row_list = {}  # Rows to be displayed

    first_row = file.readline()
    first_row = _get_row_values(first_row, regex)

    default_present = False
    if first_row[1] == "0.0.0.0":
        # Skip default route in first row
        default_present = True
        second_row = file.readline()
        second_row = _get_row_values(second_row, regex)
        second_row[net] = ip_network(second_row[net])
        row_list[second_row[path]] = {second_row[net]} 
    else:
        row_list[first_row[path]] = {ip_network(first_row[net])}

    # For each row of the table find if it can be aggregated and
    # aggregate it, otherwise append the network to the corresponding
    # list for its path in row_list.
    for line in file:
        if line == "\n":
            break  # There are no more rows
        row = _get_row_values(line, regex)
        row[net] = ip_network(row[net])
        current_path = row[path]
        aggregated = False
        if current_path in row_list:
            supernet = row[net].supernet()
            n1 , n2 = supernet.subnets()
            if n1 == row[net]:
                sibling_net = n2
            else:
                sibling_net = n1
            if supernet in row_list[current_path]:
                continue
            elif sibling_net in row_list[current_path]:
                row_list[current_path].add(supernet)
                row_list[current_path].discard(sibling_net)
                continue
            else:
                row_list[current_path].add(row[net])
        else:
            row_list[current_path] = {row[net]}


    # Print default route.
    if default_present:
        print("{0:18} {1}".format(first_row[net], first_row[path]))

    # Show aggregated routes.
    for path, net_set in row_list.items():
        for network in net_set:
            print("{0:18} {1}".format(str(network), path))
