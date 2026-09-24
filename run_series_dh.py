import subprocess
import os

# create a string list
alignment_list = ["dh/defc-pactols/component/",
                  "dh/dha-unesco/component/",
                  "dh/idai-pactols/component/",
                  "dh/idai-parthenos/component/",
                  "dh/ironagedanube-pactols/component/",
                  "dh/oeai-parthenos/component/",
                  "dh/pactols-parthenos/component/",
                  "dh/tadirah-unesco/component/"]

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
