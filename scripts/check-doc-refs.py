#!/usr/bin/env python3
"""
Check that README.md file:line references contain expected content.
Usage: python3 scripts/check-doc-refs.py
"""
import re
import sys
from pathlib import Path

# Mapping table rows: (concept, claimed_location, expected_token)
# Format: each entry is (description, "file:lines", "keyword to find in that range")
CHECKS = [
    ("Multi-stage", "Containerfile:1-21, 23-71", "FROM.*AS builder"),
    ("UBI base", "Containerfile:3, 24", "FROM.*ubi9/"),
    ("Non-root USER", "Containerfile:53-57, 63", "useradd"),
    ("ARG + ENV", "Containerfile:5-7, 26-35", "ARG.*VERSION"),
    ("EXPOSE", "Containerfile:65", "EXPOSE"),
    ("LABEL", "Containerfile:37-45", "LABEL name"),
    ("Exec-form", "Containerfile:70-71", "ENTRYPOINT"),
    ("Layer caching", "Containerfile:15-18, 61", "COPY requirements"),
    ("COPY --from", "Containerfile:51", "COPY --from=builder"),
    ("Secret file", "compose.yaml:10-13, 43-45, 89-91", "secrets:"),
    ("Secret in code", "app/main.py:25-37", "DB_PASSWORD_FILE"),
    ("Named volume", "compose.yaml:14-17, 85-87", "volumes:"),
    ("Bind :Z", "compose.yaml:16", ":Z"),
    ("Two networks", "compose.yaml:17-19, 46-48, 68-69, 74-83", "networks:"),
    ("Manual network", "scripts/manual-setup.sh:35-38", "podman network create"),
    ("depends_on", "compose.yaml:49-51, 70-71", "depends_on:"),
    ("container_name", "compose.yaml:6, 34, 65", "container_name:"),
    ("ports", "compose.yaml:66-67", "ports:"),
    ("PostgreSQL image", "compose.yaml:5", "postgresql-16"),
    ("No published DB", "compose.yaml:4-25", "db:"),
    ("Pinned tags", "Makefile:4-5, compose.yaml:5, 33, 64", "VERSION"),
    ("podman build", "Makefile:49-54, scripts/manual-setup.sh:73-78", "podman build"),
    ("podman run manual", "scripts/manual-setup.sh:48-61, 83-95, 105-110", "podman run"),
    ("network create", "scripts/manual-setup.sh:35-38", "network create"),
    ("secret create", "scripts/setup-secret.sh:48", "podman secret create"),
    ("volume create", "scripts/manual-setup.sh:43", "podman volume create"),
    ("save/load", "scripts/save-image.sh:14", "podman save"),
    ("generate kube", "scripts/generate-kube.sh:14-24", "podman.*kube"),
    ("pg_dump", "scripts/backup-db.sh:14", "pg_dump"),
    ("volume export", "scripts/export-volume.sh:20", "podman volume export"),
    ("inspect", "Makefile:121-129", "podman inspect"),
    ("events", "Makefile:131-132", "podman events"),
    ("logs", "Makefile:71", "podman-compose logs"),
    ("port", "Makefile:142", "podman port"),
    ("exec", "Makefile:134-145", "podman exec"),
    ("restart policies", "compose.yaml:19, 52, 72", "restart:"),
    ("healthcheck", "compose.yaml:20-25, 53-59", "healthcheck:"),
    ("HEALTHCHECK", "Containerfile:67-68", "HEALTHCHECK"),
]

def parse_location(loc):
    """Parse 'file:line' or 'file:start-end' into (file, [lines])"""
    parts = loc.split(':')
    if len(parts) != 2:
        return None, []
    
    file_path = parts[0].strip()
    line_spec = parts[1].strip()
    
    if '-' in line_spec:
        start, end = line_spec.split('-')
        lines = list(range(int(start), int(end) + 1))
    else:
        lines = [int(line_spec)]
    
    return file_path, lines

def check_reference(desc, location, expected_token):
    """Check if expected_token appears in the file at the given location"""
    # location can be "file:lines, file:lines, ..."
    locations = [l.strip() for l in location.split(',')]
    
    found = False
    for loc in locations:
        file_path, lines = parse_location(loc)
        if not file_path or not lines:
            continue
        
        path = Path(file_path)
        if not path.exists():
            print(f"  ✗ {desc}: file {file_path} not found")
            return False
        
        content = path.read_text()
        file_lines = content.splitlines()
        
        # Check if any of the specified lines match
        for line_num in lines:
            if line_num <= len(file_lines):
                line_content = file_lines[line_num - 1]
                if re.search(expected_token, line_content, re.IGNORECASE):
                    found = True
                    break
        
        if found:
            break
    
    if found:
        print(f"  ✓ {desc}: {location}")
        return True
    else:
        print(f"  ✗ {desc}: '{expected_token}' not found at {location}")
        return False

def main():
    print("Checking README.md concept mapping table references...\n")
    
    passed = 0
    failed = 0
    
    for desc, location, token in CHECKS:
        if check_reference(desc, location, token):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\nSome references are incorrect. Update README.md mapping table.")
        sys.exit(1)
    else:
        print("\nAll references verified ✓")
        sys.exit(0)

if __name__ == "__main__":
    main()
