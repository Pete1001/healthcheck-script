#!/usr/bin/env python3
'''
# automated-diff.py
#
# Author:      Pete Link
# Date:        December 2024
# Description: Script to gather pre check output from network devices using SSH, then later gather post checks output and compare results.

## Contact
For questions or suggestions, feel free to open an issue or contact me via [GitHub](https://github.com/Pete1001).

 Use:        python3 `filename`

 Current directory must containt the files from the menu; e.g.:
    -CC_49xx.txt
    -CC_65xx-76xx.txt

    -the file should contain all commands from the Mandatory Pre/Post Check Verification section including the following:
        term len 0
        show run | i hostname
        show clock
    
hosts.txt must be named "hosts.txt".  The file must be located in the current directory and must be formatted in the following way:
    -one hostname or IP Address per line with no commas, quotes or spaces.
    
    -hosts.txt example:

        92.168.0.1
        192.168.0.2
'''
import os
import subprocess
from getpass import getpass
import difflib
import paramiko
import time

os.system('clear')

def ssh_command(host, username, password, commands, output_file):
    """
    Execute commands on a host via SSH and save output to a file.
    """
    try:
        # Establish SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=10)

        # Execute commands
        with open(output_file, "a") as out:
            out.write(f"\n--- Output from {host} ---\n")
            for command in commands:
                print(f"[{host}] Running command: {command}")
                stdin, stdout, stderr = ssh.exec_command(command)
                time.sleep(1)  # Give time for the command to execute
                output = stdout.read().decode()
                error = stderr.read().decode()
                if output:
                    out.write(f"\nCommand: {command}\n{output}")
                if error:
                    out.write(f"\nError: {command}\n{error}")
        ssh.close()
    except Exception as e:
        print(f"Error connecting to {host}: {e}")

def main():
    print("Automated Pre and Post Diff Check Script")
    print("=========================================================")

    # Prompt for Pre or Post health check
    health_check_type = input("Are you doing a Pre or Post Health check? (Pre/Post): ").strip().lower()
    if health_check_type not in ["pre", "post"]:
        print("Invalid choice. Please enter 'Pre' or 'Post'.")
        return

    # Equipment type selection
    print('')
    print("Select the equipment type:")
    print('')
    print("1. Cisco Catalyst 49xx")
    print("2. Cisco Catalyst 65xx or 76xx")
    print('')
    equipment_choice = input("Enter your choice (1/2): ").strip()
    
    if equipment_choice == "1":
        device_file = "CC_49xx.txt"
        file_suffix = "49xx"
    elif equipment_choice == "2":
        device_file = "CC_65xx-76xx.txt"
        file_suffix = "65xx-76xx"
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
    username = input("Enter your SSH username: ").strip()
    password = getpass("Enter your SSH password: ")

    # Read hosts from hosts.txt
    hosts_file = "hosts.txt"
    if not os.path.exists(hosts_file):
        print(f"Error: {hosts_file} not found.")
        return

    with open(hosts_file, "r") as hf:
        hosts = [line.strip() for line in hf if line.strip()]

    # Track processed files
    updated_files = []

    # Execute commands on each host
    for host in hosts:
        output_file = f"{host}.{file_suffix}.{health_check_type}"
        ssh_command(host, username, password, commands, output_file)
        print(f"Output for {host} saved to {output_file}")
        updated_files.append(output_file)

    # Perform diff for Post health check
    if health_check_type == "post":
        for host in hosts:
            pre_file = f"{host}.{file_suffix}.pre"
            post_file = f"{host}.{file_suffix}.aft"
            diff_output_file = f"{host}.{file_suffix}.out"

            if not os.path.exists(pre_file):
                print(f"Error: {pre_file} not found for {host}. Skipping diff.")
                continue

            with open(pre_file, "r") as pre, open(post_file, "r") as post, open(diff_output_file, "w") as diff_out:
                pre_lines = pre.readlines()
                post_lines = post.readlines()
                diff = difflib.unified_diff(pre_lines, post_lines, fromfile=pre_file, tofile=post_file)
                diff_output = "".join(diff)
                print(f"Difference for {host}:")
                print(diff_output)
                diff_out.write(diff_output)
                updated_files.append(diff_output_file)

            print(f"Diff for {host} saved to {diff_output_file}")

    # Summary of operations
    print("\nAll done! Have a nice day!")
    print("=========================================================")
    print("Summary of files updated:")
    for file in updated_files:
        print(f" - {file}")

if __name__ == "__main__":
    main()
