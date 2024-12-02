
#!/usr/bin/env python3

import os
import subprocess
from getpass import getpass
import difflib

def main():
    print("Health Check Script")
    print("===================")
    
    # Prompt for Pre or Post health check
    health_check_type = input("Are you doing a Pre or Post Health check? (Pre/Post): ").strip().lower()
    
    if health_check_type not in ["pre", "post"]:
        print("Invalid choice. Please enter 'Pre' or 'Post'.")
        return

    # Equipment type selection
    print("Select the equipment type:")
    print("1. Cisco 2948")
    print("2. Cisco CSR")
    equipment_choice = input("Enter your choice (1/2): ").strip()
    
    if equipment_choice == "1":
        device_name = "Cisco 2948"
        device_file = "2948.txt"
        pre_file = "2948.pre"
        post_file = "2948.aft"
    elif equipment_choice == "2":
        device_name = "Cisco CSR"
        device_file = "CSR.txt"
        pre_file = "CSR.pre"
        post_file = "CSR.aft"
    else:
        print("Invalid choice. Please enter 1 or 2.")
        return

    # Read commands from file
    if not os.path.exists(device_file):
        print(f"Error: {device_file} not found.")
        return

    with open(device_file, "r") as f:
        commands = f.read().splitlines()

    # SSH credentials
    host = input(f"Enter the {device_name} hostname or IP address: ").strip()
    username = input("Enter your SSH username: ").strip()
    password = getpass("Enter your SSH password: ")

    # Run SSH commands
    output_file = pre_file if health_check_type == "pre" else post_file
    with open(output_file, "w") as out:
        for command in commands:
            try:
                print(f"Running command: {command}")
                result = subprocess.run(
                    ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                     f"{username}@{host}", command],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                out.write(f"Command: {command}
{result.stdout}
")
            except Exception as e:
                print(f"Error executing command '{command}': {e}")

    print(f"Output saved to {output_file}")

    # Perform diff for Post health check
    if health_check_type == "post":
        if not os.path.exists(pre_file):
            print(f"Error: {pre_file} not found for comparison.")
            return

        diff_output_file = f"{device_name.replace(' ', '_')}.out"
        with open(pre_file, "r") as pre, open(post_file, "r") as post, open(diff_output_file, "w") as diff_out:
            pre_lines = pre.readlines()
            post_lines = post.readlines()
            diff = difflib.unified_diff(pre_lines, post_lines, fromfile=pre_file, tofile=post_file)
            diff_output = "".join(diff)
            print("Difference:")
            print(diff_output)
            diff_out.write(diff_output)

        print(f"Diff saved to {diff_output_file}")

if __name__ == "__main__":
    main()
