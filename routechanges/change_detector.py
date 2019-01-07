import re


def _calculate_regexp(header_line):
	"""Returns a regular expression	that helps to get each column in a
	row.
	"""
	header = header_line[0:-1]  # Remove newline character
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
			regex.append("(.{%s})" %str(len(column)+2))

	return ''.join(regex)  # Return complete regexp


# TODO: use without function.
def _get_row_values(row, regex):
	""" Returns a list that contains each column in a row. """
	row = row[0:-1] # Remove newline character
	values = re.findall(regex, line)
	values = [x.strip() for x in values[0]]
	return values
