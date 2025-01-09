#!/usr/bin/env python3
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

def ssh_command(host, username, password, commands, ticket_number, health_check_type):
    """
    Execute commands on a host via SSH and save output to separate files.
    Additionally, create a consolidated .precheck file for Pre health checks.
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

        # Create consolidated .precheck file for pre-checks
        precheck_file = None
        if health_check_type == "pre":
            precheck_file = os.path.join(ticket_number, f"{host}.precheck")

        # Execute commands
        for command in commands:
            logger.info(f"[{host}] Running command: {command}")
            ssh_shell.send(command + "\n")
            time.sleep(2)  # Wait for the command to execute
            if ssh_shell.recv_ready():
                output = ssh_shell.recv(65535).decode('utf-8')
                # Write each command's output to a separate file
                command_safe = command.replace(' ', '_').replace('|', '').replace('/', '_')
                output_file = os.path.join(ticket_number, f"{host}-{command_safe}.{health_check_type}")
                with open(output_file, "w") as out:
                    out.write(output)
                logger.info(f"[{host}] Output written to {output_file}")

                # Append to consolidated .precheck file
                if health_check_type == "pre" and precheck_file:
                    with open(precheck_file, "a") as consolidated:
                        consolidated.write(f"Command: {command}\n{output}\n{'-' * 50}\n")
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
    print("\nThis is an Automated Healthcheck and Pre / Post Check Script with automated Post Diff reporting")
    print("=" * 60)
    print("\nThis script requires the following files in the current directory:")
    print("- `hosts.txt`: List of hosts (one per line).")
    print("- `C_ASR9K.txt` : Commands for Cisco ASR9K devices.")
    print("- `CC_49xx.txt`: Commands for Cisco Catalyst 49xx devices.")
    print("- `CC_65xx-76xx.txt`: Commands for Cisco Catalyst 65xx or 76xx devices.")
    print("- Output files will be stored / retrieved from the ticket directory with the NAASOPS-xxxx name...\n")

    # Ask for the ticket number and create the directory
    ticket_number = input("Please enter / re-enter the ticket that you are working on (e.g., 'NAASOPS-xxxx'): ").strip()
    if not ticket_number:
        print("Ticket number cannot be empty. Exiting.")
        return

    # Create directory for the ticket
    if not os.path.exists(ticket_number):
        os.makedirs(ticket_number)

    print(f"\nTicket number {ticket_number} has been recorded. Output will be saved in the corresponding directory.")

    # Check required files
    required_files = ['hosts.txt', 'C_ASR9K.txt', 'CC_49xx.txt', 'CC_65xx-76xx.txt', 'CC_2960.txt', 'CC_3850.txt', 'CC_4500-X.txt', 'C-CRS.txt', 'C-Nexus 5xxx.txt',
                      'C-Nexus 7xxx.txt', 'C-Nexus 93xx-95xx.txt']
    if not check_required_files(required_files):
        return

    # Prompt for Pre or Post health check
    health_check_type = input("\nAre you doing a Pre or Post Health check? (Pre/Post): ").strip().lower()
    if health_check_type not in ["pre", "post"]:
        print("\nInvalid choice. Please enter 'Pre' or 'Post'.")
        return

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

    if equipment_choice == "1":
        device_file = "C_ASR9K.txt"

    if equipment_choice == "2":
        device_file = "C-CRS.txt"

    elif equipment_choice == "3":
        device_file = "CC_2960.txt"

    elif equipment_choice == "4":
        device_file = "CC_3850.txt"

    elif equipment_choice == "5":
        device_file = "CC_4500-X.txt"

    elif equipment_choice == "6":
        device_file = "CC_49xx.txt"

    elif equipment_choice == "7":
        device_file = "CC_65xx-76xx.txt"

    elif equipment_choice == "8":
        device_file = "C-Nexus 5xxx.txt"

    elif equipment_choice == "9":
        device_file = "C-Nexus 7xxx.txt"

    elif equipment_choice == "10":
        device_file = "C-Nexus 93xx-95xx.txt"
        
    else:
        print("\nInvalid choice. Please enter 1 - 10.")
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

    # Read devices from hosts.txt
    with open("hosts.txt", "r") as hf:
        hosts = [line.strip() for line in hf if line.strip()]

    # Track errors
    unreachable_hosts = []

    print("\nStarting health check for all hosts...\n")
    print("=" * 60)

    # Execute commands on each host
    for host in hosts:
        print(f"\nProcessing host: {host}")
        print("-" * 60)
        error = ssh_command(host, username, password, commands, ticket_number, health_check_type)
        if error:
            logger.error(f"Could not process host {host}. Error: {error}")
            unreachable_hosts.append(host)

    # Perform diff for Post health check
    if health_check_type == "post":
        print("\nPerforming diff for post health check...\n")
        for host in hosts:
            diff_output_file = os.path.join(ticket_number, f"{host}.out")
            with open(diff_output_file, "w") as diff_out:
                for command in commands:
                    command_safe = command.replace(' ', '_').replace('|', '').replace('/', '_')
                    pre_file = os.path.join(ticket_number, f"{host}-{command_safe}.pre")
                    post_file = os.path.join(ticket_number, f"{host}-{command_safe}.post")

                    if not os.path.exists(pre_file):
                        logger.warning(f"{pre_file} not found for {host}. Skipping diff.")
                        diff_out.write(f"{command} - [WARNING] Pre file not found.\n--------------------------------------------------------------\n")
                        continue

                    if not os.path.exists(post_file):
                        logger.warning(f"{post_file} not found for {host}. Skipping diff.")
                        diff_out.write(f"{command} - [WARNING] Post file not found.\n--------------------------------------------------------------\n")
                        continue

                    with open(pre_file, "r") as pre, open(post_file, "r") as post:
                        pre_lines = pre.readlines()
                        post_lines = post.readlines()
                        diff = difflib.unified_diff(pre_lines, post_lines, fromfile=pre_file, tofile=post_file)
                        diff_output = "".join(diff)
                        diff_out.write(f"Command: {command}\n")
                        if diff_output:
                            diff_out.write(diff_output)
                        else:
                            diff_out.write("[INFO] No differences detected.\n")
                        diff_out.write("\n--------------------------------------------------------------\n")

    # Summary of operations
    print("\nAll done! Have a nice day!")
    print("=" * 60)

    if unreachable_hosts:
        print("\nSummary of unreachable hosts:")
        print('')
        for host in unreachable_hosts:
            print(f" - {host}")
    else:
        print("\nAll hosts were processed successfully!")
        print('')

if __name__ == "__main__":
    main()
