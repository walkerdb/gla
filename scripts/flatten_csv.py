import os
import csv
from collections import defaultdict

with open(r"C:\Users\dev\Downloads\great_lakes_digital_library-xml (1).csv") as f:
	data = defaultdict(lambda: defaultdict(list))
	last_id = ''

	reader = csv.DictReader(f)
	for row in reader:
		last_id = row['identifier'] if row['identifier'] else last_id
		for key, value in row.items():
			data[last_id][key].append(value)

	keys = data[last_id].keys()
	max_lengths = []
	for key in keys:

		lengths = []
		for sub_dict in data.values():
			length = len(list(filter(None, sub_dict[key]))) if sub_dict[key] else 0
			lengths.append(length)

		max_lengths.append(max(lengths))

	lengths = dict(zip(keys, max_lengths))
	
	with open("great_lakes_digital_library_flattened.csv", mode="w", newline="") as f:
		writer = csv.writer(f)
		header = []
		for key in keys:
			for i in range(1, lengths[key] + 1):
				header.append("{0} {1}".format(key, i))

		writer.writerow(header)

		for sub_dict in data.values():
			row = []

			for key in keys:
				for i in range(lengths[key]):
					if i < len(sub_dict[key]):
						row.append(sub_dict[key][i])
					else:
						row.append("")

			writer.writerow(row)
