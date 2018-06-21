from os import listdir
from os.path import isfile, join
import csv

# Create csv with bgp routes

root = "/home/alexandra/Desktop/Visualization/rutas_bgp"
header = 6

for file in listdir(root):
	file_csv = "csv/" + file.split(".")[0] + ".csv"
	file_csv_open = open(join(root,file_csv),"w")
	number_first_path = map(lambda x: x.split("."),file.split("_"))
	if isfile(join(root,file)):
		file_open = open(join(root,file),"r+")
		lines  = file_open.readlines()
		count = 0
		save_ip = ""
		is_save_ip = False
		for line in lines:
			count += 1
			if count > header:
				vector_line_aux = line.split(" ")
				vector_line_aux = list(filter(lambda x: x != '', vector_line_aux))
				if not is_save_ip:
					try:
						vector_line = [vector_line_aux[1]]
						if len(vector_line_aux) < 3:
							save_ip = vector_line[0].split("\n")[0]
							is_save_ip = True
							continue
						else:
							save_ip = ""
					except IndexError:
						break
				copy = False
				if is_save_ip:
					vector_line = [save_ip]
					is_save_ip = False
				for i in range(0,len(vector_line_aux)-1):
					if vector_line_aux[i] == number_first_path[0][0]:
						copy = True
					if copy == True:
						vector_line.append(vector_line_aux[i])
				writer = csv.writer(file_csv_open, delimiter = ',')
				writer.writerow(vector_line)

print "Finish Parser"

# VER PQ GENERA ARCHIVO CSV.CSV