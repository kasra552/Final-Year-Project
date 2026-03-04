import json
import os

LOG_FILE = "baseline_log.json"

def load_log():
    """Loads the existing log, or returns empty dict if none exists."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_log(log):
    """Saves the log dict to file."""
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=4)

def add_entry(filename, file_hash):
    """Adds or updates a file's hash in the log."""
    log = load_log()
    log[filename] = file_hash
    save_log(log)
    print(f"Logged: {filename} -> {file_hash[:10]}...")

def verify_file(filename, current_hash):
    """Compares current hash against the stored hash."""
    log = load_log()
    if filename not in log:
        return False, "File not found in log."
    if log[filename] == current_hash:
        return True, f"{filename} is unchanged."
    return False, f"{filename} has been TAMPERED with!"

def print_log():
    """Prints all entries in the log."""
    log = load_log()
    if not log:
        print("Log is empty.")
    for filename, file_hash in log.items():
        print(f"{filename}: {file_hash[:10]}...")