# ChangePay Quiz Coins Farmer (Last updated 09/08/26)

An automated Python script designed specifically for students at **MAHE Bengaluru Campus** to passively farm quiz coins in the ChangePay Android application.

> [!WARNING]
> This script is provided for educational purposes only (not really). Use it responsibly.

---

## Prerequisites

Before you begin, make sure you have the following:
*   An Android smartphone with the ChangePay app installed and logged in.
*   A computer running Windows, macOS, or Linux.
*   **Python 3.8 or higher** installed on your computer.
*   A USB cable to connect your phone to your computer.

---

## Phone Setup (CRITICAL)

To allow the Python script to view your screen and simulate touches, you MUST enable specific Developer Options on your phone.

### Step 1: Enable Developer Options
1. Go to your phone's **Settings** > **About Phone**.
2. Tap the **Build Number** (or *OS Version*) 7 times rapidly until you see a toast message saying *"You are now a developer!"*.

### Step 2: Enable USB Debugging
1. Go to **Settings** > **System** > **Developer Options** (On some phones, this is under *Additional Settings*).
2. Scroll down and turn on **USB Debugging**.

### Step 3: Enable Security Settings (Xiaomi / Poco / Realme / Oppo users)
This step is **mandatory**. If you skip this, the script will crash with a `SecurityException` when trying to tap the screen.
1. In Developer Options, look directly underneath "USB Debugging".
2. Turn on **"USB debugging (Security settings)"** (or on some phones, **"Disable permission monitoring"**).
3. *Note for Xiaomi users:* You must have a SIM card inserted and be logged into a Mi Account to toggle this setting. You may have to accept 3 warning prompts. 

---

## Installation

1. **Clone the repository to your computer:**
   ```bash
   git clone https://github.com/Krekensis/changePay-quiz-coins-farming.git
   cd changePay-quiz-coins-farming
   ```

2. **Install the required Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Phone:**
   Connect your phone to your PC via USB. Run the following command to install the required background services onto your phone: (optional)
   ```bash
   python -m uiautomator2 init
   ```
   *(Keep an eye on your phone screen—you will need to tap **"Allow"** on the "Allow USB Debugging?" prompt that pops up).*

---

## How to use the script

1. Unlock your phone.
2. Open the ChangePay app.
3. Open your computer terminal in the project folder.

**To run the script infinitely (until you stop it):**
```bash
python src/farm.py
```
*To stop the script, press `Ctrl + C` in your terminal.*

**To run the script for a specific number of quizzes (e.g., 5 times):**
```bash
python src/farm.py --runs 5
```

---

## How the Logic Works
The script uses `uiautomator2` to read the Android UI hierarchy as XML. It matches unique `content-desc` signatures to figure out exactly what page it is on (Home, Courses, BTech Branches, etc.) and navigates accordingly.

When it reaches a quiz question, it takes advantage of a known quirk in the ChangePay app for a specific quiz: **the correct answer is always the option with the longest string length**. The script automatically reads all four options, selects the longest one, and clicks Next.
