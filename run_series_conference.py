import subprocess
import os

# create a string list
alignment_list = ["conference/cmt-conference/component/",
                  "conference/cmt-confof/component/",
                  "conference/cmt-edas/component/",
                  "conference/cmt-ekaw/component/",
                  "conference/cmt-iasted/component/",
                  "conference/cmt-sigkdd/component/",
                  "conference/conference-confof/component/",
                  "conference/conference-edas/component/",
                  "conference/conference-ekaw/component/",
                  "conference/conference-iasted/component/",
                  "conference/conference-sigkdd/component/",
                  "conference/confof-edas/component/",
                  "conference/confof-ekaw/component/",
                  "conference/confof-iasted/component/",
                  "conference/confof-sigkdd/component/",
                  "conference/edas-ekaw/component/",
                  "conference/edas-iasted/component/",
                  "conference/edas-sigkdd/component/",
                  "conference/ekaw-iasted/component/",
                  "conference/ekaw-sigkdd/component/",
                  "conference/iasted-sigkdd/component/"]

# loop through the list
for alignment in alignment_list:
    # execute the script with the new parameter
    print("alignment:", alignment)
    os.environ['alignment'] = alignment
    try:
        subprocess.run(['python', 'run_config.py'], check=True)
        print("run_config.py executed successfully.")
    except subprocess.CalledProcessError as error:
        print(f"Failed to execute run_config.py: {error}")
