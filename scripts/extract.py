import subprocess
import sys
import re

from pprint import pprint

def extract_functions(so_file):
    try:
        # Call readelf to get symbols from the shared library
        result = subprocess.run(['readelf', '-Ws', so_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check for any errors
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
            return

        output = result.stdout

        # Regex patterns to match defined, undefined, and weak functions
        defined_pattern = re.compile(r'\s+(\d+):\s+([0-9a-fA-F]+)\s+\d+\s+FUNC\s+GLOBAL\s+DEFAULT\s+\d+\s+(\w+)')
        undefined_pattern = re.compile(r'\s+(\d+):\s+0000000000000000\s+\d+\s+FUNC\s+GLOBAL\s+DEFAULT\s+UND\s+(\w+)')
        weak_pattern = re.compile(r'\s+(\d+):\s+([0-9a-fA-F]+)\s+\d+\s+FUNC\s+WEAK\s+DEFAULT\s+\d+\s+(\w+)')

        defined_functions = []
        undefined_functions = []
        weak_functions = []

        # Parse the output and categorize functions
        all_function_list_unique = set()
        for line in output.splitlines():
            defined_match = defined_pattern.match(line)
            undefined_match = undefined_pattern.match(line)
            weak_match = weak_pattern.match(line)

            if defined_match:
                defined_functions.append((defined_match.group(3), defined_match.group(2)))
            elif undefined_match:
                undefined_functions.append(undefined_match.group(2))
            elif weak_match:
                weak_functions.append((weak_match.group(3), weak_match.group(2)))

        # Output the list of defined global functions with addresses
        if defined_functions:
            # print("Defined global functions in the shared library (with addresses):")
            for func, addr in defined_functions:
                # print(f"- {func} at address {addr}")
                all_function_list_unique.add((addr, func))
        else:
            print("No defined global functions found.")

        # Output the list of undefined functions (functions dynamically linked at runtime)
        if undefined_functions:
            # print("\nUndefined functions (to be resolved at runtime):")
            for func in undefined_functions:
                print(f"- {func}")
        else:
            print("No undefined functions found.")

        # Output the list of weak functions with addresses
        if weak_functions:
            # print("\nWeak functions (can be overridden, with addresses):")
            for func, addr in weak_functions:
                # print(f"- {func} at address {addr}")
                all_function_list_unique.add((addr, func))
        else:
            print("No weak functions found.")

        pprint(all_function_list_unique)
        with open("musl_function_list.txt", "w") as fp:
            for item in all_function_list_unique:
                fp.write(f"{item[1]}\n")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 list_functions_with_addresses.py <path_to_so_file>")
        sys.exit(1)

    so_file = sys.argv[1]
    extract_functions(so_file)

