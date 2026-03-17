#!/usr/bin/env python3
"""
CatGuard 智能提交工具
自动检测变更、生成提交信息、推送到 GitHub
"""
import os
import subprocess
import datetime
from pathlib import Path

REPO_DIR = Path("/home/clawdbot/CatGuard-GitHub")
J1900_HOST = "administrator@192.168.31.80"
J1900_PASS = "123654789"
J1900_CODE_DIR = r"C:\CatGuard"

# 要同步的文件
SYNC_FILES = [
    "*.py",
    "*.bat",
    "*.sh",
    "*.md",
]

# 文件类型到提交前缀的映射
PREFIX_MAP = {
    "catguard_onnx.py": "feat",
    "catguard_profile.py": "feat",
    "catguard_detect.py": "feat",
    "benchmark": "perf",
    "test_": "test",
    "quantize": "build",
    "export": "build",
    "README": "docs",
}

def run_cmd(cmd, cwd=None):
    """运行命令"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def sync_from_j1900():
    """从 J1900 同步代码"""
    print("[1/4] 从 J1900 同步代码...")
    
    target_dir = REPO_DIR / "deployment" / "j1900"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for pattern in SYNC_FILES:
        cmd = f'sshpass -p "{J1900_PASS}" scp {J1900_HOST}:{J1900_CODE_DIR}\\\\{pattern} {target_dir}/'
        run_cmd(cmd)
    
    print("同步完成")

def get_changes():
    """获取变更文件"""
    code, stdout, _ = run_cmd("git status --porcelain", cwd=REPO_DIR)
    changes = []
    for line in stdout.strip().split('\n'):
        if line:
            status, filename = line[:2].strip(), line[3:]
            changes.append((status, filename))
    return changes

def generate_commit_message(changes):
    """智能生成提交信息"""
    if not changes:
        return "chore: no changes"
    
    # 分析变更类型
    prefixes = []
    for status, filename in changes:
        for key, prefix in PREFIX_MAP.items():
            if key in filename:
                prefixes.append(prefix)
                break
        else:
            prefixes.append("chore")
    
    # 选择最常见的前缀
    from collections import Counter
    prefix = Counter(prefixes).most_common(1)[0][0]
    
    # 生成描述
    if len(changes) == 1:
        desc = f"update {changes[0][1]}"
    else:
        desc = f"update {len(changes)} files"
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    return f"{prefix}: {desc} ({timestamp})"

def commit_and_push(message):
    """提交并推送"""
    print(f"\n[2/4] 暂存变更...")
    run_cmd("git add -A", cwd=REPO_DIR)
    
    print(f"\n[3/4] 提交: {message}")
    run_cmd(f'git commit -m "{message}"', cwd=REPO_DIR)
    
    print(f"\n[4/4] 推送到 GitHub...")
    code, stdout, stderr = run_cmd("git push origin main", cwd=REPO_DIR)
    
    if code == 0:
        print("✅ 推送成功!")
    else:
        print(f"❌ 推送失败: {stderr}")

def main():
    print("=" * 50)
    print("CatGuard 智能提交工具")
    print("=" * 50)
    print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 同步
    sync_from_j1900()
    
    # 检查变更
    changes = get_changes()
    if not changes:
        print("\n没有变更需要提交")
        return
    
    print(f"\n检测到 {len(changes)} 个文件变更:")
    for status, filename in changes:
        print(f"  {status} {filename}")
    
    # 生成提交信息
    message = generate_commit_message(changes)
    
    # 提交
    commit_and_push(message)
    
    print("\n" + "=" * 50)
    print("仓库: https://github.com/ColinStayInLife/CatGuard")
    print("=" * 50)

if __name__ == "__main__":
    main()