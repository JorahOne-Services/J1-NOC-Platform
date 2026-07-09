#!/usr/bin/env python3
import os
import subprocess
import sys
import time

REPO_DIR = "/opt/jnop"
NGINX_CONF = "/etc/nginx/sites-enabled/jnop-dashboard.conf"

def run(*cmd, **kwargs):
    print(f">>> {' '.join(map(str, cmd))}")
    result = subprocess.run(cmd, **kwargs)
    return result

def main():
    os.chdir(REPO_DIR)
    run("git", "status", "--short", "--branch")
    run("git", "config", "--global", "credential.helper", "!gh auth git-credential")
    run("git", "add", "-A")
    run("git", "commit", "-m", "autodeploy snapshot")
    run("git", "push", "origin", "main")
    run("docker", "compose", "build")
    run("docker", "compose", "up", "-d")
    for _ in range(20):
        time.sleep(1)
        health = run("curl", "-fsS", "http://127.0.0.1:8000/health", capture_output=True, text=True)
        if health.returncode == 0:
            print("Health:", health.stdout.strip())
            break
    else:
        print("Health check failed")
        sys.exit(1)
    run("docker", "compose", "ps")
    run("docker", "compose", "logs", "--tail=100")
    print("Autodeploy finished.")

if __name__ == "__main__":
    main()
