import os
import fileinput

# Directory where the files are located
directory_path = 'data/multifarm'

# Walk through the directory
for subdir, dirs, files in os.walk(directory_path):
    for file in files:
        # Check if the file name is "reference.xml"
        if file == 'reference.xml':
            file_path = os.path.join(subdir, file)
            # Open the file and replace the text
            with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
                for line in file:
                    print(line.replace('<rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment"',
                                       '<rdf:RDF xmlns="http://knowledgeweb.semanticweb.org/heterogeneity/alignment#"'), end='')
            print(f"Updated file: {file_path}")

print("All files have been updated.")