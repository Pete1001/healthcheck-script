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

def check_required_files(required_files):
    """
    Check if all required files exist in the current directory.
    """
    missing_files = [file for file in required_files if not os.path.exists(file)]
    if missing_files:
        print("\n[WARNING] The following required files are missing:")
        for file in missing_files:
            print(f" - {file}")
        print("\nPlease ensure all required files are present before proceeding.")
        return False
    return True

def ssh_command(host, username, password, commands, output_file):
    """
    Execute commands on a host via SSH and save output to a file.
    Adds a separator between each command's output.
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
                    # Add command output and separator
                    out.write(f"\nCommand: {command}\n{output}\n")
                    out.write(f"{'-' * 50}\n")  # Add separator line
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
    try:
        logger.info("Script started")

        # Introductory message
        print("\nAutomated Pre and Post Health Check Script")
        print("=" * 80)
        print("\nThis script requires the following files in the current directory:\n")
        print("         - `hosts.txt`:             - List of hosts (one per line).")
        print("         - `C_ASR9K.txt`:           - Cisco ASR9K")
        print("         - `C-CRS.txt`:             - Cisco CRS")
        print("         - `CC_2960.txt`:           - Cisco Catalyst 2960")
        print("         - `CC_3850.txt`:           - Cisco Catalyst 3850")
        print("         - `CC_4500-X.txt`:         - Cisco Catalyst 4500-X")
        print("         - `CC_49xx.txt`:           - Cisco Catalyst 49xx")
        print("         - `CC_65xx-76xx.txt`:      - Cisco Catalyst 65xx or 76xx")
        print("         - `C-Nexus 5xxx.txt`:      - Cisco Nexus 5xxx")
        print("         - `C-Nexus 7xxx.txt`:      - Cisco Nexus 7xxx")
        print("         - `C-Nexus 93xx-95xx.txt`: - Cisco Nexus 93xx/95xx\n")
        print("Ensure all required files are present before proceeding.\n")
        print("=" * 80)
        print("\nPlease NOTE:")
        print("=" * 80)
        print("\nYou can only use this for 'LIKE' devices, so ensure that hosts.txt only contains devices of a single 'type'.")
        print("Healthcheck and Pre-check output files of all commands are written to individual files with `.pre` extension.")
        print("Healthcheck and Post-check output files of all commands are written to individual files with `.post` extension.")
        print("-" * 80)
        print("Consolidated output of all commands for Healthcheck and Pre-check is written to a single file (for each device) with `.precheck` extension.")
        print("Consolidated output of all commands for Healthcheck and Post-check is written to a single file (for each device) with `.postcheck` extension.")
        print("\nConsolidated `diff` between Pre and Post Healthchecks as well as between Pre and Post checks is written to a file with `.out` extension (for each device).")
        print("-" * 80)
        print("=" * 80)

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

        # Validate equipment selection
        if equipment_choice not in device_files:
            print_colored("[ERROR] Invalid choice. Please restart and enter a number between 1 and 10.", Color.RED)
            return

        # Load commands from the corresponding file
        command_file = device_files[equipment_choice]
        if not os.path.exists(command_file):
            print_colored(f"[ERROR] Required file `{command_file}` is missing. Please add it and retry.", Color.RED)
            return

        with open(command_file, "r") as file:
            commands = [line.strip() for line in file if line.strip()]  # Read and clean up commands

        # Continue with the standard process
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

        # Execute SSH command function
        ssh_command(host, username, password, commands, folder_name, health_check_type)

        # If post-check is selected, run the diff for each command and consolidate differences
        if health_check_type == "post":
            run_diff(folder_name, host)

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        print_colored(f"[ERROR] {e}", Color.RED)

if __name__ == "__main__":
    main()
