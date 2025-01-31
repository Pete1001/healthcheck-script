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

def spinner():
    """ Generator for a simple spinner animation """
    symbols = ["|", "\\", "-", "/"]
    while True:
        for symbol in symbols:
            yield symbol

def pause_for_user():
    """ Waits for user to press ENTER to continue. """
    input("\nPress ENTER to continue... ")

def get_last_created_folder():
    """ Find the most recently created directory in the current working directory. """
    folders = [f for f in glob.glob("*/") if os.path.isdir(f)]
    if not folders:
        return None
    return max(folders, key=os.path.getctime).rstrip("/")

def run_diff(folder_name, hostname):
    """ Compare pre and post files for each command and generate a consolidated .out file """
    pre_files = [f for f in os.listdir(folder_name) if f.startswith(hostname) and f.endswith('.pre')]
    differences = []

    for pre_file in pre_files:
        post_file = pre_file.replace('.pre', '.post')
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
        print(f"{Color.YELLOW}[INFO] Differences found. Consolidated diff saved to {hostname}.out{Color.RESET}")
        logger.info(f"Consolidated diff saved to {out_file}")

def ssh_command(host, username, password, commands, folder_name, health_check_type):
    """
    Execute commands on a host via SSH and save output to .pre and .post files.
    Also consolidates into .precheck and .postcheck per device.
    """
    try:
        logger.info(f"Connecting to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=20)
        logger.info(f"Successfully connected to {host}.")

        ssh_shell = ssh.invoke_shell()
        ssh_shell.settimeout(30)

        if not ssh_shell.active:
            raise RuntimeError("SSH shell session is not active.")

        spin = spinner()

        consolidated_output = []

        for command in commands:
            sanitized_command = command.replace(" ", "_").replace("|", "").replace("/", "_")
            output_file = os.path.join(folder_name, f"{host}-{sanitized_command}.{health_check_type}")

            logger.info(f"[{host}] Running command: {command}")

            if not verbose_mode:
                print(f"{Color.BLUE}[INFO] Executing: {command}{Color.RESET}", end="", flush=True)
                for _ in range(10):  # Show the spinner while waiting
                    print(f" {next(spin)}", end="\r", flush=True)
                    time.sleep(0.1)

            ssh_shell.send(command + "\n")
            time.sleep(COMMAND_DELAY)

            if ssh_shell.recv_ready():
                output = ssh_shell.recv(65535).decode('utf-8')
                with open(output_file, "w") as out:
                    out.write(output)
                consolidated_output.append(f"--- {command} ---\n{output}\n")

            else:
                print(f"{Color.YELLOW}[WARNING] No output received for {command}{Color.RESET}")

        consolidated_file = os.path.join(folder_name, f"{host}.{health_check_type}check")
        with open(consolidated_file, "w") as cf:
            cf.write("\n\n".join(consolidated_output))

        ssh.close()
        logger.info(f"SSH session closed for {host}.")

    except paramiko.ssh_exception.AuthenticationException:
        print(f"{Color.RED}[ERROR] Authentication failed!{Color.RESET}")

def main():
    try:
        logger.info("Script started")

        print("\n" + "=" * 80)
        print(f"{Color.PURPLE}Automated Pre and Post Health Check Script{Color.RESET}")
        print("=" * 80)
        print("\nEnsure all required files are present before proceeding.\n")
        print("-" * 80)

        pause_for_user()

        username = input(f"\n{Color.BLUE}Enter SSH username: {Color.RESET}").strip()
        password = getpass(f"\n{Color.BLUE}Enter SSH password: {Color.RESET}")

        health_check_type = input("Select health check type (pre/post): ").strip().lower()
        if health_check_type == "post":
            last_folder = get_last_created_folder()
            if last_folder:
                confirm = input(f"\nUse the last created folder '{last_folder}'? (Y/N): ").strip().lower()
                folder_name = last_folder if confirm == "y" else input("Enter folder name: ").strip()
            else:
                print(f"{Color.YELLOW}[WARNING] No previous folders found. Enter a folder manually.{Color.RESET}")
                folder_name = input("Enter folder name for output files: ").strip()
        else:
            folder_name = input("Enter the ticket number / folder name to create: ").strip()

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # After post-check, inform user of output file locations
        if health_check_type == "post":
            print(f"{Color.GREEN}[INFO] Post-check completed.{Color.RESET}")
            print(f"{Color.GREEN}Consolidated post-check file: {folder_name}/<device>.postcheck{Color.RESET}")
            print(f"{Color.GREEN}Difference report (if changes exist): {folder_name}/<device>.out{Color.RESET}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"{Color.RED}[ERROR] {e}{Color.RESET}")

    finally:
        print(f"\n{Color.PURPLE}Have a nice day!{Color.RESET}")

if __name__ == "__main__":
    main()
