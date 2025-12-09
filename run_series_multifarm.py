import os
import subprocess
import gc
import time
import psutil
# import torch

base_dir = "data/multifarm"
alignment_list = []

# prefix = "cmt-cmt"
# prefix = "cmt-conference"
# prefix = "cmt-confOf"
prefix = "cmt-iasted"
# prefix = "cmt-sigkdd"
# prefix = "conference-conference"
# prefix = "conference-confof"
# prefix = "conference-iasted"
# prefix = "conference-sigkdd"
# prefix = "confof-confof"
# prefix = "confof-iasted"
# prefix = "confof-sigkdd"
# prefix = "iasted-iasted"
# prefix = "iasted-sigkdd"
# prefix = "sigkdd-sigkdd"

# collect subfolders
for name in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, name)
    if os.path.isdir(folder_path) and name.startswith(prefix+"-"):
        alignment_list.append(f"multifarm/{name}/component/")

alignment_list.sort()
print(alignment_list)
print(f"Total folders: {len(alignment_list)}")

def clean_memory():
    """Force cleanup of CPU/GPU memory between runs."""
    print("Cleaning memory...")
    # ---- python garbage collection ----
    gc.collect()

    # GPU cleanup (if torch is available)
    # try:
    #     torch.cuda.empty_cache()
    #     torch.cuda.synchronize()
    # except Exception:
    #     pass

    # kill zombie processes
    current = psutil.Process()
    for child in current.children(recursive=True):
        try:
            child.kill()
        except Exception:
            pass

    # optional: reclaim page cache (Linux only)
    if os.path.exists("/proc/sys/vm/drop_caches") and os.geteuid() == 0:
        os.system("sync; echo 3 > /proc/sys/vm/drop_caches")

    # short pause so OS reclaims memory
    time.sleep(2)

# loop through alignments
for alignment in alignment_list:
    print("\n==========================================")
    print("alignment:", alignment)
    os.environ["alignment"] = alignment

    try:
        subprocess.run(
            ["python", "run_config.py"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("run_config.py executed successfully")
    except subprocess.CalledProcessError as error:
        print(f"Failed to execute run_config.py: {error}")

    # clean memory after each run
    clean_memory()

print("\nAll runs completed.")