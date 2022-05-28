with open("rala_vals.txt", "r") as file_in:
	with open("rala_vals_corrected.txt", "w") as file_out:
		lines = file_in.readlines()
		for line in lines:
			elements = line.split()
			lineString = ""
			for el in elements:
				lineString += ("%.5f  " % float(el))
			lineString = lineString[:-2]
			file_out.write(lineString + "\n")
