You are an expert in MetaTrader 4/5 optimization and parameter tuning.

## Optimization Task

**Mode:** {mode}  
- `fine_tune`: Suggest the 2–4 most impactful parameters, with ranges and steps for very fast optimization (target <30 minutes, <400 combinations). Use wider steps and/or narrower ranges.
- `construction`: Suggest 4–6 important parameters, balancing speed and thoroughness. Use moderate step sizes and practical ranges.
- `full_power`: Suggest 6–10 (or more, unlimited if appropriate) parameters for deep or exhaustive optimization. Use finer steps/ranges. No limit on total combinations unless performance is addressed.

**Section Filter:**  
{section_instruction}
- If specified, only select parameters from these sections: {suggest_sections}
- Do not suggest parameters from these sections: {ignore_sections}

**Requirements:**  
- For each suggested parameter, provide:
    - The parameter name (as in the set file)
    - Start, end, and step values suitable for the selected mode
    - A brief reason for inclusion
- Only include parameters that affect performance (risk, reward, entry/exit logic, money management, etc.)
- Exclude cosmetic/display/identification parameters unless explicitly requested
- Output your answer as a JSON array in a code block. Each object: { name, start, end, step, reason }

**Current .set file:**
```
[PASTE .set FILE CONTENT HERE]
```

**Parameter specification:**
```csv
[PASTE PhoenixSpec.csv CONTENT HERE]
```

**Optional: Recent Backtest HTML (for context)**
```
[PASTE HTML OR SUMMARY]
```

**Instructions:**  
- Carefully analyze the .set and spec files.
- Select parameters and suggest suitable ranges/steps as per the chosen mode.
- Target the total number of optimization combinations (start/step/end per mode) as appropriate for speed or thoroughness.
- Output ONLY the JSON code block as described.

---

**Example Output:**
```json
[
  { "name": "Lot_Multiplier", "start": 1.2, "end": 1.8, "step": 0.1, "reason": "Controls martingale risk/reward." },
  { "name": "Trailing_Start1", "start": 10, "end": 30, "step": 5, "reason": "Affects profit lock timing." }
]
```