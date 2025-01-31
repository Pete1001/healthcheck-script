#!/usr/bin/env python3

import os
import logging
import difflib
import paramiko
import time
import glob
from getpass import getpass

# Global separator for formatting
SEPARATOR = '-' * 60
COMMAND_DELAY = 3  # Seconds

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("healthcheck.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ANSI color definitions for terminal output
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    RESET = '\033[0m'

# Clear the screen
os.system('clear' if os.name == 'posix' else 'cls')

def pause_for_user():
    """ Waits for user to press ENTER to continue. """
    input("\nPress ENTER to continue... ")

def get_last_created_folder():
    """ Find the most recently created directory in the current working directory. """
    folders = [f for f in glob.glob("*/") if os.path.isdir(f)]
    if not folders:
        return None
    return max(folders, key=os.path.getctime).rstrip("/")

def ssh_command(host, username, password, commands, folder_name, health_check_type, ticket_number):
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

        prepost_files = []
        consolidated_output = []

        for command in commands:
            sanitized_command = command.replace(" ", "_").replace("|", "").replace("/", "_")
            output_file = os.path.join(folder_name, f"{host}-{sanitized_command}.{health_check_type}")

            logger.info(f"[{host}] Running command: {command}")
            ssh_shell.send(command + "\n")
            time.sleep(COMMAND_DELAY)

            if ssh_shell.recv_ready():
                output = ssh_shell.recv(65535).decode('utf-8')
                with open(output_file, "w") as out:
                    out.write(output)
                prepost_files.append(output_file)
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

    except paramiko.ssh_exception.NoValidConnectionsError:
        print(f"{Color.RED}[ERROR] Unable to connect to host. Check if the device is reachable.{Color.RESET}")

    except Exception as e:
        print(f"{Color.RED}[ERROR] {e}{Color.RESET}")

def main():
    try:
        logger.info("Script started")

        print("\n" + "=" * 80)
        print(f"{Color.PURPLE}Automated Pre and Post Health Check Script{Color.RESET}")
        print("=" * 80)
        print("\nEnsure all required files are present before proceeding.\n")
        print("-" * 80)

        pause_for_user()

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
                print(f"{Color.RED}[ERROR] Required file `{command_file}` is missing.{Color.RESET}")
                return

            with open(command_file, "r") as file:
                commands = [line.strip() for line in file if line.strip()]

            with open("hosts.txt", "r") as file:
                hosts = [line.strip() for line in file if line.strip()]
        else:
            print(f"{Color.RED}[ERROR] Invalid choice.{Color.RESET}")
            return

        health_check_type = input("Select health check type (pre/post): ").strip().lower()
        ticket_number = input("Enter ticket number for tracking: ").strip()

        if health_check_type == "post":
            last_folder = get_last_created_folder()
            if last_folder:
                confirm = input(f"\nUse the last created folder '{last_folder}'? (Y/N): ").strip().lower()
                folder_name = last_folder if confirm == "y" else input("Enter folder name: ").strip()
            else:
                print(f"{Color.YELLOW}[WARNING] No previous folders found. Enter a folder manually.{Color.RESET}")
                folder_name = input("Enter folder name for output files: ").strip()
        else:
            folder_name = input("Enter folder name for output files: ").strip()

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        username = input("Enter SSH username: ").strip()
        password = getpass("Enter SSH password: ")

        for host in hosts:
            ssh_command(host, username, password, commands, folder_name, health_check_type, ticket_number)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"{Color.RED}[ERROR] {e}{Color.RESET}")

    finally:
        print(f"\n{Color.PURPLE}Have a nice day!{Color.RESET}")

if __name__ == "__main__":
    main()
