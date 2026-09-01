import sys
import subprocess

def build():
    print("=== 开始构建 UniMERNet 独立桌面软件 ===")
    sep = ";" if sys.platform.startswith("win") else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=UniMERNet-Snip",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--add-data=katex_template.html{sep}.",
        f"--add-data=configs{sep}configs",
        "--hidden-import=PySide6.QtWebEngineWidgets",
        "--hidden-import=PySide6.QtWebEngineCore",
        "--hidden-import=torch",
        "--hidden-import=torchvision",
        "--hidden-import=timm",
        "--hidden-import=albumentations",
        "app.py"
    ]
    
    subprocess.check_call(cmd)
    print("\n🎉 构建完成！独立软件存放在 dist/ 目录下。")

if __name__ == "__main__":
    build()