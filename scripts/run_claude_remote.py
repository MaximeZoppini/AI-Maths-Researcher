#!/usr/bin/env python3
"""
Background runner for Claude Code Remote Control.
Maintains the remote session alive and connected to claude.ai/code.
"""
import os
import pty
import select
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def main():
    log_file_path = Path("/var/tmp/claude_remote.log")
    
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["claude", "remote-control", "--spawn=same-dir"],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        cwd=str(ROOT_DIR),
        close_fds=True
    )
    os.close(slave)

    time.sleep(2)
    try:
        os.write(master, b"y\n")
    except Exception:
        pass

    with log_file_path.open("w", encoding="utf-8") as f:
        while proc.poll() is None:
            r, _, _ = select.select([master], [], [], 1.0)
            if r:
                try:
                    data = os.read(master, 1024)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="ignore")
                    f.write(text)
                    f.flush()
                except OSError:
                    break

if __name__ == "__main__":
    main()
