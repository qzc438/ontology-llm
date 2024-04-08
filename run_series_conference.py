import subprocess
import os

# Creating a string list
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

# Looping through the list
for alignment in alignment_list:
    print("alignment:", alignment)
    os.environ['alignment'] = alignment
    # Execute the script with the new parameter
    subprocess.run(['python', 'run_config.py'])
