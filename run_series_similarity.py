import subprocess

# starting value
start = 1.00
# ending value
end = 0.50
# step value
step = -0.05

# set the parameter value you want to use
current_value = start

while current_value >= end:
    # execute the script with the new parameter
    subprocess.run(['python', 'om_database_matching.py', str(current_value)])
    # decrement the current value
    current_value += step
    # ensure not to go below the end value due to floating-point arithmetic issues
    current_value = round(current_value, 2)
