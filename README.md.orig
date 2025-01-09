# Automated Pre and Post Diff Check Script

## Description

This script automates pre and post health checks for network devices, allowing engineers to validate device configurations and detect changes efficiently. It logs into devices via SSH, executes predefined commands, and saves outputs. Additionally, it compares pre-check and post-check outputs and generates a detailed diff file for easy review.

This script is designed to work with multiple hosts listed in a `hosts.txt` file and leverages specific command sets for different types of network devices (e.g., Cisco Catalyst). It supports error handling, detailed logging, and an easy-to-read output format.

---

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Contributing](#contributing)
- [Testing](#testing)
- [Known Issues](#known-issues)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Features

- Executes pre-check and post-check commands on multiple devices via SSH.
- Saves command outputs to `.pre` or `.post` files.
- Compares `.pre` and `.post` files, generating `.out` files with detailed diffs.
- Logs errors.
- Prompts for user name and password.
- Supports different command sets for different device types.  (via separate menu items, which may need to be added)
- Error handling for unreachable hosts or SSH authentication failures.

---

## Installation

1. Clone the repository https://github.com/Pete1001/healthcheck-script.git
   or download the file: `https://github.com/Pete1001/healthcheck-script/blob/main/automated-diff.py`
2. Navigate to the project directory: `cd automated-diff-script`
3. Installing dependencies (if required): `pip install -r requirements.txt`
4. Ensure all required files (`hosts.txt`, `CC_49xx.txt`, `CC_65xx-76xx.txt`) are in the same directory.

---

## Usage

Run the script to perform pre-checks and then run it again to perform post-checks on network devices. The output is saved in `.pre` or `.post` files.  The differences are written to `.out` files when the script is executed a second time. The process is interactive, requiring user input for the check type, device type, and SSH credentials.

1. Execute the script: `python3 automated_diff.py`
2. Follow the prompts:
   - Specify whether you are performing a pre-check or post-check.
   - The script will load the appropriate command set based on the option selected.
   - Enter SSH credentials (username and password).
3. Review Outputs:
   - Pre-check outputs (1st run of the script) are saved as `<hostname>.<device>.pre`.
   - Post-check outputs (2nd run of the script) are saved as `<hostname>.<device>.post`.
   - Also, on the 2nd run of the script, the differences between pre and post outputs are saved as `<hostname>.<device>.out`.

---

## Examples

### Output Examples

Pre-check output (`.pre`):
--- Output from 192.168.1.1 ---
Command: show version
[command output here]
--------------------------------------------------

Post-check output (`.post`):
--- Output from 192.168.1.1 ---
Command: show version
[command output here]
--------------------------------------------------

Diff output (`.out`):
==== DIFF RESULTS ====
Comparison of Pre-check (192.168.1.1.49xx.pre) and Post-check (192.168.1.1.49xx.post):
--- 192.168.1.1.49xx.pre
+++ 192.168.1.1.49xx.post
@@ -1,5 +1,5 @@
< Differences highlighted here >

==== END OF RESULTS ====

---

## Configuration

### Required Files

1. `hosts.txt`: A file containing a list of hosts (one per line) to be processed by the script.
2. Command Files:
   - `CC_49xx.txt`: Contains commands for Cisco Catalyst 49xx devices.
   - `CC_65xx-76xx.txt`: Contains commands for Cisco Catalyst 65xx/76xx devices.
   - `other files`: Based on additional menu items.

### SSH Credentials

The script will prompt for your SSH username and password during execution. Ensure that SSH access is enabled and properly configured for all devices listed in `hosts.txt`.

---

## How It Works

1. **Pre-check**: The script logs into each device in `hosts.txt`, runs the commands specified in the appropriate command file, and saves the output to a `.pre` file.
2. **Post-check**: Similar to pre-check, but the outputs are saved to a `.post` file.
3. **Diff Generation**: For post-checks, the script compares the `.pre` and `.post` files and saves the differences to a `.out` file for each host.

---

## Contributing

We welcome contributions to enhance the functionality or fix issues. Please follow these steps:

1. Fork the repository: `git checkout -b feature/your-feature-name`
2. Commit your changes and push: `git push origin feature/your-feature-name`
3. Open a pull request.

---

## Testing

Run unit tests to ensure that all functionalities work as expected.

---

## Known Issues

- Requires Python 3.8+.
- Only tested with Cisco devices; compatibility with other vendors might be limited.
- Limited multi-threading support; hosts are processed sequentially.

---

## License

MIT License Copyright (c) 2024 [Pete Link] This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Paramiko](https://github.com/paramiko/paramiko) for SSH implementation.

---

## Contact

For questions or suggestions, contact [Pete Link] via LinkedIn:  https://github.com/Pete1001
