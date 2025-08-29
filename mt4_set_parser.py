import re
from typing import List, Dict, Any

# Sections to ignore in the set file
IGNORE_SECTIONS = [
    "========= General Setting =========",
    "****** Trading Time Settings ******",
    "========= Visual Setting ========="
]

class MT4SetParameter:
    def __init__(self, name, value, start=None, step=None, end=None, section=None):
        self.name = name
        self.value = value
        self.start = start
        self.step = step
        self.end = end
        self.section = section

    def as_dict(self):
        return {
            "name": self.name,
            "value": self.value,
            "start": self.start,
            "step": self.step,
            "end": self.end,
            "section": self.section
        }

class MT4SetFile:
    def __init__(self, filename):
        self.filename = filename
        self.parameters: List[MT4SetParameter] = []
        self.load()

    def load(self):
        with open(self.filename, encoding="utf-8") as f:
            lines = f.readlines()

        param_dict: Dict[str, Dict[str, Any]] = {}
        param_name = None
        current_section = None
        ignore_section = False

        for line in lines:
            line = line.strip()
            # Detect section headers
            if "=========" in line or "******" in line:
                current_section = line.replace("_", "").replace("=", "").replace("*", "").strip()
                ignore_section = any(sect in line for sect in IGNORE_SECTIONS)
                continue
            if ignore_section:
                continue
            if not line or "=" not in line:
                continue
            if "," in line:
                match = re.match(r"([a-zA-Z0-9_]+),([F123])=(.*)", line)
                if match:
                    name, typ, val = match.groups()
                    if name not in param_dict:
                        param_dict[name] = {"section": current_section}
                    param_dict[name][typ] = val
            else:
                name, val = line.split("=", 1)
                param_name = name
                if name not in param_dict:
                    param_dict[name] = {"section": current_section}
                param_dict[name]["value"] = val

        for k, v in param_dict.items():
            self.parameters.append(
                MT4SetParameter(
                    name=k,
                    value=v.get("value"),
                    start=v.get("1"),
                    step=v.get("2"),
                    end=v.get("3"),
                    section=v.get("section")
                )
            )

    def get_parameters(self):
        return [p.as_dict() for p in self.parameters]

    def get_tunable_parameters(self):
        # Only include parameters not in ignored sections
        return [p.as_dict() for p in self.parameters if p.section not in IGNORE_SECTIONS]

    def update_parameter(self, name, new_start=None, new_end=None, new_step=None):
        for param in self.parameters:
            if param.name == name:
                if new_start is not None:
                    param.start = new_start
                if new_end is not None:
                    param.end = new_end
                if new_step is not None:
                    param.step = new_step

    def save(self, out_filename):
        # Write only non-ignored sections; keep structure for compatibility
        current_section = None
        with open(out_filename, "w", encoding="utf-8") as f:
            for param in self.parameters:
                if param.section != current_section:
                    if param.section:
                        f.write(f"_{param.section}_\n")
                        current_section = param.section
                # Only write parameter if not in ignore section
                if param.section not in IGNORE_SECTIONS:
                    f.write(f"{param.name}={param.value}\n")
                    if param.start is not None:
                        f.write(f"{param.name},1={param.start}\n")
                    if param.step is not None:
                        f.write(f"{param.name},2={param.step}\n")
                    if param.end is not None:
                        f.write(f"{param.name},3={param.end}\n")