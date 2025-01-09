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
    print("\nThis script requires the following files in the current directory:")
    print("- `hosts.txt`: List of hosts (one per line).")
    print("- `CC_49xx.txt`: Commands for Cisco Catalyst 49xx devices.")
    print("- `CC_65xx-76xx.txt`: Commands for Cisco Catalyst 65xx or 76xx devices.")
    print("- Additional files based on additional menu items to be added...\n")

    # Ask for the ticket number and create the directory
    ticket_number = input("Please enter the ticket that you are working on (e.g., 'NAASOPS-xxxx'): ").strip()
    if not ticket_number:
        print("Ticket number cannot be empty. Exiting.")
        return

    # Create directory for the ticket
    if not os.path.exists(ticket_number):
        os.makedirs(ticket_number)

    print(f"\nTicket number {ticket_number} has been recorded. Output will be saved in the corresponding directory.")

    # Check required files
    required_files = ["hosts.txt", "CC_49xx.txt", "CC_65xx-76xx.txt"]
    if not check_required_files(required_files):
        return

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
    elif equipment_choice == "2":
        device_file = "CC_65xx-76xx.txt"
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
        for command in commands:
            command_safe = command.replace(' ', '_').replace('|', '').replace('/', '_')
            diff_output_file = os.path.join(ticket_number, "diff.out")

            with open(diff_output_file, "a") as diff_out:
                for host in hosts:
                    pre_file = os.path.join(ticket_number, f"{host}-{command_safe}.pre")
                    post_file = os.path.join(ticket_number, f"{host}-{command_safe}.post")

                    if not os.path.exists(pre_file):
                        logger.warning(f"{pre_file} not found for {host}. Skipping diff.")
                        continue

                    if not os.path.exists(post_file):
                        logger.warning(f"{post_file} not found for {host}. Skipping diff.")
                        continue

                    with open(pre_file, "r") as pre, open(post_file, "r") as post:
                        pre_lines = pre.readlines()
                        post_lines = post.readlines()
                        diff = difflib.unified_diff(pre_lines, post_lines, fromfile=pre_file, tofile=post_file)
                        diff_output = "".join(diff)
                        if diff_output:
                            diff_out.write(f"{command} - Host: {host}\n")
                            diff_out.write(diff_output)
                            diff_out.write("\n-----------------\n")
                        else:
                            diff_out.write(f"{command} - Host: {host}\n[INFO] No differences detected.\n")
                            diff_out.write("\n-----------------\n")

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
