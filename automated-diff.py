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
#!/usr/bin/env python3

import os
import logging
import difflib
import paramiko
import time
import glob
import sys
from getpass import getpass
import itertools

# Global separator for formatting
SEPARATOR = '-' * 60
COMMAND_DELAY = 3  # Seconds

# Configure logging to both file and console
log_level = logging.INFO
verbose_mode = "--verbose" in sys.argv

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("healthcheck.log"),
        logging.StreamHandler() if verbose_mode else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# ANSI color definitions for terminal output
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# Clear the screen
os.system('clear' if os.name == 'posix' else 'cls')

def print_colored(message, color):
    """ Prints a message in the specified color """
    print(f"{color}{message}{Color.RESET}")

def pause_for_user():
    """ Waits for user to press ENTER to continue. """
    input("\nPress ENTER to continue... ")

def sanitize_filename(command):
    """ Sanitizes a command string to create safe filenames """
    return command.replace(" ", "_").replace("|", "").replace("/", "_")

def execute_and_save_output(ssh_shell, command, host, folder_name, check_type):
    """
    Execute a command over SSH, save its output to both individual .pre/.post files
    and consolidate all outputs into a .precheck or .postcheck file.
    """
    sanitized_command = sanitize_filename(command)
    output_file = os.path.join(folder_name, f"{host}-{sanitized_command}.{check_type}")
    consolidated_file = os.path.join(folder_name, f"{host}.{check_type}check")

    logger.info(f"[{host}] Running command: {command}")

    ssh_shell.send(command + "\n")
    time.sleep(COMMAND_DELAY)

    if ssh_shell.recv_ready():
        output = ssh_shell.recv(65535).decode('utf-8')

        # Save individual output file
        with open(output_file, "w") as out_f:
            out_f.write(output)

        # Append to consolidated precheck or postcheck file
        with open(consolidated_file, "a") as cf:
            cf.write(f"--- {command} ---\n{output}\n\n")

    else:
        print_colored(f"[WARNING] No output received for {command}", Color.YELLOW)

def run_diff(folder_name, hostname):
    """
    Compare pre and post files for each command and generate a consolidated .out file per host.
    """
    precheck_files = [f for f in os.listdir(folder_name) if f.startswith(hostname) and f.endswith('.pre')]
    postcheck_files = [f.replace('.pre', '.post') for f in precheck_files]

    differences = []
    for pre_file, post_file in zip(precheck_files, postcheck_files):
        pre_path = os.path.join(folder_name, pre_file)
        post_path = os.path.join(folder_name, post_file)

        if os.path.exists(post_path):
            with open(pre_path, 'r') as pre_f, open(post_path, 'r') as post_f:
                pre_content = pre_f.readlines()
                post_content = post_f.readlines()

            diff = list(difflib.unified_diff(pre_content, post_content, lineterm=''))

            if diff:
                differences.append(f"--- Differences in {pre_file.replace('.pre', '')} ---\n" + "\n".join(diff))

    if differences:
        out_file = os.path.join(folder_name, f"{hostname}.out")
        with open(out_file, 'w') as out_f:
            out_f.write("\n\n".join(differences))
        print_colored(f"[INFO] Differences found for {hostname}. Consolidated diff saved to {hostname}.out", Color.YELLOW)
        logger.info(f"Consolidated diff saved to {out_file}")
    else:
        print_colored(f"[INFO] No differences found for {hostname}", Color.GREEN)
        logger.info(f"No differences found for {hostname}")

def ssh_command(host, username, password, commands, folder_name, check_type):
    """ Establishes SSH connection and executes commands """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False)
        ssh_shell = client.invoke_shell()

        for command in commands:
            execute_and_save_output(ssh_shell, command, host, folder_name, check_type)

        client.close()
    except Exception as e:
        print_colored(f"[ERROR] SSH Connection failed: {e}", Color.RED)
        logger.error(f"SSH Connection failed: {e}")

def main():
    try:
        logger.info("Script started")

        print("\nAutomated Pre and Post Health Check Script")
        print("=" * 80)

        pause_for_user()

        # Equipment type selection
        print("\nSelect the equipment type:")
        print(" 1. Cisco ASR9K")
        print(" 2. Cisco CRS")
        print(" 3. Cisco Catalyst 2960")
        print(" 4. Cisco Catalyst 3850")
        print(" 5. Cisco Catalyst 4500-X")
        print(" 6. Cisco Catalyst 49xx")
        print(" 7. Cisco Catalyst 65xx or 76xx")
        print(" 8. Cisco Nexus 5xxx")
        print(" 9. Cisco Nexus 7xxx")
        print("10. Cisco Nexus 93xx/95xx")

        equipment_choice = input("\nEnter your choice (1-10): ").strip()
        device_files = {
            "1": "C-ASR9K.txt",
            "2": "C-CRS.txt",
            "3": "CC_2960.txt",
            "4": "CC_3850.txt",
            "5": "CC_4500-X.txt",
            "6": "CC_49xx.txt",
            "7": "CC_65xx-76xx.txt",
            "8": "C-Nexus 5xxx.txt",
            "9": "C-Nexus 7xxx.txt",
            "10": "C-Nexus 93xx-95xx.txt"
        }

        if equipment_choice not in device_files:
            print_colored("[ERROR] Invalid choice. Please restart and enter a number between 1 and 10.", Color.RED)
            return

        command_file = device_files[equipment_choice]
        if not os.path.exists(command_file):
            print_colored(f"[ERROR] Required file `{command_file}` is missing. Please add it and retry.", Color.RED)
            return

        with open(command_file, "r") as file:
            commands = [line.strip() for line in file if line.strip()]

        health_check_type = input("Select health check type (pre/post): ").strip().lower()
        folder_name = input("Enter folder name to store health check output files: ").strip()
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        username = input("Enter SSH username: ").strip()
        password = getpass("Enter SSH password: ")
        host = input("Enter the hostname or IP: ").strip()

        # Execute SSH commands
        ssh_command(host, username, password, commands, folder_name, health_check_type)

        # If post-check is selected, run the diff for each command
        if health_check_type == "post":
            run_diff(folder_name, host)

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        print_colored(f"[ERROR] {e}", Color.RED)

if __name__ == "__main__":
    main()
