import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import json
import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import requests
from googlesearch import search
import webbrowser
import whois
import dns.resolver
import subprocess
from bs4 import BeautifulSoup
import socket
import ssl

# Configure logging
logging.basicConfig(
    filename='ph470m_gui.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load configuration
CONFIG_FILE = 'config.json'
if not os.path.isfile(CONFIG_FILE):
    # Create default config if not exists
    default_config = {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0"
        ],
        "default_threads": 10,
        "proxy_validation_timeout": 5
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

# User-Agent list for rotation from config
USER_AGENTS = config.get("user_agents", [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0"
])

DEFAULT_THREADS = config.get("default_threads", 10)
PROXY_VALIDATION_TIMEOUT = config.get("proxy_validation_timeout", 5)

# Tooltip class for providing tips
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#4B4B4B", foreground="white",
                         relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class PH470MGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PH4N70M")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)
        self.root.configure(bg="#2E2E2E")  # Dark background

        self.stop_event = threading.Event()

        # Initialize variables
        self.dorks = []
        self.proxies = []
        self.valid_proxies = []
        self.output_mode = tk.StringVar(value='none')
        self.validate_urls_flag = tk.BooleanVar()
        self.num_results = tk.IntVar(value=10)
        self.threads = tk.IntVar(value=DEFAULT_THREADS)
        self.output_file = tk.StringVar(value='results.txt')
        self.live_dorks_limit = tk.IntVar(value=10)  # Number of dorks to fetch
        self.selected_dorks_file = tk.StringVar(value='')  # Path to selected dorks file

        # Create UI components
        self.create_widgets()

    def create_widgets(self):
        # Create Notebook (Tabbed Interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Style the Notebook
        style = ttk.Style()
        style.theme_use('clam')  # More customizable
        style.configure("TNotebook", background="#2E2E2E")
        style.configure("TNotebook.Tab", background="#3C3F41", foreground="white", padding=[10, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", "#4CAF50")],
                  foreground=[("selected", "white")])

        # Create Frames for each tab using tk.Frame for background customization
        self.control_panel_tab = tk.Frame(self.notebook, bg="#2E2E2E")
        self.proxies_tab = tk.Frame(self.notebook, bg="#2E2E2E")
        self.settings_tab = tk.Frame(self.notebook, bg="#2E2E2E")
        self.find_dorks_tab = tk.Frame(self.notebook, bg="#2E2E2E")  # Renamed from Live Dorks
        self.site_info_tab = tk.Frame(self.notebook, bg="#2E2E2E")
        self.results_tab = tk.Frame(self.notebook, bg="#2E2E2E")
        self.about_tab = tk.Frame(self.notebook, bg="#2E2E2E")

        self.notebook.add(self.control_panel_tab, text='Control Panel')
        self.notebook.add(self.proxies_tab, text='Proxies')
        self.notebook.add(self.settings_tab, text='Settings')
        self.notebook.add(self.find_dorks_tab, text='Find Dorks')  # Renamed
        self.notebook.add(self.site_info_tab, text='Site Info')
        self.notebook.add(self.results_tab, text='Search Results')
        self.notebook.add(self.about_tab, text='About')

        # Create content for each tab
        self.create_control_panel()
        self.create_proxies()
        self.create_settings()
        self.create_find_dorks()
        self.create_site_info()
        self.create_search_results()
        self.create_about()

    def create_control_panel(self):
        # Control Panel Tab Content
        # Start and Stop Buttons and GitHub Link
        button_frame = tk.Frame(self.control_panel_tab, bg="#2E2E2E")
        button_frame.pack(pady=10, anchor='nw', padx=10)

        self.start_btn = tk.Button(button_frame, text="Start Search", command=self.start_search, bg="#4CAF50", fg="white", width=12, height=2, font=("Helvetica", 10, "bold"))
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.start_btn, "Begin the search process based on the provided settings.")

        self.stop_btn = tk.Button(button_frame, text="Stop Search", command=self.stop_search, bg="#F44336", fg="white", width=12, height=2, font=("Helvetica", 10, "bold"), state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.stop_btn, "Terminate the ongoing search process.")

        # Clear Search Results Button
        clear_results_btn = tk.Button(button_frame, text="Clear Results", command=self.clear_search_results, bg="#9E9E9E", fg="white", width=12, font=("Helvetica", 10, "bold"))
        clear_results_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(clear_results_btn, "Clear the Search Results console.")

        # GitHub Link
        github_label = tk.Label(button_frame, text="ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤGitHub:https://github.com/zebbern", fg="#2196F3", bg="#2E2E2E", cursor="hand2", font=("Helvetica", 14, "underline"))
        github_label.pack(side=tk.LEFT, padx=20)
        github_label.bind("<Button-1>", lambda e: self.open_github())

        # Dork Queries Frame
        dorks_frame = tk.LabelFrame(self.control_panel_tab, text="Dork Queries", padx=10, pady=10, bg="#2E2E2E", fg="white")
        dorks_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.dorks_text = scrolledtext.ScrolledText(dorks_frame, width=100, height=10, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.dorks_text.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Configure grid weights
        dorks_frame.grid_rowconfigure(0, weight=1)
        dorks_frame.grid_columnconfigure(0, weight=1)

        # Persistent Tip below the text box
        dork_tip = tk.Label(dorks_frame, text="Enter dork queries here, one per line or separated by commas.", bg="#2E2E2E", fg="light gray", font=("Helvetica", 9))
        dork_tip.grid(row=1, column=0, sticky=tk.W, padx=5)

        # Load Dorks Button
        load_dorks_btn = tk.Button(dorks_frame, text="Load Dorks from File", command=self.load_dorks, bg="#4CAF50", fg="white", width=20, font=("Helvetica", 9, "bold"))
        load_dorks_btn.grid(row=2, column=0, sticky=tk.E, padx=5, pady=5)
        ToolTip(load_dorks_btn, "Load dork queries from a text file.")

         # Load & Replace Dorks Button
        load_and_replace_dorks_btn = tk.Button(dorks_frame, text="Auto Replace Sosials From Dork", command=self.load_and_replace_dorks, bg="#4CAF50", fg="white", width=25, font=("Helvetica", 9, "bold"))
        load_and_replace_dorks_btn.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ToolTip(load_and_replace_dorks_btn, "Load dork queries from a file and replace 'Name Or Username' with a specified name.")

        # Load & Replace Sites Button
        load_and_replace_sites_btn = tk.Button(dorks_frame, text="Auto Replace Sites From Dork", command=self.load_and_replace_sites, bg="#4CAF50", fg="white", width=25, font=("Helvetica", 9, "bold"))
        load_and_replace_sites_btn.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ToolTip(load_and_replace_sites_btn, "Load file and replace 'site.com' with a specified site name.")
    
    def create_proxies(self):
        # Proxies Tab Content
        # Proxies Frame
        proxies_frame = tk.LabelFrame(self.proxies_tab, text="Proxies", padx=10, pady=10, bg="#2E2E2E", fg="white")
        proxies_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.proxies_text = scrolledtext.ScrolledText(proxies_frame, width=100, height=10, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.proxies_text.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Configure grid weights
        proxies_frame.grid_rowconfigure(0, weight=1)
        proxies_frame.grid_columnconfigure(0, weight=1)

        # Persistent Tip below the text box
        proxy_tip = tk.Label(proxies_frame, text="Enter proxies here, one per line (e.g., http://IP:PORT).", bg="#2E2E2E", fg="light gray", font=("Helvetica", 9))
        proxy_tip.grid(row=1, column=0, sticky=tk.W, padx=5)

        # Load Proxies Button
        load_proxies_btn = tk.Button(proxies_frame, text="Load Proxies from File", command=self.load_proxies, bg="#2196F3", fg="white", width=20, font=("Helvetica", 9, "bold"))
        load_proxies_btn.grid(row=2, column=0, sticky=tk.E, padx=5, pady=5)
        ToolTip(load_proxies_btn, "Load proxies from a text file.")

    def create_settings(self):
        # Settings Tab Content
        # Settings Options Frame
        settings_options_frame = tk.Frame(self.settings_tab, bg="#2E2E2E")
        settings_options_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # User-Agent Customization
        ua_frame = tk.LabelFrame(settings_options_frame, text="User-Agent Customization", padx=10, pady=10, bg="#2E2E2E", fg="white")
        ua_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.ua_listbox = tk.Listbox(ua_frame, bg="#3C3F41", fg="white", selectbackground="#4CAF50", selectforeground="white", font=("Courier New", 10))
        self.ua_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)

        # Populate Listbox
        for ua in USER_AGENTS:
            self.ua_listbox.insert(tk.END, ua)

        # Buttons for User-Agent
        ua_button_frame = tk.Frame(ua_frame, bg="#2E2E2E")
        ua_button_frame.pack(side=tk.LEFT, fill="y", padx=5, pady=5)

        add_ua_btn = tk.Button(ua_button_frame, text="Add", command=self.add_user_agent, bg="#4CAF50", fg="white", width=10, font=("Helvetica", 9, "bold"))
        add_ua_btn.pack(pady=2)
        ToolTip(add_ua_btn, "Add a new User-Agent string.")

        remove_ua_btn = tk.Button(ua_button_frame, text="Remove", command=self.remove_user_agent, bg="#F44336", fg="white", width=10, font=("Helvetica", 9, "bold"))
        remove_ua_btn.pack(pady=2)
        ToolTip(remove_ua_btn, "Remove the selected User-Agent string.")

        edit_ua_btn = tk.Button(ua_button_frame, text="Edit", command=self.edit_user_agent, bg="#2196F3", fg="white", width=10, font=("Helvetica", 9, "bold"))
        edit_ua_btn.pack(pady=2)
        ToolTip(edit_ua_btn, "Edit the selected User-Agent string.")

        # Configure Settings Button on the right
        config_btn = tk.Button(settings_options_frame, text="Configure Settings", command=self.open_config, bg="#FF9800", fg="white", width=20, font=("Helvetica", 10, "bold"))
        config_btn.grid(row=0, column=1, sticky='e', padx=5, pady=5)
        ToolTip(config_btn, "Open configuration settings to modify default options.")

        # Number of Results
        tk.Label(settings_options_frame, text="Number of Results per Dork:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(settings_options_frame, textvariable=self.num_results, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10)).grid(row=1, column=1, padx=10, pady=5)
        ToolTip(settings_options_frame.grid_slaves(row=1, column=1)[0], "Specify how many search results to retrieve for each dork.")

        # Number of Threads
        tk.Label(settings_options_frame, text="Number of Threads:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(settings_options_frame, textvariable=self.threads, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10)).grid(row=2, column=1, padx=10, pady=5)
        ToolTip(settings_options_frame.grid_slaves(row=2, column=1)[0], "Set the number of concurrent threads for URL validation.")

        # Validate URLs
        tk.Checkbutton(settings_options_frame, text="Validate URLs", variable=self.validate_urls_flag, bg="#2E2E2E", fg="white", selectcolor="#2E2E2E", font=("Helvetica", 10)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        ToolTip(settings_options_frame.grid_slaves(row=3, column=0)[0], "Enable to check if the retrieved URLs are reachable.")

        # Output Options
        tk.Label(settings_options_frame, text="Output Mode:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Radiobutton(settings_options_frame, text="Single File", variable=self.output_mode, value='single', bg="#2E2E2E", fg="white", selectcolor="#2E2E2E", font=("Helvetica", 10)).grid(row=4, column=1, sticky=tk.W, padx=10, pady=2)
        ToolTip(settings_options_frame.grid_slaves(row=4, column=1)[0], "Save all results into a single file.")
        tk.Radiobutton(settings_options_frame, text="Multiple Files", variable=self.output_mode, value='multiple', bg="#2E2E2E", fg="white", selectcolor="#2E2E2E", font=("Helvetica", 10)).grid(row=5, column=1, sticky=tk.W, padx=10, pady=2)
        ToolTip(settings_options_frame.grid_slaves(row=5, column=1)[0], "Save results for each dork into separate files.")
        tk.Radiobutton(settings_options_frame, text="None", variable=self.output_mode, value='none', bg="#2E2E2E", fg="white", selectcolor="#2E2E2E", font=("Helvetica", 10)).grid(row=6, column=1, sticky=tk.W, padx=10, pady=2)
        ToolTip(settings_options_frame.grid_slaves(row=6, column=1)[0], "Do not save the results to any file; display only within the GUI.")

        # Output Filename
        tk.Label(settings_options_frame, text="Output Filename:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
        tk.Entry(settings_options_frame, textvariable=self.output_file, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10)).grid(row=7, column=1, padx=10, pady=5)
        ToolTip(settings_options_frame.grid_slaves(row=7, column=1)[0], "Specify the filename for single file output.")

        # Configure grid weights for responsiveness
        settings_options_frame.grid_rowconfigure(0, weight=1)
        settings_options_frame.grid_columnconfigure(0, weight=1)
        settings_options_frame.grid_columnconfigure(1, weight=1)

    def create_find_dorks(self):
        # Find Dorks Tab Content
        # Find Dorks Frame
        find_dorks_frame = tk.LabelFrame(self.find_dorks_tab, text="Find Dork Queries", padx=10, pady=10, bg="#2E2E2E", fg="white")
        find_dorks_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Search Bar, Number of Dorks, and Dorks File Selection
        search_frame = tk.Frame(find_dorks_frame, bg="#2E2E2E")
        search_frame.pack(fill="x", pady=5)

        tk.Label(search_frame, text="Keyword:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.live_dork_search_var = tk.StringVar()
        self.live_dork_search_entry = tk.Entry(search_frame, textvariable=self.live_dork_search_var, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.live_dork_search_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        ToolTip(self.live_dork_search_entry, "Enter a keyword to filter dork queries (e.g., 'php').")

        tk.Label(search_frame, text="Number of Dorks:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.live_dork_number_var = tk.IntVar(value=10)
        self.live_dork_number_entry = tk.Entry(search_frame, textvariable=self.live_dork_number_var, bg="#3C3F41", fg="white", insertbackground="white", width=5, font=("Courier New", 10))
        self.live_dork_number_entry.pack(side=tk.LEFT, padx=5)
        ToolTip(self.live_dork_number_entry, "Specify how many dorks to fetch based on the keyword.")

        # Choose Dorks File Button
        choose_file_btn = tk.Button(search_frame, text="Choose Dorks File", command=self.choose_dorks_file, bg="#9C27B0", fg="white", width=15, font=("Helvetica", 10, "bold"))
        choose_file_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(choose_file_btn, "Select the dorks file to fetch from.")

        # Fetch Dorks Button
        fetch_dorks_btn = tk.Button(search_frame, text="Fetch Dorks", command=self.fetch_dorks_from_file, bg="#2196F3", fg="white", width=15, font=("Helvetica", 10, "bold"))
        fetch_dorks_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(fetch_dorks_btn, "Fetch dork queries from the selected file based on the entered keyword.")

        # Current Dorks File Display
        self.current_dorks_file_label = tk.Label(find_dorks_frame, text="No file selected.", bg="#2E2E2E", fg="#FFEB3B", font=("Helvetica", 9))
        self.current_dorks_file_label.pack(anchor='w', padx=10, pady=2)

        # Find Dorks Display
        self.find_dorks_text = scrolledtext.ScrolledText(find_dorks_frame, width=80, height=20, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.find_dorks_text.pack(fill="both", expand=True, padx=5, pady=5)
        ToolTip(self.find_dorks_text, "Displays fetched dork queries based on the selected file and keyword.")

    def create_site_info(self):
        # Site Info Tab Content
        # Site Info Frame
        site_info_frame = tk.LabelFrame(self.site_info_tab, text="Website Information", padx=10, pady=10, bg="#2E2E2E", fg="white")
        site_info_frame.pack(fill="both", expand=False, padx=10, pady=5)

        # URL Entry
        tk.Label(site_info_frame, text="Website URL:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.site_url_entry = tk.Entry(site_info_frame, width=60, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.site_url_entry.grid(row=0, column=1, padx=5, pady=5)
        ToolTip(self.site_url_entry, "Enter the website URL to gather information.")

        # Buttons for Commands
        commands_frame = tk.Frame(site_info_frame, bg="#2E2E2E")
        commands_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # Define commands and their corresponding functions
        self.site_commands = {
            "WHOIS": self.perform_whois,
            "DIG": self.perform_dig,
            "Ping": self.perform_ping,
            "Traceroute": self.perform_traceroute,
            "Reverse IP Lookup": self.perform_reverse_ip,
            "NSLookup": self.perform_nslookup,
            "Curl -I": self.perform_curl,
            "Netstat": self.perform_netstat,
            "ARP -a": self.perform_arp,
            "Echo | Telnet": self.perform_echo_telnet,
            "Host": self.perform_host,
            "Echo | OpenSSL": self.perform_echo_openssl,
            "Dig MX": self.perform_dig_mx,
            "Dig TXT": self.perform_dig_txt,
            "Dig CNAME": self.perform_dig_cname,
            "NSLookup -Any": self.perform_nslookup_any,
            "Wget | Grep": self.perform_wget_grep
        }

        # Create buttons dynamically to avoid repetition
        for idx, (cmd, func) in enumerate(self.site_commands.items()):
            btn = tk.Button(commands_frame, text=cmd, command=func, bg="#607D8B", fg="white", width=18, height=2, font=("Helvetica", 9, "bold"))
            btn.grid(row=idx//4, column=idx%4, padx=5, pady=5)
            ToolTip(btn, f"Perform {cmd} on the entered URL.")

        # Clear Site Info Button
        clear_site_info_btn = tk.Button(commands_frame, text="Clear", command=self.clear_site_info, bg="#9E9E9E", fg="white", width=18, height=2, font=("Helvetica", 9, "bold"))
        clear_site_info_btn.grid(row=(len(self.site_commands)//4)+1, column=0, padx=5, pady=5, columnspan=4, sticky='we')
        ToolTip(clear_site_info_btn, "Clear the Site Info console.")

        # Results Display
        self.site_info_text = scrolledtext.ScrolledText(site_info_frame, width=80, height=20, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.site_info_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')
        ToolTip(self.site_info_text, "Displays the results of the performed commands.")

        # Configure grid weights
        site_info_frame.grid_rowconfigure(2, weight=1)
        site_info_frame.grid_columnconfigure(1, weight=1)

    def create_search_results(self):
        # Search Results Tab Content
        # Progress Bar Frame
        progress_frame = tk.Frame(self.results_tab, bg="#2E2E2E")
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        ToolTip(self.progress_bar, "Shows the progress of the search operation.")

        # Search Results Text Area
        results_frame = tk.Frame(self.results_tab, bg="#2E2E2E")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Clear Search Results Button
        clear_search_btn = tk.Button(results_frame, text="Clear", command=self.clear_search_results, bg="#9E9E9E", fg="white", width=12, font=("Helvetica", 10, "bold"))
        clear_search_btn.pack(anchor='ne', pady=5)
        ToolTip(clear_search_btn, "Clear the Search Results console.")

        self.results_text = scrolledtext.ScrolledText(results_frame, width=100, height=15, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.results_text.pack(fill="both", expand=True)
        ToolTip(self.results_text, "Displays the search results in real-time.")

    def create_about(self):
        # About Tab Content
        # About Frame
        about_frame = tk.Frame(self.about_tab, bg="#2E2E2E")
        about_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Tool Description
        description = (
            "PH4N70M is a comprehensive penetration testing tool designed to perform Google dorking efficiently.\n"
            "Utilize dork queries to uncover sensitive information across the web.\n"
            "Customize your searches with proxy support, real-time URL validation, and in-depth site information gathering.\n"
            "\n"
            "Features:\n"
            "- Google Dorking for information retrieval\n"
            "- Proxy management for enhanced anonymity\n"
            "- URL validation to ensure result accuracy\n"
            "- Keyword-based filtering of dork queries from a local file\n"
            "- Comprehensive site information including WHOIS, DIG, Ping, Traceroute, Reverse IP Lookup, NSLookup, Curl, Netstat, ARP, Telnet, OpenSSL, Dig (MX, TXT, CNAME), and Wget | Grep\n"
            "\n"
            "Developed by [Your Name]. For more information and updates, visit my GitHub repository."
        )
        tk.Label(about_frame, text=description, bg="#2E2E2E", fg="white", justify=tk.LEFT, wraplength=850, font=("Helvetica", 10)).pack(pady=10)

        # GitHub Link
        github_label = tk.Label(about_frame, text="Visit my GitHub: https://github.com/zebbern", fg="#2196F3", bg="#2E2E2E", cursor="hand2", font=("Helvetica", 10, "underline"))
        github_label.pack(pady=10)
        github_label.bind("<Button-1>", lambda e: self.open_github())

    def choose_dorks_file(self):
        file_path = filedialog.askopenfilename(title="Select Dorks File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if file_path:
            self.selected_dorks_file.set(file_path)
            self.current_dorks_file_label.config(text=f"Selected File: {os.path.basename(file_path)}")
            logging.info(f"Selected dorks file: {file_path}")
        else:
            self.selected_dorks_file.set('')
            self.current_dorks_file_label.config(text="No file selected.")
            logging.info("No dorks file selected.")

    def load_and_replace_sites(self):
        # Prompt the user to enter a new site name to replace 'site.com'
        replacement_site = simpledialog.askstring("Enter Site", "Please enter the site to replace 'site.com':", parent=self.root)
        if not replacement_site:
            messagebox.showerror("Error", "Site cannot be empty.")
            return

        # Open a file dialog to select the file containing 'site.com'
        file_path = filedialog.askopenfilename(title="Select Site File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if file_path:
            try:
                # Read and replace 'site.com' in each line
                with open(file_path, 'r') as f:
                    sites = [line.replace("site.com", replacement_site).strip() for line in f if line.strip()]

                # Display the updated sites in the GUI's dork text area (or any other text area you prefer)
                self.dorks_text.delete('1.0', tk.END)
                self.dorks_text.insert(tk.END, "\n".join(sites))

                # Display a success message
                messagebox.showinfo("Success", f"Loaded and replaced 'site.com' in {len(sites)} entries from '{file_path}'.")
                logging.info(f"Loaded and replaced 'site.com' in {len(sites)} entries from '{file_path}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load and replace sites: {e}")
                logging.error(f"Failed to load and replace sites from '{file_path}': {e}")
    
    def load_and_replace_dorks(self):
        # Prompt user for replacement name
        replacement_name = simpledialog.askstring("Enter Name", "Please enter the name to replace 'Name Or Username':", parent=self.root)
        if not replacement_name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return

        # Open a file dialog to select the dork file
        file_path = filedialog.askopenfilename(title="Select Dorks File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if file_path:
            try:
                # Read and replace the placeholder in each line
                with open(file_path, 'r') as f:
                    dorks = [line.replace("Name Or Username", replacement_name).strip() for line in f if line.strip()]

                # Display the updated dorks in the GUI's dork text area
                self.dorks_text.delete('1.0', tk.END)
                self.dorks_text.insert(tk.END, "\n".join(dorks))

                # Display a success message
                messagebox.showinfo("Success", f"Loaded and replaced placeholders in {len(dorks)} dorks from '{file_path}'.")
                logging.info(f"Loaded and replaced placeholders in {len(dorks)} dorks from '{file_path}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load and replace dorks: {e}")
                logging.error(f"Failed to load and replace dorks from '{file_path}': {e}")


    def fetch_dorks_from_file(self):
        keyword = self.live_dork_search_var.get().strip()
        if not keyword:
            messagebox.showerror("Error", "Please enter a keyword to fetch relevant dorks.")
            return
        limit = self.live_dork_number_var.get()
        if limit <= 0:
            messagebox.showerror("Error", "Number of dorks to fetch must be a positive integer.")
            return
        dorks_file = self.selected_dorks_file.get()
        if not dorks_file:
            messagebox.showerror("Error", "Please select a dorks file to fetch from.")
            return

        def fetch():
            self.find_dorks_text.config(state='normal')
            self.find_dorks_text.delete('1.0', tk.END)
            self.find_dorks_text.insert(tk.END, f"Fetching dork queries with keyword '{keyword}' from '{os.path.basename(dorks_file)}'...\n")
            self.find_dorks_text.config(state='disabled')
            try:
                with open(dorks_file, 'r') as f:
                    all_dorks = [line.strip() for line in f if line.strip()]
                # Filter dorks based on keyword
                filtered_dorks = [dork for dork in all_dorks if keyword.lower() in dork.lower()]
                if not filtered_dorks:
                    self.log(f"No dork queries found with keyword '{keyword}' in '{os.path.basename(dorks_file)}'.")
                    return
                # Limit the number of dorks
                limited_dorks = filtered_dorks[:limit]
                self.find_dorks_text.config(state='normal')
                self.find_dorks_text.delete('1.0', tk.END)
                for dork in limited_dorks:
                    self.find_dorks_text.insert(tk.END, dork + "\n")
                self.find_dorks_text.config(state='disabled')
                self.log(f"Fetched {len(limited_dorks)} dork queries with keyword '{keyword}' from '{os.path.basename(dorks_file)}'.")
            except Exception as e:
                self.log(f"Error fetching dorks: {e}")

        threading.Thread(target=fetch).start()

    def load_dorks(self):
        file_path = filedialog.askopenfilename(title="Select Dorks File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    dorks = [line.strip() for line in f if line.strip()]
                self.dorks_text.delete('1.0', tk.END)
                self.dorks_text.insert(tk.END, "\n".join(dorks))
                messagebox.showinfo("Success", f"Loaded {len(dorks)} dorks from '{file_path}'.")
                logging.info(f"Loaded {len(dorks)} dorks from '{file_path}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load dorks: {e}")
                logging.error(f"Failed to load dorks from '{file_path}': {e}")

    def load_proxies(self):
        file_path = filedialog.askopenfilename(title="Select Proxies File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    proxies = [line.strip() for line in f if line.strip()]
                self.proxies_text.delete('1.0', tk.END)
                self.proxies_text.insert(tk.END, "\n".join(proxies))
                messagebox.showinfo("Success", f"Loaded {len(proxies)} proxies from '{file_path}'.")
                logging.info(f"Loaded {len(proxies)} proxies from '{file_path}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load proxies: {e}")
                logging.error(f"Failed to load proxies from '{file_path}': {e}")

    def log(self, message):
        self.results_text.config(state='normal')
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state='disabled')
        logging.info(message)

    def validate_proxy(self, proxy):
        try:
            response = requests.get('http://www.google.com', proxies={"http": proxy, "https": proxy},
                                    headers={'User-Agent': random.choice(USER_AGENTS)},
                                    timeout=PROXY_VALIDATION_TIMEOUT)
            if response.status_code == 200:
                self.log(f"Proxy is working: {proxy}")
                return proxy
        except requests.RequestException:
            self.log(f"Proxy failed: {proxy}")
        return None

    def get_valid_proxies(self, proxies):
        self.log("Validating proxies...")
        valid_proxies = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {executor.submit(self.validate_proxy, proxy): proxy for proxy in proxies}
            for future in as_completed(future_to_proxy):
                if self.stop_event.is_set():
                    break
                proxy = future_to_proxy[future]
                result = future.result()
                if result:
                    valid_proxies.append(result)
        self.log(f"Valid proxies found: {len(valid_proxies)}")
        return valid_proxies

    def validate_url(self, url):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
            if response.status_code == 200:
                self.log(f"URL is alive: {url}")
                return url, True
            else:
                self.log(f"URL is not reachable: {url}")
                return url, False
        except requests.RequestException:
            self.log(f"URL validation failed: {url}")
            return url, False

    def validate_urls(self, urls, threads):
        alive_urls = []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_url = {executor.submit(self.validate_url, url): url for url in urls}
            for future in as_completed(future_to_url):
                if self.stop_event.is_set():
                    break
                url, is_alive = future.result()
                if is_alive:
                    alive_urls.append(url)
        return alive_urls

    def start_search(self):
        # Disable start button and enable stop button
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.stop_event.clear()
        self.progress.set(0)
        self.log("Starting search...")
        thread = threading.Thread(target=self.perform_search)
        thread.start()

    def stop_search(self):
        self.stop_event.set()
        self.log("Stopping search...")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def perform_search(self):
        # Get dorks
        dorks_input = self.dorks_text.get('1.0', tk.END).strip()
        if not dorks_input:
            messagebox.showerror("Error", "Please enter at least one dork query.")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            return
        # Split by newlines and commas
        self.dorks = [dork.strip() for dork in dorks_input.replace(',', '\n').split('\n') if dork.strip()]
        total_dorks = len(self.dorks)
        self.log(f"Loaded {total_dorks} dorks.")

        # Get number of results
        amount = self.num_results.get()
        if amount <= 0:
            messagebox.showerror("Error", "Number of results must be a positive integer.")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            return

        # Get proxies
        proxies_input = self.proxies_text.get('1.0', tk.END).strip()
        if proxies_input:
            proxies = [proxy.strip() for proxy in proxies_input.split('\n') if proxy.strip()]
            self.log(f"Loaded {len(proxies)} proxies.")
            self.valid_proxies = self.get_valid_proxies(proxies)
        else:
            self.valid_proxies = []
            self.log("No proxies loaded.")

        # Validate URLs flag
        validate_flag = self.validate_urls_flag.get()

        # Output mode
        output_mode = self.output_mode.get()
        output_file = self.output_file.get()

        # Threads
        threads = self.threads.get()
        if threads <= 0:
            messagebox.showerror("Error", "Number of threads must be a positive integer.")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            return

        dorks_results = {}
        processed_dorks = 0

        for dork in self.dorks:
            if self.stop_event.is_set():
                self.log("Search stopped by user.")
                break
            self.log(f"Searching for dork ({processed_dorks + 1}/{total_dorks}): {dork}")
            try:
                # If using proxies, rotate them
                if self.valid_proxies:
                    proxy = random.choice(self.valid_proxies)
                    self.log(f"Using proxy: {proxy}")
                    # Note: 'proxies' parameter in googlesearch.search does not exist; adjust accordingly
                    results = list(search(dork, num=amount, stop=amount, pause=2))
                else:
                    results = list(search(dork, num=amount, stop=amount, pause=2))
                self.log(f"Found {len(results)} results for dork: {dork}")
                if validate_flag:
                    self.log("Validating URLs...")
                    results = self.validate_urls(results, threads)
                    self.log(f"Validated {len(results)} alive URLs.")
                dorks_results[dork] = results
                for idx, url in enumerate(results, 1):
                    self.log(f"{idx}. {url}")
                processed_dorks += 1
                # Update progress
                progress_percentage = (processed_dorks / total_dorks) * 100
                self.update_progress(progress_percentage)
            except Exception as e:
                self.log(f"Error searching for dork '{dork}': {e}")

        # Handle output
        if not self.stop_event.is_set():
            if output_mode == 'single':
                self.save_results_single(dorks_results, output_file, output_format='txt')
            elif output_mode == 'multiple':
                self.save_results_multiple(dorks_results)
            elif output_mode == 'none':
                self.log("Output skipped.")
        else:
            self.log("Search was stopped before completion.")

        self.log("Search process completed.")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def update_progress(self, percentage):
        self.progress.set(percentage)
        self.results_tab.update_idletasks()

    def save_results_single(self, dorks_results, filename, output_format='txt'):
        try:
            if output_format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(dorks_results, f, indent=4)
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    for dork, urls in dorks_results.items():
                        f.write(f"Dork: {dork}\n")
                        for idx, url in enumerate(urls, 1):
                            f.write(f"  {idx}. {url}\n")
                        f.write("\n")
            self.log(f"Results saved to '{filename}'.")
            messagebox.showinfo("Success", f"Results saved to '{filename}'.")
            logging.info(f"Results saved to '{filename}'.")
        except Exception as e:
            self.log(f"Failed to save results to '{filename}': {e}")
            messagebox.showerror("Error", f"Failed to save results to '{filename}'.")

    def save_results_multiple(self, dorks_results):
        try:
            for dork, urls in dorks_results.items():
                sanitized_dork = "_".join(dork.split())
                filename = f"{sanitized_dork}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    for idx, url in enumerate(urls, 1):
                        f.write(f"{idx}. {url}\n")
            self.log("Results saved to individual dork files.")
            messagebox.showinfo("Success", "Results saved to individual dork files.")
            logging.info("Results saved to individual dork files.")
        except Exception as e:
            self.log(f"Failed to save results to individual files: {e}")
            messagebox.showerror("Error", "Failed to save results to individual files.")

    def open_config(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration Settings")
        config_window.geometry("600x600")
        config_window.configure(bg="#2E2E2E")

        # User Agents
        tk.Label(config_window, text="User Agents:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).pack(anchor=tk.W, padx=10, pady=5)
        self.ua_text_config = scrolledtext.ScrolledText(config_window, width=70, height=15, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10))
        self.ua_text_config.pack(padx=10, pady=5)
        self.ua_text_config.insert(tk.END, "\n".join(USER_AGENTS))
        ToolTip(self.ua_text_config, "Edit the list of User-Agent strings used for requests.")

        # Default Threads
        tk.Label(config_window, text="Default Threads:", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).pack(anchor=tk.W, padx=10, pady=5)
        self.default_threads_var_config = tk.IntVar(value=DEFAULT_THREADS)
        tk.Entry(config_window, textvariable=self.default_threads_var_config, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10)).pack(padx=10, pady=5)
        ToolTip(config_window, "Set the default number of threads for URL validation.")

        # Proxy Validation Timeout
        tk.Label(config_window, text="Proxy Validation Timeout (seconds):", bg="#2E2E2E", fg="white", font=("Helvetica", 10)).pack(anchor=tk.W, padx=10, pady=5)
        self.proxy_timeout_var_config = tk.IntVar(value=PROXY_VALIDATION_TIMEOUT)
        tk.Entry(config_window, textvariable=self.proxy_timeout_var_config, bg="#3C3F41", fg="white", insertbackground="white", font=("Courier New", 10)).pack(padx=10, pady=5)
        ToolTip(config_window, "Set the timeout duration for proxy validation.")

        # Save Button
        save_btn = tk.Button(config_window, text="Save Settings", command=lambda: self.save_config(config_window), bg="#FF9800", fg="white", width=20, font=("Helvetica", 10, "bold"))
        save_btn.pack(pady=20)
        ToolTip(save_btn, "Save the updated configuration settings.")

    def save_config(self, window):
        # Update User Agents
        uas = self.ua_text_config.get('1.0', tk.END).strip().split('\n')
        uas = [ua.strip() for ua in uas if ua.strip()]
        if uas:
            config['user_agents'] = uas
            global USER_AGENTS
            USER_AGENTS = uas
            self.ua_listbox.delete(0, tk.END)
            for ua in uas:
                self.ua_listbox.insert(tk.END, ua)
            logging.info("User Agents updated via GUI.")
        else:
            messagebox.showerror("Error", "User-Agent list cannot be empty.")
            return

        # Update Default Threads
        threads = self.default_threads_var_config.get()
        if threads > 0:
            config['default_threads'] = threads
            global DEFAULT_THREADS
            DEFAULT_THREADS = threads
            logging.info("Default Threads updated via GUI.")
        else:
            messagebox.showerror("Error", "Default Threads must be a positive integer.")
            return

        # Update Proxy Validation Timeout
        timeout = self.proxy_timeout_var_config.get()
        if timeout > 0:
            config['proxy_validation_timeout'] = timeout
            global PROXY_VALIDATION_TIMEOUT
            PROXY_VALIDATION_TIMEOUT = timeout
            logging.info("Proxy Validation Timeout updated via GUI.")
        else:
            messagebox.showerror("Error", "Proxy Validation Timeout must be a positive integer.")
            return

        # Save to config file
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Success", "Configuration settings saved successfully.")
            window.destroy()
        except Exception as e:
            self.log(f"Failed to save configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def add_user_agent(self):
        new_ua = simpledialog.askstring("Add User-Agent", "Enter new User-Agent string:", parent=self.root)
        if new_ua:
            self.ua_listbox.insert(tk.END, new_ua)
            self.ua_text_config.insert(tk.END, new_ua + "\n")
            logging.info(f"Added new User-Agent: {new_ua}")
        else:
            messagebox.showerror("Error", "User-Agent cannot be empty.")

    def remove_user_agent(self):
        selected_indices = self.ua_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a User-Agent to remove.")
            return
        for index in reversed(selected_indices):
            ua = self.ua_listbox.get(index)
            self.ua_listbox.delete(index)
            # Also remove from config
            try:
                ua_list = self.ua_text_config.get('1.0', tk.END).strip().split('\n')
                ua_list.remove(ua)
                self.ua_text_config.delete('1.0', tk.END)
                self.ua_text_config.insert(tk.END, "\n".join(ua_list))
            except ValueError:
                pass
            logging.info(f"Removed User-Agent: {ua}")

    def edit_user_agent(self):
        selected_indices = self.ua_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a User-Agent to edit.")
            return
        if len(selected_indices) > 1:
            messagebox.showerror("Error", "Please select only one User-Agent to edit.")
            return
        index = selected_indices[0]
        current_ua = self.ua_listbox.get(index)

        new_ua = simpledialog.askstring("Edit User-Agent", "Edit selected User-Agent string:", initialvalue=current_ua, parent=self.root)
        if new_ua:
            self.ua_listbox.delete(index)
            self.ua_listbox.insert(index, new_ua)
            # Update in config
            try:
                ua_list = self.ua_text_config.get('1.0', tk.END).strip().split('\n')
                ua_list[index] = new_ua
                self.ua_text_config.delete('1.0', tk.END)
                self.ua_text_config.insert(tk.END, "\n".join(ua_list))
            except IndexError:
                pass
            logging.info(f"Edited User-Agent to: {new_ua}")
        else:
            messagebox.showerror("Error", "User-Agent cannot be empty.")

    def clear_site_info(self):
        self.site_info_text.delete('1.0', tk.END)
        self.log("Site Info console cleared.")

    def clear_search_results(self):
        self.results_text.delete('1.0', tk.END)
        self.log("Search Results console cleared.")

    def perform_wget_grep(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return

        keyword = self.live_dork_search_var.get().strip()
        if not keyword:
            keyword = simpledialog.askstring("Keyword Input", "Enter the keyword to search for:", parent=self.root)
            if not keyword:
                messagebox.showerror("Error", "Keyword cannot be empty.")
                return

        def wget_grep():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"wget -q -O - http://{domain} | grep -i \"{keyword}\""
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                # Fetch webpage content using requests
                response = requests.get(f"http://{domain}", headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=10)
                matches = [line for line in response.text.split('\n') if keyword.lower() in line.lower()]
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Wget | Grep Results for {domain} with keyword '{keyword}':\n")
                for match in matches:
                    # Highlight keyword in red
                    start_idx = self.site_info_text.index(tk.INSERT)
                    self.site_info_text.insert(tk.END, f"{match}\n")
                    # Apply tag to the keyword occurrences
                    self.highlight_keyword_in_line(match, keyword)
                if not matches:
                    self.site_info_text.insert(tk.END, f"No matches found for keyword '{keyword}'.\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed Wget | Grep for {domain} with keyword '{keyword}'")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Wget | Grep failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Wget | Grep failed for {url}: {e}")
        threading.Thread(target=wget_grep).start()

    def highlight_keyword_in_line(self, line, keyword):
        index = self.site_info_text.index(tk.INSERT + " linestart")
        lower_line = line.lower()
        lower_keyword = keyword.lower()
        start = 0
        while True:
            pos = lower_line.find(lower_keyword, start)
            if pos == -1:
                break
            start_idx = f"{index.split('.')[0]}.{int(index.split('.')[1]) + pos}"
            end_idx = f"{index.split('.')[0]}.{int(index.split('.')[1]) + pos + len(keyword)}"
            self.site_info_text.tag_add("keyword", start_idx, end_idx)
            start = pos + len(keyword)
        self.site_info_text.tag_configure("keyword", foreground="red")

    # Placeholder methods for commands not implemented
    # ...

    def open_github(self):
        webbrowser.open_new("https://github.com/zebbern")

    def perform_whois(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def whois_lookup():
            command = f"whois {url}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                w = whois.whois(url)
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"WHOIS Information for {url}:\n{w.text}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed WHOIS lookup for {url}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"WHOIS lookup failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"WHOIS lookup failed for {url}: {e}")
        threading.Thread(target=whois_lookup).start()

    def perform_dig(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def dig_lookup():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"dig {domain}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                resolver = dns.resolver.Resolver()
                answers = resolver.resolve(domain, 'A')
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"DIG A Record for {domain}:\n")
                for rdata in answers:
                    self.site_info_text.insert(tk.END, f" - {rdata.address}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed DIG lookup for {domain}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"DIG lookup failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"DIG lookup failed for {url}: {e}")
        threading.Thread(target=dig_lookup).start()

    def perform_ping(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def ping_site():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"ping -c 4 {domain}" if os.name != 'nt' else f"ping -n 4 {domain}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Ping Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Pinged {domain} successfully.")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Ping failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Ping failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Ping failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Ping failed for {url}: {e}")
        threading.Thread(target=ping_site).start()

    def perform_traceroute(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def traceroute_site():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"traceroute {domain}" if os.name != 'nt' else f"tracert {domain}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Traceroute Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Traceroute for {domain} completed successfully.")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Traceroute failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Traceroute failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Traceroute failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Traceroute failed for {url}: {e}")
        threading.Thread(target=traceroute_site).start()

    def perform_reverse_ip(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def reverse_ip_lookup():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            try:
                ip = socket.gethostbyname(domain)
                command = f"dig +short -x {ip}" if os.name != 'nt' else f"nslookup {domain}"
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
                self.site_info_text.config(state='disabled')
                if os.name != 'nt':
                    resolver = dns.resolver.Resolver()
                    try:
                        answers = resolver.resolve_address(ip)
                        reverse_dns = [str(rdata.target).rstrip('.') for rdata in answers]
                    except dns.resolver.NXDOMAIN:
                        reverse_dns = []
                else:
                    # On Windows, using nslookup for reverse DNS
                    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                    reverse_dns = []
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            if "name =" in line:
                                reverse_dns.append(line.split("name =")[1].strip())
                self.site_info_text.config(state='normal')
                if reverse_dns:
                    self.site_info_text.insert(tk.END, f"Reverse DNS for {ip}:\n")
                    for rdns in reverse_dns:
                        self.site_info_text.insert(tk.END, f" - {rdns}\n")
                else:
                    self.site_info_text.insert(tk.END, f"No Reverse DNS records found for {ip}.\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed Reverse IP Lookup for {domain}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Reverse IP Lookup failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Reverse IP Lookup failed for {url}: {e}")
        threading.Thread(target=reverse_ip_lookup).start()

    def perform_nslookup(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def nslookup():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"nslookup {domain}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"NSLookup Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Performed NSLookup for {domain}")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"NSLookup failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"NSLookup failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"NSLookup failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"NSLookup failed for {url}: {e}")
        threading.Thread(target=nslookup).start()

    def perform_curl(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def curl_i():
            command = f"curl -I {url}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Curl -I Results for {url}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Performed Curl -I for {url}")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Curl -I failed for {url}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Curl -I failed for {url}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Curl -I failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Curl -I failed for {url}: {e}")
        threading.Thread(target=curl_i).start()

    def perform_netstat(self):
        def netstat_cmd():
            command = "netstat -a"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                if os.name == 'nt':
                    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                else:
                    result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Netstat Results:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info("Performed Netstat command.")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Netstat failed:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Netstat failed: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Netstat failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Netstat failed: {e}")
        threading.Thread(target=netstat_cmd).start()

    def perform_arp(self):
        def arp_cmd():
            command = "arp -a"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                if os.name == 'nt':
                    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                else:
                    result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"ARP -a Results:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info("Performed ARP -a command.")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"ARP -a failed:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"ARP -a failed: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"ARP -a failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"ARP -a failed: {e}")
        threading.Thread(target=arp_cmd).start()

    def perform_echo_telnet(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def echo_telnet():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"echo | telnet {domain} 80"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Echo | Telnet Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Performed Echo | Telnet for {domain}")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Echo | Telnet failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Echo | Telnet failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Echo | Telnet failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Echo | Telnet failed for {url}: {e}")
        threading.Thread(target=echo_telnet).start()

    def perform_host(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def host_cmd():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"host {domain}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Host Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Performed Host command for {domain}")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Host command failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Host command failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Host command failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Host command failed for {url}: {e}")
        threading.Thread(target=host_cmd).start()

    def perform_echo_openssl(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def echo_openssl():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            try:
                ip = socket.gethostbyname(domain)
                command = f"echo | openssl s_client -connect {domain}:443 2>/dev/null | openssl x509 -noout -text"
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
                self.site_info_text.config(state='disabled')
                if os.name == 'nt':
                    # Windows doesn't support redirection '2>/dev/null'
                    command = f"echo | openssl s_client -connect {domain}:443 | openssl x509 -noout -text"
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Echo | OpenSSL Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Performed Echo | OpenSSL for {domain}")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"Echo | OpenSSL failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"Echo | OpenSSL failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Echo | OpenSSL failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Echo | OpenSSL failed for {url}: {e}")
        threading.Thread(target=echo_openssl).start()

    def perform_dig_mx(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def dig_mx():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"dig {domain} MX +short"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                resolver = dns.resolver.Resolver()
                answers = resolver.resolve(domain, 'MX')
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Dig MX Records for {domain}:\n")
                for rdata in answers:
                    self.site_info_text.insert(tk.END, f" - {rdata.exchange} Priority: {rdata.preference}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed Dig MX for {domain}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Dig MX failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Dig MX failed for {url}: {e}")
        threading.Thread(target=dig_mx).start()

    def perform_dig_txt(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def dig_txt():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"dig {domain} TXT +short"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                resolver = dns.resolver.Resolver()
                answers = resolver.resolve(domain, 'TXT')
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Dig TXT Records for {domain}:\n")
                for rdata in answers:
                    txt_record = ''.join([part.decode('utf-8') for part in rdata.strings])
                    self.site_info_text.insert(tk.END, f" - {txt_record}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed Dig TXT for {domain}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Dig TXT failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Dig TXT failed for {url}: {e}")
        threading.Thread(target=dig_txt).start()

    def perform_dig_cname(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def dig_cname():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"dig {domain} CNAME +short"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                resolver = dns.resolver.Resolver()
                answers = resolver.resolve(domain, 'CNAME')
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Dig CNAME Records for {domain}:\n")
                for rdata in answers:
                    self.site_info_text.insert(tk.END, f" - {rdata.target}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed Dig CNAME for {domain}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Dig CNAME failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Dig CNAME failed for {url}: {e}")
        threading.Thread(target=dig_cname).start()

    def perform_nslookup_any(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        def nslookup_any():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"nslookup -query=any {domain}"
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"NSLookup -Any Results for {domain}:\n{result.stdout}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.info(f"Performed NSLookup -Any for {domain}")
                else:
                    self.site_info_text.config(state='normal')
                    self.site_info_text.insert(tk.END, f"NSLookup -Any failed for {domain}:\n{result.stderr}\n")
                    self.site_info_text.see(tk.END)
                    self.site_info_text.config(state='disabled')
                    logging.error(f"NSLookup -Any failed for {domain}: {result.stderr}")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"NSLookup -Any failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"NSLookup -Any failed for {url}: {e}")
        threading.Thread(target=nslookup_any).start()

    def perform_wget_grep(self):
        url = self.site_url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return

        keyword = self.live_dork_search_var.get().strip()
        if not keyword:
            keyword = simpledialog.askstring("Keyword Input", "Enter the keyword to search for:", parent=self.root)
            if not keyword:
                messagebox.showerror("Error", "Keyword cannot be empty.")
                return

        def wget_grep():
            domain = url.replace('http://', '').replace('https://', '').split('/')[0]
            command = f"wget -q -O - http://{domain} | grep -i \"{keyword}\""
            self.site_info_text.config(state='normal')
            self.site_info_text.insert(tk.END, f"Executing Command: {command}\n")
            self.site_info_text.config(state='disabled')
            try:
                # Fetch webpage content using requests
                response = requests.get(f"http://{domain}", headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=10)
                matches = [line for line in response.text.split('\n') if keyword.lower() in line.lower()]
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Wget | Grep Results for {domain} with keyword '{keyword}':\n")
                for match in matches:
                    # Highlight keyword in red
                    start_idx = self.site_info_text.index(tk.INSERT)
                    self.site_info_text.insert(tk.END, f"{match}\n")
                    # Apply tag to the keyword occurrences
                    self.highlight_keyword_in_line(match, keyword)
                if not matches:
                    self.site_info_text.insert(tk.END, f"No matches found for keyword '{keyword}'.\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.info(f"Performed Wget | Grep for {domain} with keyword '{keyword}'")
            except Exception as e:
                self.site_info_text.config(state='normal')
                self.site_info_text.insert(tk.END, f"Wget | Grep failed: {e}\n")
                self.site_info_text.see(tk.END)
                self.site_info_text.config(state='disabled')
                logging.error(f"Wget | Grep failed for {url}: {e}")
        threading.Thread(target=wget_grep).start()

    def highlight_keyword_in_line(self, line, keyword):
        index = self.site_info_text.index(tk.INSERT + " linestart")
        lower_line = line.lower()
        lower_keyword = keyword.lower()
        start = 0
        while True:
            pos = lower_line.find(lower_keyword, start)
            if pos == -1:
                break
            start_idx = f"{index.split('.')[0]}.{int(index.split('.')[1]) + pos}"
            end_idx = f"{index.split('.')[0]}.{int(index.split('.')[1]) + pos + len(keyword)}"
            self.site_info_text.tag_add("keyword", start_idx, end_idx)
            start = pos + len(keyword)
        self.site_info_text.tag_configure("keyword", foreground="red")

    # Placeholder methods for commands not implemented
    # ...

    def open_github(self):
        webbrowser.open_new("https://github.com/zebbern")

    # Additional site information methods (WHOIS, DIG, etc.) are defined above

# Main function
def main():
    root = tk.Tk()
    app = PH470MGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
