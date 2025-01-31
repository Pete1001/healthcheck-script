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

# ANSI color definitions for terminal output
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'

# Clear the screen
os.system('clear' if os.name == 'posix' else 'cls')

def pause_for_user():
    """ Waits for user to press the space bar to continue. """
    input("\nPress SPACE BAR to continue... ")

def ssh_command(host, username, password, commands, output_file):
    """
    Execute commands on a host via SSH and save output to a file.
    """
    try:
        logger.info(f"Attempting to connect to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=20)
        logger.info(f"Successfully connected to {host}.")

        ssh_shell = ssh.invoke_shell()
        ssh_shell.settimeout(10)

        if not ssh_shell.active:
            raise RuntimeError("SSH shell session is not active.")

        with open(output_file, "a") as out:
            out.write(f"\n--- Output from {host} ---\n")
            for command in commands:
                logger.info(f"[{host}] Running command: {command}")
                ssh_shell.send(command + "\n")
                time.sleep(2)  
                if ssh_shell.recv_ready():
                    output = ssh_shell.recv(65535).decode('utf-8')
                    out.write(f"\nCommand: {command}\n{output}\n")
                    out.write(f"{'-' * 50}\n")
                    logger.info(f"[{host}] Command executed successfully.")
                else:
                    logger.warning(f"[{host}] No output received for command: {command}")

        ssh.close()
        return None

    except paramiko.ssh_exception.AuthenticationException:
        return "[ERROR] Authentication failed. Please check your username or password."

    except paramiko.ssh_exception.NoValidConnectionsError:
        return "[ERROR] Unable to connect to host. Check if the device is reachable."

    except Exception as e:
        return f"[ERROR] {e}"

def main():
    try:
        logger.info("Script started")

        # Display Welcome Message
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
        print("Healthcheck and Pre-check output files are written to `.pre` files.")
        print("Post-check output files are written to `.post` files.")
        print("-" * 80)
        print("Consolidated Pre-check output -> `.precheck` file per device")
        print("Consolidated Post-check output -> `.postcheck` file per device")
        print("Differences saved to `.out` files per device")
        print("=" * 80)

        pause_for_user()

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
            host = input("Enter the single device hostname or IP: ").strip()
            hosts = [host]
        elif equipment_choice in device_files:
            command_file = device_files[equipment_choice]
            if not os.path.exists(command_file):
                print_colored(f"[ERROR] Required file `{command_file}` is missing.", Color.RED)
                return

            with open(command_file, "r") as file:
                commands = [line.strip() for line in file if line.strip()]

            with open("hosts.txt", "r") as file:
                hosts = [line.strip() for line in file if line.strip()]
        else:
            print_colored("[ERROR] Invalid choice.", Color.RED)
            return

        health_check_type = input("Select health check type (pre/post): ").strip().lower()
        folder_name = input("Enter folder name for output files: ").strip()
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        username = input("Enter SSH username: ").strip()
        password = getpass("Enter SSH password: ")

        for host in hosts:
            ssh_command(host, username, password, commands, f"{folder_name}/{host}.{health_check_type}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print_colored(f"[ERROR] {e}", Color.RED)

if __name__ == "__main__":
    main()
