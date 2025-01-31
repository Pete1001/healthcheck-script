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
from getpass import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.system('clear')

def print_colored(message, color):
    """ Prints a message in the specified color """
    print(f"{color}{message}\033[0m")

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
        print_colored(f"[INFO] Differences found for {hostname}. Consolidated diff saved to {hostname}.out", "\033[93m")
        logger.info(f"Consolidated diff saved to {out_file}")
    else:
        print_colored(f"[INFO] No differences found for {hostname}", "\033[92m")
        logger.info(f"No differences found for {hostname}")

def main():
    try:
        logger.info("Script started")

        # Introductory message
        print("\nAutomated Pre and Post Health Check Script")
        print("=" * 80)

        # Equipment type selection
        print("\nSelect the equipment type:")
        print(" 1. Single Device (Manually Enter IP/Hostname)")
        print(" 2. Cisco ASR9K")
        print(" 3. Cisco CRS")
        print(" 4. Cisco Catalyst 2960")
        print(" 5. Cisco Catalyst 3850")
        print(" 6. Cisco Catalyst 4500-X")
        print(" 7. Cisco Catalyst 49xx")
        print(" 8. Cisco Catalyst 65xx or 76xx")
        print(" 9. Cisco Nexus 5xxx")
        print("10. Cisco Nexus 7xxx")
        print("11. Cisco Nexus 93xx/95xx")

        equipment_choice = input("\nEnter your choice (1-11): ").strip()
        device_files = {
            "2": "C-ASR9K.txt",
            "3": "C-CRS.txt",
            "4": "CC_2960.txt",
            "5": "CC_3850.txt",
            "6": "CC_4500-X.txt",
            "7": "CC_49xx.txt",
            "8": "CC_65xx-76xx.txt",
            "9": "C-Nexus 5xxx.txt",
            "10": "C-Nexus 7xxx.txt",
            "11": "C-Nexus 93xx-95xx.txt"
        }

        if equipment_choice == "1":
            # Manual Single Device Entry
            host = input("Enter the single device hostname or IP: ").strip()
            hosts = [host]
            commands = []
        elif equipment_choice in device_files:
            command_file = device_files[equipment_choice]

            if not os.path.exists(command_file):
                print_colored(f"[ERROR] Required file `{command_file}` is missing.", "\033[91m")
                return

            if not os.path.exists("hosts.txt"):
                print_colored("[ERROR] Required file `hosts.txt` is missing.", "\033[91m")
                return

            with open(command_file, "r") as file:
                commands = [line.strip() for line in file if line.strip()]

            with open("hosts.txt", "r") as file:
                hosts = [line.strip() for line in file if line.strip()]

            print("\nHosts found in hosts.txt:")
            for h in hosts:
                print(f" - {h}")

            confirm_hosts = input("\nDo you want to continue with these hosts? (Y/N): ").strip().lower()
            if confirm_hosts != "y":
                print_colored("Operation aborted by user.", "\033[91m")
                return
        else:
            print_colored("[ERROR] Invalid choice. Please restart and enter a valid number.", "\033[91m")
            return

        # Ask user for health check type
        health_check_type = input("Select health check type (pre/post): ").strip().lower()
        folder_name = input("Enter folder name to store health check output files: ").strip()
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        username = input("Enter SSH username: ").strip()
        password = getpass("Enter SSH password: ")
        host = input("Enter the hostname or IP: ").strip()

        # Run the diff function if it's a post check
        if health_check_type == "post":
            run_diff(folder_name, host)

        print_colored("[INFO] Setup complete. Proceeding with execution...", "\033[92m")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print_colored(f"[ERROR] {e}", "\033[91m")

if __name__ == "__main__":
    main()
