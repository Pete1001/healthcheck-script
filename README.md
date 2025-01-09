# Automated Healthcheck and Pre / Post Check Script with automated Post Diff reporting Script

## Overview
The **Automated Healthcheck and Pre / Post Check Script with automated Post Diff reporting** is a Python-based tool designed to streamline network device health checks. It allows for pre- and post-checks by connecting to devices over SSH, executing a series of commands, saving output files, and generating detailed comparisons.

This script is particularly useful for network engineers performing routine checks, troubleshooting, or validating configurations during change management processes.

---

## Features
- **Automated SSH Connections:** Connect to multiple devices using `hosts.txt`.
- **Customizable Commands:** Read commands from input files specific to device types.
- **Output Management:** Save command output for each device and command separately in `.pre` and `.post` files.
- **Detailed Diff Reports:** Compare pre- and post-check outputs and generate consolidated `.out` files per device.
- **Ticket-based Organization:** All outputs are saved in a directory named after the provided ticket.
- **Warnings for Missing Files:** Alerts for missing `.pre` or `.post` files during diff operations.

---

## Prerequisites
1. Python 3.x installed on your system.
2. The following Python libraries:
   - `paramiko`
   - `difflib`
3. Required files:
   - `hosts.txt`: Contains a list of hostnames or IP addresses.
   - Device-specific command files (e.g., `CC_49xx.txt`, `CC_65xx-76xx.txt`).

---

## Installation
1. Clone or download this repository to your local machine.
2. Install required Python packages:
   ```bash
   pip install paramiko
   ```
3. Ensure all required files (`hosts.txt`, device command files) are in the same directory as the script.

---

## Usage
### Running the Script
Run the script using Python:
```bash
python3 automated-diff.py
```

### Script Flow
1. **Input Ticket Number**
   The script prompts you to enter the ticket number:
   ```
   Please enter the ticket that you are working on (e.g., 'NAASOPS-xxxx'):
   ```
   A directory with the provided ticket name is created.

2. **Select Health Check Type**
   Choose whether you are performing a Pre or Post health check:
   ```
   Are you doing a Pre or Post Health check? (Pre/Post):
   ```

3. **Select Device Type**
   Choose the device type to determine the command file:
   ```
   Select the equipment type:
   1. Cisco Catalyst 49xx
   2. Cisco Catalyst 65xx or 76xx
   ```

4. **Provide SSH Credentials**
   Enter your SSH username and password.

5. **Command Execution**
   The script connects to each host listed in `hosts.txt`, executes commands, and saves outputs as `.pre` or `.post` files.

6. **Diff Operation** (Post Check Only)
   For Post checks, `.pre` and `.post` files are compared, and results are saved in a consolidated `.out` file per host.

### Example Command Files
**`CC_49xx.txt`**
```
show version
show run | include hostname
show ip interface brief
```

**`hosts.txt`**
```
192.168.1.1
192.168.1.2
10.0.0.1
```

---

## Example Outputs
### `.pre` or `.post` File
For a host `192.168.1.1` and command `show ip interface brief`, the file `192.168.1.1-show_ip_interface_brief.pre` may contain:
```
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/1     192.168.1.1     YES manual up                    up
GigabitEthernet0/2     unassigned      YES unset  administratively down down
```

### `.out` File
For a host `192.168.1.1`, the consolidated `.out` file may contain:
```
Command: show version
[INFO] No differences detected.
-------------------------------

Command: show run | include hostname
- hostname OLD_HOSTNAME
+ hostname NEW_HOSTNAME
-------------------------------

Command: show ip interface brief
- GigabitEthernet0/2     unassigned      YES unset  administratively down down
+ GigabitEthernet0/2     10.0.0.2        YES manual up                    up
-------------------------------
```

---

## Troubleshooting
### Common Issues
1. **Authentication Failure:**
   Ensure the correct username and password are used.
2. **Missing Command Files:**
   Verify that the device-specific command file exists in the directory.
3. **Connection Errors:**
   Check network reachability and SSH configurations on the devices.

---

## Contributing
If you have suggestions or want to contribute, feel free to fork this repository and create a pull request. For issues, open a GitHub issue.

---

## License
This project is licensed under the MIT License by Pete Link. See `LICENSE` for details.

---

## Contact
For questions or feedback, please reach out to Pete Link or open a GitHub issue:  https://www.linkedin.com/in/petelink/