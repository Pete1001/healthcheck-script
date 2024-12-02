
# Health Check Script

## Overview
This script automates Pre and Post health checks for network devices, specifically for Cisco 2948 and Cisco CSR switches. 
It uses SSH to connect to the device, runs specified commands, saves the outputs, and provides a comparison between Pre and Post health checks.

---

## Features
1. **Interactive Menu**:
   - Allows users to select between Pre and Post health checks.
   - Lets users choose the type of device: Cisco 2948 or Cisco CSR.

2. **Automated SSH Command Execution**:
   - Reads commands from pre-defined files (`2948.txt` or `CSR.txt`).
   - Connects to the device using SSH and executes the commands.

3. **Output Management**:
   - Saves Pre-check outputs to `<device>.pre` files.
   - Saves Post-check outputs to `<device>.aft` files.

4. **Difference Comparison**:
   - Compares the Pre and Post outputs using a unified diff format.
   - Saves the comparison results in a `.out` file.

---

## Prerequisites
- **Python 3.x**
- **SSH and sshpass**: Ensure `sshpass` is installed for password-based SSH.
- **Network Access**: The script requires access to the network devices.
- **Command Files**: Provide device-specific command files (`2948.txt` and `CSR.txt`) with one command per line.

---

## File Descriptions
### Command Files
- **2948.txt**: Contains commands for Cisco 2948 switches.
- **CSR.txt**: Contains commands for Cisco CSR switches.

Example content for `2948.txt`:
```
show version
show ip interface brief
show running-config
```

Example content for `CSR.txt`:
```
show version
show interfaces description
show ip route
```

### Output Files
- **Pre-check Output**: Saved as `2948.pre` or `CSR.pre` depending on the selected device.
- **Post-check Output**: Saved as `2948.aft` or `CSR.aft` depending on the selected device.
- **Diff Output**: Saved as `Cisco_2948.out` or `Cisco_CSR.out` depending on the selected device.

---

## Usage
1. Run the script:
   ```bash
   python3 health_check_script.py
   ```

2. Follow the prompts:
   - Choose `Pre` or `Post` health check.
   - Select the device type (Cisco 2948 or Cisco CSR).
   - Enter the device hostname/IP and SSH credentials.

3. Output files will be generated in the current directory.

4. For Post health checks, the script will compare Pre and Post outputs and display the differences on the screen and save them to a `.out` file.

---

## Example Run

### Pre Health Check
1. The script prompts:
   ```
   Are you doing a Pre or Post Health check? (Pre/Post): Pre
   Select the equipment type:
   1. Cisco 2948
   2. Cisco CSR
   Enter your choice (1/2): 1
   ```

2. Output is saved to `2948.pre`.

### Post Health Check
1. The script prompts:
   ```
   Are you doing a Pre or Post Health check? (Pre/Post): Post
   Select the equipment type:
   1. Cisco 2948
   2. Cisco CSR
   Enter your choice (1/2): 1
   ```

2. Output is saved to `2948.aft`.
3. Diff results are displayed and saved to `Cisco_2948.out`.

---

## Important Notes
- **Security**: The script uses `sshpass` for password authentication. Avoid using it on sensitive systems.
- **Testing**: Always test the script in a non-production environment first.
- **Device Access**: Ensure proper permissions and access to the target devices.

---

## Contact
For questions or suggestions, feel free to reach out!

---

## License
This script is provided as-is without warranty. Use at your own risk.
