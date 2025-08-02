#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors gracefully."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"  {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e.stderr.strip()}")
        return False

def main():
    # Get commit message from command line or use default
    if len(sys.argv) > 1:
        commit_message = " ".join(sys.argv[1:])
    else:
        commit_message = "new post"
    
    print(f"Publishing blog with message: '{commit_message}'")
    print("=" * 50)
    
    # Build the site
    if not run_command("python build.py", "Building static site"):
        print("Build failed. Aborting.")
        sys.exit(1)
    
    # Check if there are any changes to commit
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("→ No changes to publish.")
        return
    
    # Git operations
    commands = [
        ("git add .", "Staging changes"),
        (f'git commit -m "{commit_message}"', "Committing changes"),
        ("git push origin main", "Pushing to GitHub")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            print(f"Failed at: {desc}")
            sys.exit(1)
    
    print("=" * 50)
    print("✅ Successfully published to https://co2sou.github.io/blog")

if __name__ == "__main__":
    main()