import argparse
import json
import openai
import re
from set_file_updater import update_parameters

def extract_json_objects(text):
    """
    Extract all JSON code blocks from the OpenAI response and return as a list of dicts.
    Supports both single and multiple JSON code blocks.
    """
    # Try to find a single JSON array in the response
    array_match = re.search(r"\[\s*{.+?}\s*\]", text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except Exception:
            pass

    # Fallback: Find all ```json ... ``` code blocks (even if they're single objects)
    code_blocks = re.findall(r"```json(.*?)```", text, re.DOTALL)
    params = []
    for block in code_blocks:
        try:
            obj = json.loads(block.strip())
            # If it's a list, extend; if dict, append
            if isinstance(obj, list):
                params.extend(obj)
            else:
                params.append(obj)
        except Exception:
            continue
    return params

def get_current_value(param_name, set_path):
    """
    Extract the current value of a parameter from the .set file.
    """
    try:
        with open(set_path, encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith(param_name + "="):
                    try:
                        return float(line.strip().split("=")[1])
                    except Exception:
                        return None
    except Exception:
        pass
    return None

def prompt_openai_for_suggestions(param, set_content, htm_content, api_key, current_value=None):
    client = openai.OpenAI(api_key=api_key)
    prompt = (
        f"In the following MetaTrader 4 `.set` file, the parameter '{param}' is known to be important. "
        "Please suggest suitable start, end, and step values for optimizing '{param}'.\n\n"
        "When suggesting parameters to optimize, do not include any parameters that are under the 'General Setting', 'Trading Time Settings', or 'Visual Setting' sections in the .set file.\n\n"
        "To make the optimization process faster, please use wider steps and/or narrower ranges, and suggest only the most impactful parameters. "
        "Your goal is to minimize the total number of optimization rounds, so please keep the number of combinations as low as reasonably possible for a quick optimization run.\n"
        "However, it is also important that your suggested parameters, ranges, and steps allow the optimizer to find combinations that maximize net profit, maximize profit factor, and minimize drawdown in the resulting backtests. "
        "Balance both goals: fast optimization and the ability to achieve the best trading performance."
    )
    if current_value is not None:
        prompt += (
            f"\nFor '{param}', the current value is {current_value}. If this is a risk-related parameter (like DrawDown_SL_Money), please ensure your suggested range includes values below and at the current value, so the optimizer can search for safer settings."
        )
    prompt += f"\n\nHere is the .set file content:\n\n{set_content}\n"
    if htm_content:
        prompt += (
            f"\nBelow is a summary of the recent backtest report for context:\n\n{htm_content}\n"
        )
    prompt += (
        f"\nAdditionally, please review the file and suggest any other important parameters to optimize for improved performance, but exclude any from the above sections. "
        f"For each parameter (including '{param}' and any others you suggest), provide suitable start, end, and step values for MT4 optimization. "
        f"Return your answer as a single array in a code block in JSON format, or as multiple JSON code blocks if needed. Each object should have: name, start, end, step."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in MetaTrader 4 optimization and parameter tuning."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=1200,
    )
    resp = response.choices[0].message.content
    params = extract_json_objects(resp)
    if params:
        return params, resp
    else:
        print(f"Failed to find JSON parameter suggestions. Response was:\n{resp}")
        return [], resp

def get_file_head(path, max_chars=2000):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read(max_chars)
    except Exception:
        return ""

def main():
    parser = argparse.ArgumentParser(description="MT4 .set file optimizer/updater with OpenAI for parameter range suggestion")
    parser.add_argument("--set", required=True, help="Input .set file path")
    parser.add_argument("--htm", required=False, help="Backtest HTML report file (optional, for context)")
    parser.add_argument("--out", required=True, help="Output .set file path")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument("--param", required=True, help="Base parameter to highlight for optimization (e.g. DrawDown_SL_Money)")
    args = parser.parse_args()

    set_content = get_file_head(args.set, 4000)
    htm_content = get_file_head(args.htm, 2000) if args.htm else ""
    current_value = get_current_value(args.param, args.set)

    suggestions, raw_response = prompt_openai_for_suggestions(args.param, set_content, htm_content, args.api_key, current_value=current_value)

    if not suggestions:
        print(f"No suggestions found for optimization. Exiting.")
        # Still write the raw response for debugging/review
        suggestions_path = args.out + ".suggestions.txt"
        with open(suggestions_path, "w", encoding="utf-8") as f:
            f.write(raw_response)
        print(f"OpenAI raw response written to: {suggestions_path}")
        return

    # Write suggestions to a separate file for review
    suggestions_path = args.out + ".suggestions.json"
    with open(suggestions_path, "w", encoding="utf-8") as f:
        json.dump(suggestions, f, indent=2)
    print(f"OpenAI suggestions written to: {suggestions_path}")

    update_parameters(args.set, suggestions, args.out)
    print("Done. Updated .set file written to:", args.out)

if __name__ == "__main__":
    main()