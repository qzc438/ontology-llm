import os
import fileinput


old_statement = 'http://knowledgeweb.semanticweb.org/heterogeneity/alignment'
new_statement = 'http://knowledgeweb.semanticweb.org/heterogeneity/alignment#'


def fix_reference_syntax (directory_path):
    # walk through the directory
    for subdir, dirs, files in os.walk(directory_path):
        for file in files:
            # check if the file name is "reference"
            if file in ('reference.xml', 'reference.rdf'):
                file_path = os.path.join(subdir, file)
                # open the file and replace the text
                with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
                    for line in file:
                        # replace only the exact old_statement
                        updated_line = line.replace(old_statement, new_statement) if old_statement in line and new_statement not in line else line
                        print(updated_line, end='')
                print(f"Updated file: {file_path}")
    # print completion
    print(f"{directory_path}: All files have been updated.")

if __name__ == '__main__':
    fix_reference_syntax('data')
