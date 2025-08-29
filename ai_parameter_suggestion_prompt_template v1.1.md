You are an expert in MetaTrader 4/5 optimization and parameter tuning.

## Optimization Task

**Mode:** {mode}  
- `fine_tune`: Suggest the 2–4 most impactful parameters, with ranges and steps for very fast optimization. Use wider steps and/or narrower ranges.
- `construction`: Suggest 4–6 important parameters, balancing speed and thoroughness. Use moderate step sizes and practical ranges.
- `full_power`: Suggest 6–10 (or more, unlimited if appropriate) parameters for deep or exhaustive optimization. Use finer steps/ranges. No limit on total combinations unless performance is addressed.

**Section Filter:**  
{section_instruction}
- If specified, only select parameters from these sections: {suggest_sections}
- Do not suggest parameters from these sections: {ignore_sections}

**Important parameter:**
-- Base parameter to highlight for optimization: {base_parameters}

**Requirements:**  
- Only suggest parameters that exist in the provided .set file.  
- Do not invent or suggest any new parameters that are not present in the .set file.  
- Use only the exact parameter names (case sensitive) as found in the .set file.  
- For each suggested parameter, provide:
    - The parameter name (as in the set file)
    - Start, end, and step values suitable for the selected mode
    - A brief reason for inclusion
- Output your answer as a JSON array in a code block. Each object: {{ name, start, end, step }}

**Current .set file:**
```
[Upload .set FILE or paste content here]
```

**Parameter specification:**
```csv
[Upload PhoenixSpec.csv or paste content here]
```

**Recent Backtest summary metric in csv (for context)**
```
[Upload SUMMARY.csv or paste content here]
```

**Instructions:**  
- Carefully analyze the .set and spec files.
- Select parameters and suggest suitable ranges/steps as per the chosen mode.
- Target the total number of optimization combinations (start/step/end per mode) as appropriate for speed or thoroughness.
- Output ONLY the JSON code block as described.
