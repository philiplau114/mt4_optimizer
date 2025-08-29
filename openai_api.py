import requests
import time
from typing import List, Dict, Any

class OpenAIOptimizerAPI:
    def __init__(self, api_key, model="gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def suggest_optimization(self, metrics: Dict, parameters: List[Dict], objectives: List[str] = None) -> List[Dict]:
        prompt = self._build_prompt(metrics, parameters, objectives)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert MT4 trading parameter optimizer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 800
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        wait_seconds = 20
        for attempt in range(6):  # Up to 6 tries (exponential backoff)
            response = requests.post(self.api_url, json=payload, headers=headers)
            if response.status_code == 429:
                print(f"Rate limited by OpenAI. Waiting {wait_seconds} seconds...")
                time.sleep(wait_seconds)
                wait_seconds *= 2  # Exponential backoff: 20, 40, 80, 160, 320...
                continue
            response.raise_for_status()
            result = response.json()
            try:
                import json as pyjson
                content = result["choices"][0]["message"]["content"]
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                data = pyjson.loads(json_str)
                return data.get("to_optimize", [])
            except Exception as e:
                print("Failed to parse OpenAI response as JSON. Full response below:")
                print(result)
                return []
        raise RuntimeError("OpenAI API rate-limited too many times. Try again later.")

    def _build_prompt(self, metrics, parameters, objectives):
        obj_str = "; ".join(objectives) if objectives else "maximize profit and minimize drawdown"
        prompt = (
            "Given the following MT4 backtest summary (fields are key-value), "
            "and the list of parameters (with current value and range info), "
            f"advise which parameters to fine-tune, and what their start/end/step should be, to {obj_str}. "
            "Return your answer strictly as JSON in the format: {\"to_optimize\": [ {\"name\": ..., \"start\": ..., \"end\": ..., \"step\": ...}, ... ]}.\n"
            "Backtest metrics:\n"
        )
        for k, v in metrics.items():
            prompt += f"{k}: {v}\n"
        prompt += "\nParameters (as a list of dicts):\n"
        import json as pyjson
        prompt += pyjson.dumps(parameters, indent=2)
        return prompt