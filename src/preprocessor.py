#small preprocessor to erase comments
def preprocess(characters):
	output = ""
	pos = 0
	while pos < len(characters):
		if characters[pos:pos+2] == "/*":
			pos += 2
			#process multiline comments
			while characters[pos:pos+2] != "*/":
				#replace endlines
				if characters[pos] == "\n":
					output += "\n"
				pos+=1
			pos+=2
		elif characters[pos:pos+2] == "//":
			pos+=2
			while characters[pos] != "\n":
				pos+=1
		else:
			output+=characters[pos]
			pos+=1
	return output