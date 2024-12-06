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
import logging
import difflib
import paramiko
import time
from getpass import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.system('clear')

def ssh_command(host, username, password, commands, output_file):
    """
    Execute commands on a host via SSH and save output to a file.
    Ensures the session is active and ready for command execution.
    """
    try:
        logger.info(f"Attempting to connect to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=20)
        logger.info(f"Successfully connected to {host}.")

        # Open an interactive shell session
        ssh_shell = ssh.invoke_shell()
        ssh_shell.settimeout(10)  # Timeout for shell interactions

        # Check if the shell is active
        if not ssh_shell.active:
            raise RuntimeError("SSH shell session is not active.")

        # Execute commands
        with open(output_file, "a") as out:
            out.write(f"\n--- Output from {host} ---\n")
            for command in commands:
                logger.info(f"[{host}] Running command: {command}")
                ssh_shell.send(command + "\n")
                time.sleep(2)  # Wait for the command to execute
                if ssh_shell.recv_ready():
                    output = ssh_shell.recv(65535).decode('utf-8')
                    out.write(f"\nCommand: {command}\n{output}")
                    logger.info(f"[{host}] Command executed successfully.")
                else:
                    logger.warning(f"[{host}] No output received for command: {command}")
        ssh.close()
        return None  # No errors

    except paramiko.ssh_exception.AuthenticationException:
        return "[ERROR] Authentication failed. Please check your username or password."

    except paramiko.ssh_exception.NoValidConnectionsError:
        return "[ERROR] Unable to connect to host. Check if the device is reachable."

    except Exception as e:
        return f"[ERROR] {e}"

def main():
    print("\nAutomated Pre and Post Diff Check Script")
    print("=" * 60)

    # Prompt for Pre or Post health check
    health_check_type = input("\nAre you doing a Pre or Post Health check? (Pre/Post): ").strip().lower()
    if health_check_type not in ["pre", "post"]:
        print("\nInvalid choice. Please enter 'Pre' or 'Post'.")
        return

    # Equipment type selection
    print("\nSelect the equipment type:")
    print("1. Cisco Catalyst 49xx")
    print("2. Cisco Catalyst 65xx or 76xx")
    equipment_choice = input("\nEnter your choice (1/2): ").strip()
    
    if equipment_choice == "1":
        device_file = "CC_49xx.txt"
        file_suffix = "49xx"
    elif equipment_choice == "2":
        device_file = "CC_65xx-76xx.txt"
        file_suffix = "65xx-76xx"
    else:
        print("\nInvalid choice. Please enter 1 or 2.")
        return

    # Read commands from file
    if not os.path.exists(device_file):
        print(f"\nError: {device_file} not found.")
        return

    with open(device_file, "r") as f:
        commands = f.read().splitlines()

    # SSH credentials
    username = input("\nEnter your SSH username: ").strip()
    password = getpass("Enter your SSH password: ")

    # Read hosts from hosts.txt
    hosts_file = "hosts.txt"
    if not os.path.exists(hosts_file):
        print(f"\nError: {hosts_file} not found.")
        return

    with open(hosts_file, "r") as hf:
        hosts = [line.strip() for line in hf if line.strip()]

    # Track processed files and errors
    updated_files = []
    unreachable_hosts = []

    print("\nStarting health check for all hosts...\n")
    print("=" * 60)

    # Execute commands on each host
    for host in hosts:
        print(f"\nProcessing host: {host}")
        print("-" * 60)
        output_file = f"{host}.{file_suffix}.{health_check_type}"
        error = ssh_command(host, username, password, commands, output_file)
        if error:
            logger.error(f"Could not process host {host}. Error: {error}")
            unreachable_hosts.append(host)
        else:
            logger.info(f"Output for {host} saved to {output_file}")
            updated_files.append(output_file)

    # Perform diff for Post health check
    if health_check_type == "post":
        print("\nPerforming diff for post health check...\n")
        for host in hosts:
            pre_file = f"{host}.{file_suffix}.pre"
            post_file = f"{host}.{file_suffix}.aft"
            diff_output_file = f"{host}.{file_suffix}.out"

            if not os.path.exists(pre_file):
                logger.warning(f"{pre_file} not found for {host}. Skipping diff.")
                continue

            with open(pre_file, "r") as pre, open(post_file, "r") as post, open(diff_output_file, "w") as diff_out:
                pre_lines = pre.readlines()
                post_lines = post.readlines()
                diff = difflib.unified_diff(pre_lines, post_lines, fromfile=pre_file, tofile=post_file)
                diff_output = "".join(diff)
                if diff_output:
                    logger.info(f"Difference found for {host}.")
                    print(diff_output)
                else:
                    logger.info(f"No differences found for {host}.")
                diff_out.write(diff_output)
                updated_files.append(diff_output_file)

            logger.info(f"Diff for {host} saved to {diff_output_file}")

    # Summary of operations
    print("\nAll done! Have a nice day!")
    print("=" * 60)
    print("\nSummary of updated files:")
    for file in updated_files:
        print(f" - {file}")

    if unreachable_hosts:
        print("\nSummary of unreachable hosts:")
        for host in unreachable_hosts:
            print(f" - {host}")
    else:
        print("\nAll hosts were processed successfully!")

if __name__ == "__main__":
    main()
