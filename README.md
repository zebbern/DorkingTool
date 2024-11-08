# **PH4N70M - Dorking Tool**
![PH4N70M Logo](https://path-to-your-logo.png) <!-- Optional: Add a logo image -->

**PH4N70M** is a GUI-based Python tool that simplifies and automates Google dorking for penetration testers, security researchers, and anyone interested in advanced web searches. PH4N70M offers extensive proxy support, automated query management, live URL validation, and rich site information tools.

> **Disclaimer**: This tool is intended for educational purposes and legitimate use only. Unauthorized or malicious use of this tool is prohibited.

---

## **Table of Contents**

- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---

## **Features**

- **Automated Google Dorking**: Effortlessly search for sensitive information across the web using custom dork queries.
- **Proxy Support**: Add and manage proxies to protect privacy and reduce rate-limiting.
- **Live URL Validation**: Automatically check if retrieved URLs are active, ensuring high-quality search results.
- **Dork Query Management**: Load, edit, and auto-replace placeholders in dork queries with a few clicks.
- **Comprehensive Site Information**: Gather WHOIS data, perform Ping and Traceroute, and conduct Reverse IP Lookups on targeted sites.
- **User-Agent Rotation**: Customize and rotate user-agent strings to mimic different devices.
- **Advanced Multi-threading**: Execute searches and validations in parallel for maximum efficiency.

---

## **Screenshots**

| Feature         | Screenshot |
|-----------------|------------|
| **Main Interface** | ![Main Interface](https://path-to-main-interface-screenshot.png) |
| **Proxy Management** | ![Proxy Management](https://path-to-proxy-screenshot.png) |
| **URL Validation** | ![URL Validation](https://path-to-url-validation-screenshot.png) |

---

## **Installation**

### **1. Clone the Repository**
```
git clone https://github.com/yourusername/PH4N70M.git
cd PH4N70M
```
2. Install Dependencies
Make sure you have Python 3.6+ installed. Install required packages via pip:
```
pip install -r requirements.txt
```
If this command fails due to package conflicts or other issues, you can try installing each package individually using the following commands:
```
pip install requests==2.26.0
pip install beautifulsoup4==4.10.0
pip install validators==0.18.2
pip install python-whois==0.7.3
pip install scapy==2.4.5
```
Note: If you encounter issues with scapy, make sure you have the necessary permissions or try installing it with sudo pip install scapy (on macOS/Linux).

Additional Backup Installation Instructions
For users who continue to face issues with the installation, suggest they set up a virtual environment to avoid conflicts with their existing Python packages.

Create a Virtual Environment (optional but recommended):
```
python -m venv ph4n70m_env
source ph4n70m_env/bin/activate   # On macOS/Linux
ph4n70m_env\Scripts\activate      # On Windows
Install Dependencies in the Virtual Environment:
```
Then run
```
pip install -r requirements.txt
```
3. Run the Application
```
python run.py
```
Usage
Load Dorks: Click on "Load Dorks from File" to select a file with dork queries.
Auto Replace Placeholders: Use the "Auto Replace Sosials From Dork" and "Auto Replace Sites From Dork" buttons to replace placeholders like "Name Or Username" and "site.com" with specific values.
Manage Proxies: Go to the "Proxies" tab to load and manage proxies for anonymous searching.
URL Validation: Enable URL validation to automatically check the status of each retrieved URL.
View Site Information: Use tools like WHOIS, Ping, Traceroute, and Reverse IP Lookup for deeper insights into specific domains.
Example Commands
Load and Replace Dorks: Loads a dork file and replaces "Name Or Username" placeholders with a specified name.
Load and Replace Sites: Loads a file with "site.com" placeholders and replaces them with a chosen site name.
Configuration
User-Agent Management: Customize user-agent strings in settings for advanced device simulation.
Threading and Timeout Settings: Adjust the number of concurrent threads and set timeouts for proxy validation in the Settings tab.
File Structure
run.py: Main entry point to start the PH4N70M application.
config.json: Configuration file containing default settings (user-agents, threading).
requirements.txt: Lists all dependencies required by PH4N70M.
src/: Contains core functionality code, helper classes, and utility functions.
LICENSE: Proprietary license information.

Contributing
Contributions are welcome! To contribute:

Fork the repository
Create a new feature branch
```
git checkout -b feature/NewFeature
```
Commit your changes
```
git commit -m "Add new feature"
```
Push the branch
```
git push origin feature/NewFeature
```
Open a Pull Request
Before starting major work, please open an issue to discuss your ideas.

Contact
For questions or support, please contact [Your Email Address].

Acknowledgments
This project was inspired by open-source dorking tools and built with a focus on simplicity, efficiency, and privacy.
Special thanks to the open-source community for providing inspiration and resources for project development.


