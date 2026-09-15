file_path = r"c:\yara-care-os\apps\hub\data\src\main\java\ir\sayda\yara\hub\data\repository\HomeAndConnectivityRepositories.kt"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "diagnostics = diagnostics," in line:
        if lines[i+3].strip() == "}":
            del lines[i+3]
            break

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
