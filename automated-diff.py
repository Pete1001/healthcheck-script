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

import os
import logging
import difflib
import paramiko
import time
from getpass import getpass

# Global separator for consistent formatting
SEPARATOR = '-' * 60
COMMAND_DELAY = 3  # Seconds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("healthcheck.log"),
        logging.StreamHandler()
    ]
)
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
    Additionally, create a consolidated .precheck or .postcheck file.
    """
    try:
        logger.info(f"Attempting to connect to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=20)
        logger.info(f"Successfully connected to {host}.")

        # Open an interactive shell session
        ssh_shell = ssh.invoke_shell()
        ssh_shell.settimeout(30)  # Timeout for shell interactions

        # Check if the shell is active
        if not ssh_shell.active:
            raise RuntimeError("SSH shell session is not active.")

        # Add a delay to ensure the shell is ready
        time.sleep(5)  # Initial delay for shell readiness
        while ssh_shell.recv_ready():  # Flush any residual output
            ssh_shell.recv(65535)

        # Clear the logging buffer before executing commands
        logger.info(f"[{host}] Clearing logging buffer...")
        ssh_shell.send("clear logging\n")
        time.sleep(COMMAND_DELAY)
        while ssh_shell.recv_ready():  # Flush any remaining buffer data
            ssh_shell.recv(65535)

        # Create consolidated .precheck or .postcheck file
        consolidated_file = None
        if health_check_type == "pre":
            consolidated_file = os.path.join(ticket_number, f"{host}.precheck")
        elif health_check_type == "post":
            consolidated_file = os.path.join(ticket_number, f"{host}.postcheck")

        if consolidated_file:
            logger.info(f"Consolidated file will be created: {consolidated_file}")

        # Execute commands
        for command in commands:
            logger.info(f"[{host}] Running command: {command}")
            ssh_shell.send(command + "\n")
            time.sleep(COMMAND_DELAY + 2)  # Allow additional time for long outputs

            # Increase buffer size and retrieve command output
            output = ""
            if ssh_shell.recv_ready():
                while ssh_shell.recv_ready():
                    output += ssh_shell.recv(65535).decode('utf-8')

            # Ensure output is not empty
            if not output.strip():
                logger.warning(f"[{host}] No output received for command: {command}")
                continue

            # Write each command's output to a separate file
            command_safe = command.replace(' ', '_').replace('|', '').replace('/', '_')
            output_file = os.path.join(ticket_number, f"{host}-{command_safe}.{health_check_type}")
            try:
                with open(output_file, "w") as out:
                    out.write(output)
                logger.info(f"[{host}] Output written to {output_file}")
            except IOError as e:
                logger.error(f"[{host}] Failed to write output file: {output_file}. Error: {e}")

            # Append to consolidated .precheck or .postcheck file
            if consolidated_file:
                try:
                    with open(consolidated_file, "a") as consolidated:
                        consolidated.write(f"Command: {command}\n{output}\n{SEPARATOR}\n")
                    logger.info(f"[{host}] Command output appended to {consolidated_file}.")
                except IOError as e:
                    logger.error(f"[{host}] Failed to write to consolidated file: {consolidated_file}. Error: {e}")

        ssh.close()
        logger.info(f"SSH session closed for {host}.")
        return None  # No errors

    except paramiko.ssh_exception.AuthenticationException:
        return "[ERROR] Authentication failed. Please check your username or password."

    except paramiko.ssh_exception.NoValidConnectionsError:
        return "[ERROR] Unable to connect to host. Check if the device is reachable."

    except Exception as e:
        return f"[ERROR] {e}"

def main():
    print("\nAutomated Pre and Post Health Check Script")
    print("=" * 80)
    print("\nThis script requires the following files in the current directory:")
    print('')
    print("         -`hosts.txt`:             - List of hosts (one per line).")
    print("         -`C_ASR9K.txt`:           - Cisco ASR9K")
    print("         -`C-CRS.txt`:             - Cisco CRS")
    print("         -`CC_2960.txt`:           - Cisco Catalyst 2960")
    print("         -`CC_3850.txt`:           - Cisco Catalyst 3850")
    print("         -`CC_4500-X.txt`:         - Cisco Catalyst 4500-X")
    print("         -`CC_49xx.txt`:           - Cisco Catalyst 49xx")
    print("         -`CC_65xx-76xx.txt`:      - Cisco Catalyst 65xx or 76xx")
    print("         -`C-Nexus 5xxx.txt`:      - Cisco Nexus 5xxx")
    print("         -`C-Nexus 7xxx.txt`:      - Cisco Nexus 7xxx")
    print("         -`C-Nexus 93xx-95xx.txt`: - Cisco Nexus 93xx/95xx")
    print('')
    print("\nEnsure all required files are present before proceeding.\n")
    print("=" * 80)
    print('Please NOTE:')
    print("=" * 80)
    print('')
    print("You can only use this for 'LIKE' devices, so ensure that hosts.txt only contains devices of a single 'type'")
    print('Healththeck and Pre-check output files of all commands are written to individual files with `.pre` extension (bunch of individual files)')
    print('Healthcheck and Post-check output files of all commands are written to individual files with `.post` extension (bunch of individual files)')
    print('')
    print("-" * 80)
    print('Consolidated output of all commands for Healtcheck and Pre-check is written to a single file (for each device) with `.precheck` extension')
    print('Consolidated output of all commands for Healtcheck and Post-check is written to a single file (for each device) with `.postcheck` extension')
    print('')
    print('Consolidated `diff` between Pre and Post Healthchecks as well as between Pre and Post checks is written to a file with `.out` extension (for each device)')
    print("-" * 80)
    print('')
    print("=" * 80)

    # Ask for the ticket number and create the directory
    ticket_number = input("Please enter the ticket that you are working on (e.g., 'NAASOPS-xxxx'): ").strip()
    if not ticket_number:
        print("Ticket number cannot be empty. Exiting.")
        logger.error("Ticket number not provided. Exiting.")
        return

    # Create directory for the ticket
    try:
        if not os.path.exists(ticket_number):
            os.makedirs(ticket_number)
        logger.info(f"Directory {ticket_number} created successfully.")
    except OSError as e:
        print(f"\nError: Unable to create directory {ticket_number}. {e}")
        logger.error(f"Failed to create directory {ticket_number}: {e}")
        return

    # Validate required files
    required_files = ["hosts.txt"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"\nError: {file} is missing.")
            logger.error(f"Required file {file} is missing. Exiting.")
            return

    # Prompt for Pre or Post health check
    print("\nAre you performing a Pre or Post health check?")
    print('')
    print("  - Pre: Collects initial configuration data.")
    print("  - Post: Collects final configuration data and compares it to Pre.")
    print('')
    health_check_type = input("Enter your choice (Pre/Post): ").strip().lower()

    if health_check_type not in ["pre", "post"]:
        print("\nInvalid choice. Please enter 'Pre' or 'Post'.")
        logger.error("Invalid health check type entered. Exiting.")
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

    device_file = device_files.get(equipment_choice)
    if not device_file:
        print("\nInvalid choice. Please enter a number between 1 and 10.")
        logger.error("Invalid equipment type selected. Exiting.")
        return

    # Validate command file
    if not os.path.exists(device_file):
        print(f"\nError: {device_file} not found.")
        logger.error(f"Command file {device_file} is missing. Exiting.")
        return

    with open(device_file, "r") as f:
        commands = f.read().splitlines()

    if not commands:
        print(f"\nError: The file {device_file} is empty or contains invalid commands.")
        logger.error(f"The file {device_file} is empty or improperly formatted. Exiting.")
        return

    # Validate COMMAND_DELAY value
    if COMMAND_DELAY < 1 or COMMAND_DELAY > 10:
        logger.warning("COMMAND_DELAY is set to an unusual value. Adjust if necessary.")

    # Read hosts from hosts.txt
    with open("hosts.txt", "r") as hf:
        hosts = [line.strip() for line in hf if line.strip()]

    if not hosts:
        print("\nError: hosts.txt is empty or improperly formatted. Ensure one hostname or IP per line.")
        logger.error("hosts.txt is empty or improperly formatted. Exiting.")
        return

    # SSH credentials
    username = input("\nEnter your SSH username: ").strip()
    password = getpass("Enter your SSH password: ")

    # Process each host
    unreachable_hosts = []
    print("\nStarting health check for all hosts...\n")
    print("=" * 60)

    for host in hosts:
        print(f"\nProcessing host: {host}")
        print(SEPARATOR)
        error = ssh_command(host, username, password, commands, ticket_number, health_check_type)
        if error:
            logger.error(f"Could not process host {host}. Error: {error}")
            unreachable_hosts.append(host)

    # Post health check: Perform diff
    if health_check_type == "post":
        print("\nPerforming diff for post health check...\n")
        for host in hosts:
            diff_output_file = os.path.join(ticket_number, f"{host}.out")
            with open(diff_output_file, "w") as diff_out:
                logger.info(f"Starting diff for host {host}, output will be saved to {diff_output_file}")
                for command in commands:
                    command_safe = command.replace(' ', '_').replace('|', '').replace('/', '_')
                    pre_file = os.path.join(ticket_number, f"{host}-{command_safe}.pre")
                    post_file = os.path.join(ticket_number, f"{host}-{command_safe}.post")

                    if not os.path.exists(pre_file):
                        logger.warning(f"{pre_file} not found for {host}. Skipping diff.")
                        diff_out.write(f"{command} - [WARNING] Pre file not found.\n{SEPARATOR}\n")
                        continue

                    if not os.path.exists(post_file):
                        logger.warning(f"{post_file} not found for {host}. Skipping diff.")
                        diff_out.write(f"{command} - [WARNING] Post file not found.\n{SEPARATOR}\n")
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
                        diff_out.write(f"\n{SEPARATOR}\n")
                logger.info(f"Diff results for host {host} saved to {diff_output_file}")

    # Summary of processed hosts
    print("\nSummary of Processed Hosts:")
    print('')
    processed_count = len(hosts) - len(unreachable_hosts)
    failed_count = len(unreachable_hosts)

    print(f" Processed {processed_count} hosts successfully.")
    if failed_count > 0:
        print(f"    -Failed to process {failed_count} hosts:")
        print('')
        for host in unreachable_hosts:
            print(f" - {host}")
        # Log unreachable hosts
        logger.info(f"Failed to process {failed_count} hosts: {', '.join(unreachable_hosts)}")
    else:
        print("    -No failures. All hosts were processed successfully.")
        print('')
        logger.info("All hosts were processed successfully.")

    if health_check_type == "pre":
        logger.info(f"Pre-check operation completed for all hosts. Outputs saved in {ticket_number} directory.")

    if health_check_type == "post":
        logger.info(f"Post-check operation completed for all hosts. Diffs saved in {ticket_number} directory.")

if __name__ == "__main__":
    main()
