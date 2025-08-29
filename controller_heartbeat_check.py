import time
import os

HEARTBEAT_LOG = r"C:\temp\uipath_heartbeat.log"
HEARTBEAT_TIMEOUT = 90  # seconds

def is_process_alive():
    if not os.path.exists(HEARTBEAT_LOG):
        return False
    with open(HEARTBEAT_LOG, "r") as f:
        lines = f.readlines()
    if not lines:
        return False
    last_line = lines[-1]
    # Extract timestamp (adjust regex/substring as needed)
    timestamp_str = last_line.split("]")[0][1:]
    last_time = time.mktime(time.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"))
    return (time.time() - last_time) < HEARTBEAT_TIMEOUT

if is_process_alive():
    print("Process is running")
else:
    print("Process is NOT running")