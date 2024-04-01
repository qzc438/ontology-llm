import subprocess

# Starting and ending values
start = 1.00
end = 0.50
step = -0.05  # Negative step for decrement

# Set the parameter value you want to use
current_value = start

while current_value >= end:
    # Execute the script with the new parameter
    subprocess.run(['python', 'om_database_matching.py', str(current_value)])
    # Decrement the current value
    current_value += step
    # Ensure not to go below the end value due to floating-point arithmetic issues
    current_value = round(current_value, 2)
