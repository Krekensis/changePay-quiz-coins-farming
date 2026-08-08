import sys
import os
import time
import json
import argparse
import xml.etree.ElementTree as ET

os.system('')

class Log:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def info(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Log.CYAN}[INFO]{Log.RESET} {msg}")

    @staticmethod
    def success(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Log.GREEN}[SUCCESS]{Log.RESET} {msg}")

    @staticmethod
    def warn(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Log.YELLOW}[WARN]{Log.RESET} {msg}")

    @staticmethod
    def error(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Log.RED}[ERROR]{Log.RESET} {msg}")

    @staticmethod
    def action(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {Log.MAGENTA}[ACTION]{Log.RESET} {msg}")

try:
    import uiautomator2 as u2
    from uiautomator2.exceptions import ConnectError
except ImportError:
    Log.error("uiautomator2 is not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

DEFAULT_CONFIG = {
    "target_package": "in.changepay.customerAndroidApp",
    "waits": {
        "main_loop_poll": 0.3,
        "app_unfocused_retry": 3.0,
        "unknown_page_retry": 2.0,
        "error_recovery": 5.0,
        "normal_click": 0.3,
        "quiz_option_select": 0.1,
        "quiz_loading_transition": 1.5,
        "home_loading_transition": 0.5
    }
}

try:
    with open(CONFIG_PATH, 'r') as f:
        user_config = json.load(f)
        for k, v in user_config.items():
            if isinstance(v, dict):
                DEFAULT_CONFIG[k].update(v)
            else:
                DEFAULT_CONFIG[k] = v
except FileNotFoundError:
    pass
except Exception as e:
    Log.warn(f"Failed to load config.json: {e}. Using default settings.")
    
CONFIG = DEFAULT_CONFIG
TARGET_PACKAGE = CONFIG["target_package"]

def get_current_page(xml_dump):
    """Identifies the current page based on compound content-desc checks."""
    try:
        root = ET.fromstring(xml_dump)
    except ET.ParseError:
        return None
        
    descs = [n.get('content-desc', '') for n in root.iter('node') if n.get('content-desc')]
    
    def has_desc(text):
        return any(text in d for d in descs)
        
    def has_exact(text):
        return any(text == d for d in descs)

    if has_desc("Topic") and has_desc("questions correctly!"):
        return "09"
        
    if (has_exact("Next") or has_exact("Done")) and not has_desc("questions correctly!") and not has_desc("Topic"):
        return "08"
        
    if has_exact("Choose difficulty level") and has_exact(".. EASY") and has_exact("Dismiss"):
        return "07"
        
    if has_exact("Back") and has_exact("2nd Year") and has_exact("O\nObject-Oriented Programming"):
        return "06"
        
    if has_exact("Back") and has_exact("Computer Science & Engineering (CSE/IT)") and (has_exact("1\n1st Year") or has_exact("2\n2nd Year")):
        return "05"
        
    if has_exact("Back") and has_exact("Engineering") and has_exact("Computer Science & Engineering (CSE/IT)"):
        return "04"
        
    if has_exact("Back") and has_exact("ChangePay Quiz") and has_exact("Engineering"):
        return "03"
        
    if has_exact("Games") and has_exact("ChangePay Quiz"):
        return "02"
        
    if has_desc("Recommended for you") and has_desc("MAHE Bengaluru"):
        return "01"
        
    return None

def truncate_log(text, max_len=40):
    """Escapes newlines and truncates long text for clean console output."""
    text = text.replace('\n', '\\n')
    if len(text) > max_len:
        return text[:15] + "......" + text[-15:]
    return text

def click_desc(d, desc_text, contains=False):
    """Clicks an element exactly matching the content-desc, or containing if specified"""
    if contains:
        elem = d(descriptionContains=desc_text)
    else:
        elem = d(description=desc_text)
        
    log_text = truncate_log(desc_text)
        
    if elem.exists:
        elem.click()
        Log.action(f"Clicked -> '{log_text}'")
        return True
    else:
        Log.warn(f"Element not found -> '{log_text}'")
        return False

def handle_quiz_question(d, xml_dump):
    """Finds the 4 answer options, picks the longest, clicks it, then clicks Next."""
    try:
        root = ET.fromstring(xml_dump)
    except ET.ParseError:
        return False
        
    options = []
    for node in root.iter("node"):
        if node.get("class") == "android.view.View" and node.get("clickable", "false").lower() == "true":
            desc = node.get("content-desc", "")
            if desc:
                options.append(desc)
                
    if not options:
        Log.warn("No answer options found!")
        return False
        
    longest_option = max(options, key=len)
    log_text = truncate_log(longest_option)
    Log.info(f"Selected longest answer: ({len(longest_option)} chars).")
    
    click_desc(d, longest_option)
    time.sleep(CONFIG["waits"]["quiz_option_select"])
    
    next_btn = d(className="android.widget.Button", description="Next")
    done_btn = d(className="android.widget.Button", description="Done")
    
    if next_btn.exists:
        next_btn.click()
        Log.action("Clicked -> 'Next'")
        return True
    elif done_btn.exists:
        done_btn.click()
        Log.action("Clicked -> 'Done'")
        return True
    else:
        Log.warn("Neither Next nor Done button was found!")
        return False

def main():
    parser = argparse.ArgumentParser(description="ChangePay Quiz Farming Bot")
    parser.add_argument("--runs", type=int, default=0, help="Number of full quiz loops to run (0 for infinite)")
    args = parser.parse_args()
    
    Log.info("Connecting to Android device...")
    try:
        d = u2.connect()
        Log.success(f"Connected successfully to SDK {d.info.get('sdkInt', 'Unknown')}.")
    except Exception as e:
        Log.error(f"Failed to connect: {e}")
        sys.exit(1)
        
    runs_completed = 0
    max_runs = args.runs
    
    Log.info(f"Starting automation. Target runs: {'Infinite' if max_runs == 0 else max_runs}")
    print(f"{Log.BOLD}Press Ctrl+C to stop.{Log.RESET}")
    print("-" * 50)
    
    try:
        while True:
            try:
                if max_runs > 0 and runs_completed >= max_runs:
                    Log.success(f"Completed target of {max_runs} runs. Exiting.")
                    break
                    
                time.sleep(CONFIG["waits"]["main_loop_poll"])
                
                current_app = d.app_current()
                if current_app.get('package') != TARGET_PACKAGE:
                    Log.warn(f"ChangePay app is not open! (Current: {current_app.get('package')}). Waiting...")
                    time.sleep(CONFIG["waits"]["app_unfocused_retry"])
                    continue
                
                xml_dump = d.dump_hierarchy()
                current_page = get_current_page(xml_dump)
                
                if not current_page:
                    Log.warn("Unknown page or loading. Waiting...")
                    time.sleep(CONFIG["waits"]["unknown_page_retry"])
                    continue
                    
                Log.info(f"Detected Page: {Log.BOLD}Page {current_page}{Log.RESET}")
                
                clicked = False
                
                if current_page == "01":
                    clicked = click_desc(d, "GAMES\nTab 2 of 5")
                elif current_page == "02":
                    clicked = click_desc(d, "ChangePay Quiz")
                elif current_page == "03":
                    clicked = click_desc(d, "Engineering")
                elif current_page == "04":
                    clicked = click_desc(d, "Computer Science & Engineering (CSE/IT)")
                elif current_page == "05":
                    clicked = click_desc(d, "2\n2nd Year")
                elif current_page == "06":
                    clicked = click_desc(d, "O\nObject-Oriented Programming")
                elif current_page == "07":
                    clicked = click_desc(d, "HARD", contains=True)
                    if clicked:
                        time.sleep(CONFIG["waits"]["quiz_loading_transition"])
                elif current_page == "08":
                    clicked = handle_quiz_question(d, xml_dump)
                elif current_page == "09":
                    clicked = click_desc(d, "Exit")
                    if clicked:
                        runs_completed += 1
                        print(f"\n{Log.GREEN}{'='*50}")
                        print(f"   🎉 COMPLETED RUN {runs_completed} 🎉")
                        print(f"{'='*50}{Log.RESET}\n")
                        time.sleep(CONFIG["waits"]["home_loading_transition"])
                        
                if clicked and current_page not in ("07", "09", "08"):
                    time.sleep(CONFIG["waits"]["normal_click"])
                    
            except Exception as e:
                Log.error(f"Runtime error occurred: {e}")
                Log.info(f"Attempting to recover in {CONFIG['waits']['error_recovery']} seconds...")
                time.sleep(CONFIG["waits"]["error_recovery"])
                
    except KeyboardInterrupt:
        print(f"\n{Log.YELLOW}Bot stopped by user.{Log.RESET}")
        
if __name__ == "__main__":
    main()
