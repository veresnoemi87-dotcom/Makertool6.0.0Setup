import sys
import os
import subprocess
import re
from datetime import datetime

VERSION = "6.0.0"
LOG_FILE = "log.txt"

# --- UTILITY LIBRARY ---

def log(action, status, detail="", code=None):
    """Generates a detailed, scannable log entry."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "=" * 60
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{divider}\n")
        log_entry = f"[{timestamp}] ACTION: {action} | STATUS: {status}"
        if code is not None: log_entry += f" | EXIT_CODE: {code}"
        f.write(log_entry + "\n")
        if detail: f.write(f"DETAILS:\n{detail}\n")

def fix_java_syntax(text):
    """Wraps println content in quotes if the user forgot them."""
    pattern = r'System\.out\.println\((?!"|\\")(.*?)(?!"|\\")\);'
    replacement = r'System.out.println("\1");'
    return re.sub(pattern, replacement, text)

def decode_binary(filename):
    """Helper to convert .mkr binary back to string."""
    with open(filename, "r") as f:
        bin_str = f.read().strip()
    return ''.join(chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8))

# --- CORE FUNCTIONS ---

def make_file(filename, text):
    try:
        if not filename.endswith(".mkr"): filename += ".mkr"
        fixed_text = fix_java_syntax(text)
        binary_data = ''.join(format(ord(c), '08b') for c in fixed_text)
        with open(filename, "w") as f:
            f.write(binary_data)
        log("MAKE", "SUCCESS", detail=f"Target: {filename}\nContent: {fixed_text}")
        print(f"Success: Encoded to {filename}")
    except Exception as e:
        log("MAKE", "ERROR", detail=str(e))
        print(f"Encoding Error: {e}")

def import_java():
    path = input("Enter path to .java file: ").strip().replace('"', '')
    if not os.path.exists(path):
        print("Error: File not found."); return
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        make_file("imported", content)
        log("IMPORT", "SUCCESS", f"Imported: {path}")
    except Exception as e:
        log("IMPORT", "ERROR", str(e)); print(f"Import Error: {e}")

def run_java(filename):
    try:
        if not os.path.exists(filename): print("File not found."); return
        code = decode_binary(filename)
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else "Runner"
        java_file = f"{class_name}.java"

        with open(java_file, "w", encoding="utf-8") as j:
            j.write(code)
        
        print(f"Executing Java: {class_name}...")
        process = subprocess.Popen(["java", java_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            if stdout: print(stdout)
            log("RUN_JAVA", "SUCCESS", detail=f"Class: {class_name}\nSTDOUT: {stdout}", code=0)
        else:
            print(f"Java Error:\n{stderr}")
            log("RUN_JAVA", "FAILED", detail=f"Class: {class_name}\nSTDERR: {stderr}", code=process.returncode)
            
        for ext in [".java", ".class"]:
            if os.path.exists(f"{class_name}{ext}"): os.remove(f"{class_name}{ext}")
    except Exception as e:
        log("RUN_JAVA", "EXCEPTION", detail=str(e)); print(f"System Error: {e}")

def run_python(filename):
    try:
        if not os.path.exists(filename): print("File not found."); return
        code = decode_binary(filename)
        temp_py = "temp_exec.py"
        with open(temp_py, "w", encoding="utf-8") as f: f.write(code)
            
        print(f"Executing Python: {filename}...")
        result = subprocess.run([sys.executable, temp_py], capture_output=True, text=True)
        
        if result.returncode == 0:
            if result.stdout: print(result.stdout)
            log("RUN_PY", "SUCCESS", detail=f"Output: {result.stdout}", code=0)
        else:
            print(f"Python Error:\n{result.stderr}")
            log("RUN_PY", "FAILED", detail=f"Stderr: {result.stderr}", code=result.returncode)

        if os.path.exists(temp_py): os.remove(temp_py)
    except Exception as e:
        log("RUN_PY", "EXCEPTION", detail=str(e)); print(f"System Error: {e}")

def delete_file(filename):
    if not filename.endswith(".mkr"): filename += ".mkr"
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Deleted {filename}")
        log("DELETE", "SUCCESS", f"Target: {filename}")
    else: print("File not found.")

# --- THE GLOBAL ENTRY POINT ---

def main():
    args = sys.argv[1:]
    
    # Version check
    if "--version" in args:
        print(f"MAKER CLI Version: {VERSION}")
        return

    if not args or "--help" in args:
        print("\nMAKER CLI - Universal Runner\n" + "-"*30)
        print("maker --version                    : Print current version")
        print("maker --file [name] --text [code]  : Encode code")
        print("maker --run [file].mkr             : Run as Java")
        print("maker --py [file].mkr              : Run as Python")
        print("maker --import                     : Import .java file")
        print("maker --delete [file]              : Delete .mkr file")
        print("maker --clear                      : Clear log.txt")
    
    elif "--clear" in args:
        with open(LOG_FILE, "w") as f: f.write(f"[{datetime.now()}] Log Reset\n")
        print("Log cleared.")
        
    elif "--import" in args:
        import_java()
        
    elif "--delete" in args:
        try:
            delete_file(args[args.index("--delete") + 1])
        except (IndexError, ValueError):
            print("Error: Specify filename after --delete")
            
    elif "--file" in args and "--text" in args:
        try:
            f_idx = args.index("--file")
            t_idx = args.index("--text")
            filename = args[f_idx + 1]
            content = " ".join(args[t_idx + 1:])
            make_file(filename, content)
        except (IndexError, ValueError):
            print("Error: Usage: maker --file [name] --text [content]")
            
    elif "--run" in args:
        try:
            run_java(args[args.index("--run") + 1])
        except (IndexError, ValueError):
            print("Error: Specify .mkr file after --run")
            
    elif "--py" in args:
        try:
            run_python(args[args.index("--py") + 1])
        except (IndexError, ValueError):
            print("Error: Specify .mkr file after --py")

if __name__ == "__main__":
    main()