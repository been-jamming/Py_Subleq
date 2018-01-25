import sys

subroutines = {}
constants = {}
labels = {}

current_label = 0

def process_inline(inline):
	if "{" not in inline:
		return
	inlines = inline.split("}")
	inlines.pop()
	for inline in inlines:
		inline_args, inline_contents = inline.split("{", 1)
		inline_name, inline_args = inline_args.split(" ", 1)
		inline_name = inline_name.strip()
		inline_args = inline_args.strip()
		inline_args = inline_args.split()
		inline_contents = inline_contents.strip()
		subroutines[inline_name] = [inline_args, inline_contents, 0]

def assemble_code(lines, scope):
	lines = lines.replace(":", scope + ":")
	lines = lines.replace("*", scope + "*")
	lines = lines.replace("&", "*")
	lines = lines.split("\n")
	i = 0
	while(i < len(lines)):
		if(lines[i].find("[") == 0):
			sub_name, args = lines[i].split(" ", 1)
			sub_name = sub_name[1:-1]
			if sub_name in subroutines:
				args = args.split()
				sub_contents = " " + subroutines[sub_name][1] + " "
				sub_contents = sub_contents.replace(" ", "  ")
				for arg, name in zip(args, subroutines[sub_name][0]):
					if "*" in arg:
						arg = arg.replace("*", "&")
					sub_contents = sub_contents.replace(" " + name + " ", " " + arg + " ")
					sub_contents = sub_contents.replace("\n" + name + " ", "\n" + arg + " ")
					sub_contents = sub_contents.replace(" " + name + "\n", " " + arg + "\n")
					sub_contents = sub_contents.replace("\n" + name + "\n", "\n" + arg + "\n")
				sub_contents = sub_contents.replace("  ", " ")
				sub_contents = sub_contents.strip()
				lines.pop(i)
				lines[i:i] = assemble_code(sub_contents, scope + "+" + sub_name + "-" + str(subroutines[sub_name][2]))
				subroutines[sub_name][2] += 1
			else:
				print("Error: unknown subroutine "+sub_name)
				exit()
		else:
			i += 1
	return lines

def process_labels(lines):
	current_line = 0
	current_address = 0
	addresses = []
	
	while current_line < len(lines):
		if lines[current_line] == "":
			lines.pop(current_line)
		else:
			lines[current_line] = lines[current_line].replace("^", "main-0*")
			for constant in constants.keys():
				lines[current_line] = lines[current_line].replace(constant, constants[constant])
			current_line += 1
	current_line = 0
	while current_line < len(lines):
		lines[current_line] = lines[current_line].strip()
		if ":" in lines[current_line]:
			labels[lines[current_line][:-1]] = current_address
			lines.pop(current_line)
		else:
			addresses.append(current_address)
			if " " in lines[current_line]:
				current_address += 6
			elif "*0" in lines[current_line] or "*1" in lines[current_line]:
				current_address += 1
			elif "*" in lines[current_line]:
				current_address += 2
			else:
				current_address += 1
			current_line += 1
	addr_string = "%0.4X" % current_address
	addr_string1 = addr_string[:2]
	addr_string2 = addr_string[2:]
	for line in range(len(lines)):
		lines[line] = lines[line].replace("AFTER1", addr_string1)
		lines[line] = lines[line].replace("AFTER2", addr_string2)
	for label in labels.keys():
		addr = "%0.4X" % labels[label]
		addr0 = addr[:2]
		addr1 = addr[2:]
		addr = addr0 + " " + addr1
		for line in range(len(lines)):
			lines[line] = lines[line].replace(label + "*0", addr0)
			lines[line] = lines[line].replace(label + "*1", addr1)
			lines[line] = lines[line].replace(label + "*", addr)
	for line in range(len(lines)):
		line_parts = lines[line].split()
		if len(line_parts) != 1 and len(line_parts) != 4 and len(line_parts) != 6:
			print("Warning: invalid opcode length on line " + str(line + 2))
			print("\t" + lines[line])
		if len(line_parts) == 4:
			addr = "%0.4X" % (addresses[line] + 6)
			addr = addr[:2] + " " + addr[2:]
			lines[line] += " " + addr
	return "\n".join(lines)

def assemble(lines, inline):
	process_inline(inline)
	assembled = assemble_code(lines.strip(), "main-0")
	return process_labels(assembled)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Error: no file name given"
		exit()
	if len(sys.argv) > 2:
		if len(sys.argv) == 3:
			text = "Error: unknown argument"
		else:
			text = "Error: unknown arguments"
		for i in range(len(sys.argv) - 2):
			text += " " + sys.argv[i + 2] + ","
		print text[:-1]
		exit()
	file_name = sys.argv[1]
	with open(file_name, "r") as f:
		contents = f.read()
	code_contents, inline_contents = contents.split("#inline")
	code_lines = code_contents.split("\n")
	i = 0
	while(code_lines[i].find("#define") == 0):
		parts = code_lines[i].split(" ", 2)
		constants[parts[1]] = parts[2]
		i += 1
	
	code_lines = code_contents.split("\n")
	while(code_lines[0].find("#define") == 0):
		code_lines.pop(0)
	new_contents = assemble("\n".join(code_lines), inline_contents)
	with open("a.rom", "w") as f:
		f.write("v2.0 raw\n" + new_contents.strip())
