import re

# Pattern we're looking for
pattern = re.compile(r"^[A-Z]{3}\d{2}[-/]([a-zA-Z0-9]+)#\1[@$!][0-9a-fA-F]{3}$")

filename = 'flags.txt'

try:
    with open(filename, 'r') as f:
        found = False

        for line in f:
            flag_line = line.strip()

            # only lines that look like flags
            if flag_line.startswith("haxagon{") and flag_line.endswith("}"):
                content = flag_line[8:-1]  # get text inside {}

                # check if it fully matches the pattern
                if pattern.fullmatch(content):
                    print("--- VALID FLAG FOUND ---")
                    print(flag_line)
                    found = True
                    break  # only one flag expected

        if not found:
            print("No valid flag found in the file.")

except FileNotFoundError:
    print(f"Error: file '{filename}' not found.")
    print(f"Make sure you saved your flags list as {filename} in the same folder.")
