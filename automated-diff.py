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

# Add color codes for different log levels
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_colored(text, color):
    """
    Prints the given text in the specified color.
    """
    print(f"{color}{text}{Color.RESET}")

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

spinner = spinning_cursor()

def validate_username(username):
    """
    Validate the username to ensure it does not contain spaces.
    """
    if ' ' in username:
        print_colored("[ERROR] Invalid username. Spaces are not allowed.", Color.RED)
        return False
    return True

def ping_host(host):
    """
    Ping a host to check if it is reachable. Returns True if reachable, False otherwise.
    """
    try:
        response = subprocess.run(
            ['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if response.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        return False

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
        
        # Add a brief pause to ensure authentication is complete
        time.sleep(2)  # Short pause for authentication to settle
        
        # Check if the connection was successful (authentication check)
        if ssh.get_transport().is_active():
            print_colored(f"[INFO] Successfully authenticated to {host}.", Color.GREEN)
        else:
            print_colored(f"[ERROR] Authentication failed for {host}. Please check your username/password.", Color.RED)
            logger.error(f"Authentication failed for {host}. Exiting.")
            return "[ERROR] Authentication failed."
        
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

        # Send a marker command to confirm readiness
        logger.info(f"[{host}] Sending readiness marker.")
        ssh_shell.send("\n\n\n")  # Send 3x newlines to clear and prepare the shell
        time.sleep(2)
        while ssh_shell.recv_ready():
            readiness_output = ssh_shell.recv(65535).decode('utf-8')
        logger.info(f"[{host}] Readiness marker output: {readiness_output}")

        # Clear the logging buffer
        logger.info(f"[{host}] Clearing logging buffer.")
        ssh_shell.send("\n\n\nclear logging\n\n\n")  # Send 3x newlines before and after the command
        time.sleep(3)
        while ssh_shell.recv_ready():
            ssh_shell.recv(65535)

        # Execute commands
        for index, command in enumerate(commands):
            print(next(spinner), end='\r')  # Show spinning cursor on screen during execution
            sys.stdout.flush()

            while ssh_shell.recv_ready():
                ssh_shell.recv(65535)

            # Send 3x newlines before the command
            ssh_shell.send("\n\n\n")
            time.sleep(0.1)

            # Send the command and 3x newlines after
            ssh_shell.send(command + "\n\n\n")
            logger.debug(f"[{host}] Command sent: {command}")

            # Add an additional delay for the first command
            if index == 0:
                time.sleep(COMMAND_DELAY + 5)
            else:
                time.sleep(COMMAND_DELAY + 2)

            # Retrieve the output
            output = ""
            if ssh_shell.recv_ready():
                while ssh_shell.recv_ready():
                    output += ssh_shell.recv(65535).decode('utf-8')

            # Ensure output is logged even if empty
            if not output.strip():
                print_colored(f"[INFO] No output received for command: {command}", Color.YELLOW)
                logger.warning(f"[{host}] No output received for command: {command}")
                output = "[INFO] No output received."
            else:
                print_colored(f"[INFO] Command completed: {command}", Color.GREEN)

            # Write each command's output to a separate file
            command_safe = command.replace(' ', '_').replace('|', '').replace('/', '_')
            output_file = os.path.join(ticket_number, f"{host}-{command_safe}.{health_check_type}")
            try:
                with open(output_file, "w") as out:
                    out.write(output)
                logger.info(f"[{host}] Output written to {output_file}")
            except IOError as e:
                logger.error(f"[{host}] Failed to write output file: {output_file}. Error: {e}")
                
        ssh.close()
        logger.info(f"SSH session closed for {host}.")
        return None  # No errors
    except paramiko.ssh_exception.AuthenticationException:
        error_msg = "[ERROR] Authentication failed. Please check your username or password."
        print_colored(error_msg, Color.RED)
        return error_msg
    except paramiko.ssh_exception.NoValidConnectionsError:
        error_msg = "[ERROR] Unable to connect to host. Check if the device is reachable."
        print_colored(error_msg, Color.RED)
        return error_msg
    except Exception as e:
        error_msg = f"[ERROR] {e}"
        print_colored(error_msg, Color.RED)
        return error_msg

# Main program to execute health checks
def main():
    # ... (rest of your code from the main function)
    pass

if __name__ == "__main__":
    main()
