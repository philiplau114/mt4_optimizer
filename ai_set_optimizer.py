import argparse
import json
import openai
import os

from set_file_updater import update_parameters

def read_file_head(path, max_chars=8000):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read(max_chars)
    except Exception:
        return ""

def load_prompt_template(template_path):
    with open(template_path, encoding="utf-8") as f:
        return f.read()

def build_prompt(
    prompt_template,
    mode,
    suggest_sections,
    ignore_sections,
    base_parameters,
    set_content,
    phoenix_spec_content,
    summary_csv_content
):
    section_instruction = ""
    if suggest_sections:
        section_instruction += f"Only select parameters from these sections: {', '.join(suggest_sections)}.\n"
    if ignore_sections:
        section_instruction += f"Do not suggest parameters from these sections: {', '.join(ignore_sections)}.\n"
    prompt = prompt_template.format(
        mode=mode,
        section_instruction=section_instruction,
        suggest_sections=", ".join(suggest_sections) if suggest_sections else "",
        ignore_sections=", ".join(ignore_sections) if ignore_sections else "",
        base_parameters=", ".join(base_parameters)
    )
    # Now fill in set, spec, and summary
    prompt = prompt.replace("[Upload .set FILE or paste content here]", set_content)
    prompt = prompt.replace("[Upload PhoenixSpec.csv or paste content here]", phoenix_spec_content)
    prompt = prompt.replace("[Upload SUMMARY.csv or paste content here]", summary_csv_content)
    return prompt

def extract_json_array_from_response(text):
    import re
    array_match = re.search(r"\[\s*{.+?}\s*\]", text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except Exception:
            pass
    # fallback: Find all ```json ... ``` code blocks
    code_blocks = re.findall(r"```json(.*?)```", text, re.DOTALL)
    params = []
    for block in code_blocks:
        try:
            obj = json.loads(block.strip())
            if isinstance(obj, list):
                params.extend(obj)
            else:
                params.append(obj)
        except Exception:
            continue
    return params

def count_tokens(text, model="gpt-4o"):
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception as e:
        print(f"Warning: Could not count tokens ({e}). Returning 0.")
        return 0

def optimize_set_file(
    template_path,
    mode,
    suggest_sections,
    ignore_sections,
    base_parameters,
    set_path,
    spec_path,
    summary_path,
    api_key,
    output_path,
    suggestion_json_path=None
):
    # Load contents
    prompt_template = load_prompt_template(template_path)
    set_content = read_file_head(set_path, 8000)
    phoenix_spec_content = read_file_head(spec_path, 8000)
    summary_csv_content = read_file_head(summary_path, 8000)

    # Section arguments
    suggest_sections_list = [s.strip() for s in suggest_sections.split(",")] if suggest_sections else []
    ignore_sections_list = [s.strip() for s in ignore_sections.split(",")] if ignore_sections else []

    # Handle multiple base parameters
    base_parameters_list = [s.strip() for s in base_parameters.split(",") if s.strip()]

    # Build prompt
    prompt = build_prompt(
        prompt_template,
        mode,
        suggest_sections_list,
        ignore_sections_list,
        base_parameters_list,
        set_content,
        phoenix_spec_content,
        summary_csv_content
    )

    # Print token count for verification
    token_count = count_tokens(prompt, model="gpt-4o")
    print(f"Prompt token count: {token_count}")

    # OpenAI call
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in MetaTrader 4/5 optimization and parameter tuning."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=1600,
    )
    resp_content = response.choices[0].message.content
    suggestions = extract_json_array_from_response(resp_content)
    if not suggestions:
        suggestions_path = output_path + ".suggestions.txt"
        with open(suggestions_path, "w", encoding="utf-8") as f:
            f.write(resp_content)
        print(f"[ERROR] No valid parameter suggestion JSON found. Raw response written to: {suggestions_path}")
        return None

    # Write suggestions to specified JSON file or default
    if suggestion_json_path:
        suggestions_json_path = suggestion_json_path
    else:
        suggestions_json_path = output_path + ".suggestions.json"
    with open(suggestions_json_path, "w", encoding="utf-8") as f:
        json.dump(suggestions, f, indent=2)
    print(f"AI parameter suggestions written to: {suggestions_json_path}")

    # Update parameters in .set file
    update_parameters(set_path, suggestions, output_path)
    print(f"Updated .set file written to: {output_path}")

    return output_path  # Return the output file path

def main():
    parser = argparse.ArgumentParser(description="AI-powered .set file optimizer using OpenAI and parameter suggestion prompt template.")
    parser.add_argument("--template", required=True, help="Path to ai_parameter_suggestion_prompt_template file (Markdown)")
    parser.add_argument("--mode", required=True, choices=["fine_tune", "construction", "full_power"], help="Optimization mode")
    parser.add_argument("--suggest-sections", required=False, help="Comma-separated section names to suggest (optional)")
    parser.add_argument("--ignore-sections", required=False, help="Comma-separated section names to ignore (optional)")
    parser.add_argument("--base-parameters", required=True, help="Comma-separated base parameters to highlight for optimization")
    parser.add_argument("--set", required=True, help="Input .set file path")
    parser.add_argument("--spec", required=True, help="PhoenixSpec.csv file path")
    parser.add_argument("--summary", required=True, help="SUMMARY.csv/backtest summary file path")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    parser.add_argument("--output", required=True, help="Output .set file path")
    parser.add_argument("--suggestion-json", required=False, help="Output path for suggestion JSON file (default: output.suggestions.json)")
    args = parser.parse_args()

    output_path = optimize_set_file(
        template_path=args.template,
        mode=args.mode,
        suggest_sections=args.suggest_sections,
        ignore_sections=args.ignore_sections,
        base_parameters=args.base_parameters,
        set_path=args.set,
        spec_path=args.spec,
        summary_path=args.summary,
        api_key=args.api_key,
        output_path=args.output,
        suggestion_json_path=args.suggestion_json
    )
    if output_path:
        print(output_path)

if __name__ == "__main__":
    main()