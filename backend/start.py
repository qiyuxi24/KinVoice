"""
一键启动 KinVoice 后端
用法：cd backend && python start.py
功能：自动检查 .env → 安装依赖 → 初始化数据库 → 启动 Uvicorn
"""
import subprocess
import sys
import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(str(BASE_DIR))

STEP_OK = "  ✓"
STEP_FAIL = "  ✗"
STEP_INFO = "  →"


def run(cmd: list[str], desc: str) -> bool:
    """运行命令，失败时打印错误并返回 False"""
    print(f"{STEP_INFO} {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{STEP_FAIL} {desc} 失败")
        if result.stderr:
            print(f"    错误: {result.stderr.strip()}")
        return False
    print(f"{STEP_OK} {desc}")
    return True


def main():
    print("=" * 50)
    print("  KinVoice 后端一键启动")
    print("=" * 50)

    # ── 1. 检查 .env 文件 ──
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        print(f"{STEP_INFO} .env 不存在，从 .env.example 复制...")
        example = BASE_DIR / ".env.example"
        if example.exists():
            env_path.write_text(example.read_text(), encoding="utf-8")
            print(f"{STEP_OK} 已生成 .env，请编辑填入 API Key 后重新运行")
            print(f"     文件位置: {env_path}")
        else:
            print(f"{STEP_FAIL} .env.example 也不存在，无法继续")
        return

    # 快速校验 LLM_API_KEY
    env_content = env_path.read_text(encoding="utf-8")
    if "sk-your-key-here" in env_content:
        print(f"{STEP_FAIL} 请先编辑 backend/.env，填入真实的 LLM_API_KEY")
        return

    print(f"{STEP_OK} .env 文件已就绪")

    # ── 2. 安装/更新依赖 ──
    req_path = BASE_DIR / "requirements.txt"
    if not req_path.exists():
        print(f"{STEP_FAIL} requirements.txt 不存在")
        return

    if not run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
               "安装 Python 依赖"):
        print("    提示: 请确保已安装 Python 3.10+ 并激活虚拟环境")
        return

    # ── 3. 初始化数据库 ──
    # 先确保 data 目录存在
    (BASE_DIR / "data").mkdir(exist_ok=True)
    (BASE_DIR / "logs").mkdir(exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "init_db.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"{STEP_FAIL} 数据库初始化失败")
        print(f"    错误: {result.stderr.strip()}")
        return
    print(f"{STEP_OK} 数据库初始化完成")

    # ── 4. 启动 Uvicorn ──
    print()
    print("=" * 50)
    print("  启动服务...")
    print(f"  API 文档: http://localhost:8000/docs")
    print(f"  健康检查: http://localhost:8000/ping")
    print("=" * 50)
    print()

    # 使用 uvicorn 模块方式启动，确保日志输出正常
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    )


if __name__ == "__main__":
    main()
