import re

def normalize_param_name(name):
    """Normalize parameter names for loose matching and comparison."""
    # Remove case, whitespace, and force consistent comma placement
    name = name.strip().lower().replace(" ", "")
    return name

def init_set_file(set_file_path):
    """
    Perform a global replace in the .set file:
    Find ",F=1" and replace it with ",F=0".
    """
    with open(set_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all occurrences of ",F=1" with ",F=0"
    updated_content = content.replace(",F=1", ",F=0")

    with open(set_file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Set file initialized: {set_file_path}")

def parse_set_file(set_file_path):
    """Parse the .set file into an ordered list of (param, value) tuples."""
    params = []
    with open(set_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and ',' not in line.split('=')[0].strip().split()[-1]:
                param, value = line.split('=', 1)
                params.append((param, value))
            elif '=' in line and not line.startswith('#'):
                param, value = line.split('=', 1)
                params.append((param, value))
    return params

def write_set_file(params, out_path):
    """Write updated parameters back to a .set file."""
    with open(out_path, 'w', encoding='utf-8') as f:
        for k, v in params:
            f.write(f"{k}={v}\n")

def update_parameters(input_set_path, suggestions, output_set_path):
    """
    Update MT4 .set file using OpenAI suggestions.
    For each parameter in suggestions:
      - Write <param>,1 = start
      - Write <param>,2 = step
      - Write <param>,3 = stop/end
      - Write <param>,F = 1 (enable optimization)
    Remove any lines with keys like <param>,x,y or <param>,x,step
    """
    init_set_file(input_set_path)  # Ensure the set file is initialized
    params = parse_set_file(input_set_path)
    # Build lookup for easy update/overwrite
    param_dict = {normalize_param_name(k): (i, v) for i, (k, v) in enumerate(params)}
    updated_keys = set()

    for suggestion in suggestions:
        base_param = suggestion["name"].split(",")[0] if "," in suggestion["name"] else suggestion["name"]
        base_param = base_param.strip()
        # Set start, step, end (stop)
        for idx, field in zip([1,2,3], ["start", "step", "end"]):
            key = f"{base_param},{idx}"
            norm_key = normalize_param_name(key)
            value = suggestion.get(field)
            if value is not None:
                updated_keys.add(norm_key)
                if norm_key in param_dict:
                    orig_idx, _ = param_dict[norm_key]
                    params[orig_idx] = (key, str(value))
                else:
                    params.append((key, str(value)))
                    param_dict[norm_key] = (len(params)-1, str(value))
        # Set F flag for optimization
        flag_key = f"{base_param},F"
        flag_norm = normalize_param_name(flag_key)
        updated_keys.add(flag_norm)
        if flag_norm in param_dict:
            orig_idx, _ = param_dict[flag_norm]
            params[orig_idx] = (flag_key, "1")
        else:
            params.append((flag_key, "1"))
            param_dict[flag_norm] = (len(params)-1, "1")

    # Remove lines with keys like <param>,x,y or <param>,x,step/stop/end
    cleaned_params = []
    for k, v in params:
        # Remove keys with two or more commas (e.g. DrawDown_SL_Money,1,1 or DrawDown_SL_Money,1,step)
        if re.match(r".+,\d+,\w+$", k) or re.match(r".+,\d+,\d+$", k):
            continue
        cleaned_params.append((k, v))

    write_set_file(cleaned_params, output_set_path)
    print(f"Set file updated and written to {output_set_path}")

def update_single_parameter(set_file_path, parameter_name, parameter_value, output_set_file_path=None):
    """
    Update a single parameter in the .set file.
    If output_set_file_path is None, updates in-place.
    Example: update_single_parameter('file.set', 'Magic', 123456)
    """
    params = parse_set_file(set_file_path)
    norm_param = normalize_param_name(parameter_name)
    updated = False

    # Update if found, else add at the end
    for i, (k, v) in enumerate(params):
        if normalize_param_name(k) == norm_param:
            params[i] = (k, str(parameter_value))
            updated = True
            break
    if not updated:
        params.append((parameter_name, str(parameter_value)))

    out_path = output_set_file_path if output_set_file_path else set_file_path
    write_set_file(params, out_path)
    print(f"Parameter '{parameter_name}' updated to '{parameter_value}' in {out_path}")

if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Update MT4 .set file with parameter suggestions.")
    parser.add_argument('--input', '-i', required=True, help="Input .set file path")
    parser.add_argument('--suggestions', '-s', required=True, help="Suggestions JSON file path")
    parser.add_argument('--output', '-o', required=True, help="Output .set file path")
    args = parser.parse_args()

    with open(args.suggestions, "r", encoding="utf-8") as f:
        suggestions = json.load(f)
    update_parameters(args.input, suggestions, args.output)