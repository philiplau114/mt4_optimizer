import subprocess
import time
import os

# === CONFIGURATION ===
UIROBOT_CMD = [
    r"C:\Program Files\UiPath\Studio\UiRobot.exe",
    r"C:\Users\Philip\Documents\UiPath\Packages\MT4.Backtesting.Automation.1.0.1-alpha.2.nupkg"
]
HEARTBEAT_LOG = r"C:\temp\uipath_heartbeat.log"
HEARTBEAT_INTERVAL = 60  # seconds

def main():
    # Ensure log directory exists
    os.makedirs(os.path.dirname(HEARTBEAT_LOG), exist_ok=True)

    # Start UiRobot.exe process
    process = subprocess.Popen(UIROBOT_CMD)
    print(f"Started UiRobot.exe with PID {process.pid}")

    try:
        while True:
            retcode = process.poll()
            if retcode is not None:
                # Process finished
                with open(HEARTBEAT_LOG, "a") as f:
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Process ended with code {retcode}\n")
                print(f"UiRobot.exe ended with code {retcode}")
                break
            # Write heartbeat
            with open(HEARTBEAT_LOG, "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat: process running\n")
            print("Heartbeat sent")
            time.sleep(HEARTBEAT_INTERVAL)
    except KeyboardInterrupt:
        print("Interrupted by user. Terminating UiRobot.exe...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()