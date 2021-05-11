import sys

#small preprocessor to erase comments
def preprocess(characters):
	output = ""
	pos = 0
	while pos < len(characters):
		if characters[pos:pos+2] == "/*":
			#process multiline comments
			while characters[pos:pos+2] != "*/":
				#replace endlines
				if pos < len(characters):
					if characters[pos] == "\n":
						output += "\n"
					else:
						output += " "
					pos+=1
				else:
					sys.stderr.write("ERROR: unexpected EOF while processing comments \n")
					sys.exit(1)
			output += "  "
			pos+=2
		elif characters[pos:pos+2] == "//":
			while pos < len(characters) and\
				  characters[pos] != "\n":
				pos+=1
		else:
			output+=characters[pos]
			pos+=1
	return output