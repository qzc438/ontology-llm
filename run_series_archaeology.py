import subprocess
import os

# create a string list
alignment_list = ["archaeology/de-de/component/",
                  "archaeology/de-en/component/",
                  "archaeology/de-fr/component/",
                  "archaeology/de-it/component/",
                  "archaeology/en-en/component/",
                  "archaeology/en-fr/component/",
                  "archaeology/en-it/component/",
                  "archaeology/fr-fr/component/",
                  "archaeology/fr-it/component/",
                  "archaeology/it-it/component/"]

# loop through the list
for alignment in alignment_list:
    # execute the script with the new parameter
    print("alignment:", alignment)
    os.environ['alignment'] = alignment
    try:
        subprocess.run(['python', 'run_config.py'], check=True)
        print("run_config.py executed successfully via run_series_archaeology.py")
    except subprocess.CalledProcessError as error:
        print(f"Failed to execute run_config.py: {error}")
