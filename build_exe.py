import os
import sys
import subprocess

# 解决 Windows 终端编码问题
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def build():
    print("=== Start Building UniMERNet Desktop App ===")
    sep = ";" if sys.platform.startswith("win") else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=UniMERNet-Snip",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--add-data=katex_template.html{sep}.",
        f"--add-data=configs{sep}configs",
        "--collect-all=unimernet",
        "--collect-data=timm",
        "--collect-data=transformers",
        "--hidden-import=PySide6.QtWebEngineWidgets",
        "--hidden-import=PySide6.QtWebEngineCore",
        "--hidden-import=torch",
        "--hidden-import=torchvision",
        "app.py"
    ]
    
    print("Executing command:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("\n[SUCCESS] Build completed! Artifacts generated in dist/ directory.")

if __name__ == "__main__":
    build()
