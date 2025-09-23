import subprocess
import os

base_dir = "data/multifarm"
alignment_list = []

# Walk through the base directory and collect only folders (not files)
for name in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, name)
    if os.path.isdir(folder_path):  # ensure it's a folder
        alignment_list.append(f"multifarm/{name}/component/")

# sort alphabetically
alignment_list.sort()
# print list
print(alignment_list)
print(f"Total folders: {len(alignment_list)}")

# loop through the list
for alignment in alignment_list:
    # execute the script with the new parameter
    print("alignment:", alignment)
    os.environ['alignment'] = alignment
    try:
        subprocess.run(['python', 'run_config.py'], check=True)
        print("run_config.py executed successfully via run_series_multifarm.py")
    except subprocess.CalledProcessError as error:
        print(f"Failed to execute run_config.py: {error}")
