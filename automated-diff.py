#!/usr/bin/python3
'''
# automated-diff.py
#
# Author:      Pete Link
# Date:        January 2025
# Description: This script logs into network devices and gathers Automated Healthcheck and Pre / Post Check with automated Post Diff reporting

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
#
import os
import logging
import difflib
import paramiko
import time
import subprocess
import re
from getpass import getpass
import sys

SEPARATOR = '-' * 60
COMMAND_DELAY = 3

# Configure logging
log_level = logging.INFO

if '--verbose' in sys.argv:
    log_level = logging.DEBUG
    verbose_logging = True
else:
    verbose_logging = False

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() if verbose_logging else logging.NullHandler(),
        logging.FileHandler("healthcheck.log")
    ]
)
logger = logging.getLogger(__name__)

# Color definitions
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'

def print_colored(text, color):
    print(f"{color}{text}{Color.RESET}")

def sanitize_filename(command):
    return command.replace(" ", "_").replace("|", "").replace("/", "_")

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

def ssh_command(host, username, password, commands, folder_name, health_check_type):
    """
    Execute each command separately, save individual .pre and .post files, and generate a consolidated precheck/postcheck per host.
    """
    try:
        logger.info(f"Connecting to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=20)
        
        time.sleep(2)

        if ssh.get_transport().is_active():
            print_colored(f"[INFO] Successfully authenticated to {host}.", Color.GREEN)
        else:
            print_colored(f"[ERROR] Authentication failed for {host}.", Color.RED)
            logger.error(f"Authentication failed for {host}. Exiting.")
            return

        ssh_shell = ssh.invoke_shell()
        ssh_shell.settimeout(30)
        time.sleep(5)

        while ssh_shell.recv_ready():
            ssh_shell.recv(65535)

        consolidated_output = []

        for index, command in enumerate(commands):
            command_safe = sanitize_filename(command)

            if not verbose_logging:
                print(next(spinner), end='\r')
                sys.stdout.flush()

            logger.info(f"Executing command: {command} on {host}")

            while ssh_shell.recv_ready():
                ssh_shell.recv(65535)

            ssh_shell.send("\n\n\n")
            time.sleep(0.1)
            ssh_shell.send(command + "\n\n\n")

            time.sleep(COMMAND_DELAY + (5 if index == 0 else 2))

            output = ""
            if ssh_shell.recv_ready():
                while ssh_shell.recv_ready():
                    output += ssh_shell.recv(65535).decode('utf-8')

            if not output.strip():
                print_colored(f"[INFO] No output received for command: {command}", Color.YELLOW)
                logger.warning(f"[{host}] No output received for command: {command}")
            else:
                print_colored(f"[INFO] Command completed: {command}", Color.GREEN)

            # Write each command's output to a separate .pre or .post file
            output_file = os.path.join(folder_name, f"{host}-{command_safe}.{health_check_type}")
            try:
                with open(output_file, "w") as out:
                    out.write(output)
                logger.info(f"[{host}] Output written to {output_file}")
            except IOError as e:
                logger.error(f"[{host}] Failed to write output file: {output_file}. Error: {e}")

            consolidated_output.append(f"--- {command} ---\n{output}")

        # Write consolidated precheck or postcheck file for the host
        consolidated_file = os.path.join(folder_name, f"{host}.{health_check_type}check")
        with open(consolidated_file, "w") as cf:
            cf.write("\n\n".join(consolidated_output))
        logger.info(f"Consolidated {health_check_type}check file written: {consolidated_file}")

        ssh.close()
        logger.info(f"SSH session closed for {host}.")
    except paramiko.AuthenticationException:
        print_colored("[ERROR] Authentication failed. Please check your username or password.", Color.RED)
    except paramiko.NoValidConnectionsError:
        print_colored("[ERROR] Unable to connect to host. Check if the device is reachable.", Color.RED)
    except Exception as e:
        print_colored(f"[ERROR] {e}", Color.RED)

def main():
    try:
        logger.info("Script started")

        health_check_type = input("Select health check type (pre/post): ").strip().lower()
        folder_name = input("Enter folder name to store health check output files: ").strip()
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        username = input("Enter SSH username: ").strip()
        if not username.isalnum():
            print_colored("[ERROR] Invalid username. Only alphanumeric characters allowed.", Color.RED)
            return

        password = getpass("Enter SSH password: ")
        
        host = input("Enter the hostname or IP: ").strip()
        commands = ["show version", "show interfaces", "show ip route"]  # Placeholder commands

        ssh_command(host, username, password, commands, folder_name, health_check_type)

        # If post-check is selected, run the diff for each command and consolidate differences
        if health_check_type == "post":
            run_diff(folder_name, host)

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        print_colored(f"[ERROR] {e}", Color.RED)

if __name__ == "__main__":
    main()
