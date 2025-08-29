import subprocess
import json

UIROBOT_PATH = r"C:\Users\Philip\AppData\Local\Programs\UiPath\Studio\UiRobot.exe"
PACKAGE_PATH = r"C:\Users\Philip\Documents\UiPath\Packages\MT4.Backtesting.Automation.1.0.1-alpha.2.nupkg"

set_files = [
    r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71 GBPUSD M30 P5316 PF2.3 DD614 T530 2022.07.23-2025.07.23 (SL 920).set"
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Return code:", result.returncode)
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)
    print("-" * 40)

if __name__ == "__main__":
    for set_file in set_files:
        run_uipath(set_file, job_id="1")