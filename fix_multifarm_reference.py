import os
import fileinput

directory_path = 'data/multifarm'
old_statement = '<rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment'
new_statement = '<rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#'


if __name__ == '__main__':
    # walk through the directory
    for subdir, dirs, files in os.walk(directory_path):
        for file in files:
            # check if the file name is "reference.xml"
            if file == 'reference.xml':
                file_path = os.path.join(subdir, file)
                # open the file and replace the text
                with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
                    for line in file:
                        print(line.replace(old_statement, new_statement), end='')
                print(f"Updated file: {file_path}")
    # print completion
    print("All files have been updated.")
