import subprocess
import json
import time
import os

UIROBOT_PATH = r"C:\Users\Philip\AppData\Local\Programs\UiPath\Studio\UiRobot.exe"
PACKAGE_PATH = r"C:\Users\Philip\Documents\UiPath\Packages\MT4.Backtesting.Automation.1.0.1-alpha.2.nupkg"
HEARTBEAT_LOG = r"C:\temp\uipath_heartbeat.log"
HEARTBEAT_INTERVAL = 600  # seconds

set_files = [
r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71_GBPNZD_M30_1500_P1979_DD369_20220819-20250819_SL500_WR77.84_PF4.12_T334_M463013893_V1_S233.set",
r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71_NZDCAD_H1_1500_P1156_DD775_20220812-20250812_WR80.04_PF1.66_T456_M917464664_V1_S50.set",
r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71_NZDCHF_M30_1500_P5188_DD547_20220829-20250827_SL600_WR66.6_PF3.63_T485_M891445183_V1_S367.set",
r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71_USDCHF_M30_1500_P-1489_DD2030_20220815-20250813_WR81.91_PF0.45_T199_M632423138_V1_S85.set"
]

def run_uipath(set_file, job_id="1"):
    input_args = {
        "in_InputSetFilePath": set_file,
        "in_JobId": job_id
    }
    input_args_json = json.dumps(input_args)
    cmd = [
        UIROBOT_PATH,
        "execute",
        "--file", PACKAGE_PATH,
        "--input", input_args_json
    ]
    print("Running:", " ".join(cmd))
    
    # Start the subprocess
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    last_heartbeat = 0

    while True:
        retcode = process.poll()
        now = time.time()
        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            with open(HEARTBEAT_LOG, "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat: {set_file} job {job_id} still running\n")
            print("Heartbeat sent")
            last_heartbeat = now
        if retcode is not None:
            # Process finished
            stdout, stderr = process.communicate()
            print("Return code:", retcode)
            print("STDOUT:\n", stdout)
            print("STDERR:\n", stderr)
            with open(HEARTBEAT_LOG, "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Job {job_id} for {set_file} ended with code {retcode}\n")
            print("-" * 40)
            break
        time.sleep(15)  # Check every 15 seconds

if __name__ == "__main__":
    os.makedirs(os.path.dirname(HEARTBEAT_LOG), exist_ok=True)
    for set_file in set_files:
        run_uipath(set_file, job_id="1")