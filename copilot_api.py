import requests
from typing import List, Dict, Any

class CopilotOptimizerAPI:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def suggest_optimization(self, metrics: Dict, parameters: List[Dict], objectives: List[str] = None) -> List[Dict]:
        payload = {
            "backtest_metrics": metrics,
            "set_file_parameters": parameters,
        }
        if objectives:
            payload["objectives"] = objectives
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("to_optimize", [])