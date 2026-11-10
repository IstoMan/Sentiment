#!/usr/bin/env python3
"""
Validate README.md concept mapping table file:line references.
Parses both tables from README.md, validates line references AND content tokens,
and checks that all #anchor links resolve to actual README headings.
"""
import re
import sys
from pathlib import Path

# Expected tokens for each concept - must appear in the cited range
EXPECTED_TOKENS = {
    "Multi-stage Containerfile": r"FROM.*AS (builder|test|runtime)",
    "UBI Base Images": r"FROM.*ubi",
    "Non-root USER": r"(useradd|USER\s+\d+)",
    "ARG + ENV with defaults": r"(ARG|ENV)",
    "EXPOSE": r"^EXPOSE",
    "LABEL": r"^LABEL",
    "Exec-form ENTRYPOINT/CMD": r"^(ENTRYPOINT|CMD)\s*\[",
    "Layer caching optimization": r"(COPY.*requirements|RUN.*pip install)",
    "COPY --from=builder": r"COPY.*--from",
    "Podman secret (file)": r"(secrets:|file:)",
    "Secret consumption in code": r"(DB_PASSWORD_FILE|get_db_password)",
    "Named volume": r"volumes:",
    "Bind mount with :Z": r":Z",
    "Two networks (real isolation)": r"(networks:|internal:|isolate:)",
    "User-created network with opts": r"podman network create.*--opt",
    "depends_on with condition": r"depends_on:.*service_",
    "container_name": r"container_name:",
    "ports (127.0.0.1)": r"127\.0\.0\.1",
    "PostgreSQL UBI image": r"postgresql",
    "No published DB port": r"db:",
    "Fully qualified tags (no latest)": r"(VERSION|:[0-9])",
    "podman build with args": r"podman build",
    "podman run manual": r"podman run",
    "podman network create": r"podman network create",
    "podman secret create": r"podman secret create",
    "podman volume create": r"podman volume create",
    "podman save/load": r"podman (save|load)",
    "podman generate/kube": r"podman (generate|kube)",
    "pg_dump backup": r"pg_dump",
    "podman volume export": r"podman volume export",
    "podman inspect --format": r"podman inspect.*--format",
    "podman events": r"podman.*events",
    "podman logs -f": r"podman.*logs",
    "podman port": r"podman.*port",
    "podman exec": r"podman exec",
    "restart policies": r"restart:",
    "compose healthcheck": r"healthcheck:",
    "HEALTHCHECK in Containerfile": r"^HEALTHCHECK",
    "UBI variants": r"FROM.*ubi",
    "DB env vars on empty volume": r"(database|init)",
    "Default network DNS issue": r"(network|DNS|dns)",
    "App binding (0.0.0.0)": r"(0\.0\.0\.0|PORT)",
    "compose up/down/down -v": r"(up|down)",
    "podman ps": r"podman.*ps",
}

def github_slugify(text):
    """Convert heading text to GitHub-style anchor slug."""
    # Remove markdown formatting
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](link) -> text
    text = re.sub(r'[*_`]', '', text)  # Remove emphasis markers
    
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove non-word chars except spaces and hyphens
    slug = re.sub(r'[\s_]+', '-', slug)   # Replace spaces/underscores with hyphens
    slug = re.sub(r'-+', '-', slug)        # Collapse multiple hyphens
    slug = slug.strip('-')                 # Remove leading/trailing hyphens
    
    return slug

def extract_readme_headings(readme_path):
    """Extract all headings from README and return mapping of anchor -> heading text."""
    content = Path(readme_path).read_text()
    headings = {}
    
    for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
        heading_text = match.group(2).strip()
        slug = github_slugify(heading_text)
        headings[slug] = heading_text
    
    return headings

def parse_readme_tables(readme_path):
    """Extract all file:line references from both README tables."""
    content = Path(readme_path).read_text()
    
    # Find all table sections (from first concept row until next ## heading or end)
    # Look for the main table starting with "Multi-stage"
    main_table_match = re.search(
        r'\| \*\*Multi-stage Containerfile\*\*.*?(?=\n##|\Z)',
        content,
        re.DOTALL
    )
    
    refs = []
    
    if main_table_match:
        table_text = main_table_match.group(0)
        refs.extend(parse_table_rows(table_text))
    
    # Also look for "Additional Concepts" table
    additional_match = re.search(
        r'### Additional Concepts.*?\n\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )
    
    if additional_match:
        table_text = additional_match.group(1)
        refs.extend(parse_table_rows(table_text))
    
    return refs

def parse_table_rows(table_text):
    """Parse individual table rows and extract references."""
    refs = []
    
    for line in table_text.split('\n'):
        if '|' not in line or line.startswith('|---'):
            continue
        
        # Extract cells
        cells = [c.strip() for c in line.split('|')]
        if len(cells) < 4:
            continue
        
        concept = cells[1].strip('*')
        location = cells[2]
        
        # Skip if location doesn't have backticks or parentheses (likely a header)
        if '`' not in location and '(' not in location:
            continue
        
        # Extract all file:line references from backticks
        file_refs = re.findall(r'`([^`]+)`', location)
        for ref in file_refs:
            refs.append((concept, ref, line))
        
        # Extract #anchor references
        anchor_refs = re.findall(r'\(#([^)]+)\)', location)
        for anchor in anchor_refs:
            refs.append((concept, f'#{anchor}', line))
    
    return refs

def parse_location_spec(spec):
    """
    Parse a location spec like 'file:1-10' or 'file:5' or '10-20' or '5'.
    Returns (file, [line_numbers]) or (None, []) if invalid.
    """
    if ':' in spec:
        parts = spec.split(':', 1)
        file_path = parts[0].strip()
        line_spec = parts[1].strip()
    else:
        # Bare numbers - return None for file, caller must use last file
        file_path = None
        line_spec = spec.strip()
    
    # Parse line spec
    lines = []
    if '-' in line_spec:
        try:
            start, end = line_spec.split('-', 1)
            lines = list(range(int(start), int(end) + 1))
        except ValueError:
            return file_path, []
    else:
        try:
            lines = [int(line_spec)]
        except ValueError:
            return file_path, []
    
    return file_path, lines

def check_token_in_range(concept, file_path, lines, base_path='.'):
    """Check that the expected token appears in the cited line range."""
    expected_token = EXPECTED_TOKENS.get(concept)
    if not expected_token:
        # No token defined for this concept, skip token check
        return True
    
    path = Path(base_path) / file_path
    try:
        file_lines = path.read_text().splitlines()
    except Exception as e:
        return False
    
    # Concatenate all lines in range for multi-line pattern matching
    range_lines = []
    for line_num in lines:
        if line_num < 1 or line_num > len(file_lines):
            continue
        range_lines.append(file_lines[line_num - 1])
    
    # Check pattern against concatenated content
    combined_content = '\n'.join(range_lines)
    pattern = re.compile(expected_token, re.IGNORECASE | re.DOTALL)
    if pattern.search(combined_content):
        return True
    
    return False

def check_references(refs, base_path='.', readme_headings=None):
    """Check all file:line references and anchors."""
    passed = 0
    failed = 0
    
    for concept, location, _ in refs:
        # Handle anchor references
        if location.startswith('#'):
            anchor = location[1:]  # Remove leading #
            if readme_headings and anchor in readme_headings:
                print(f"  ✓ {concept}: {location}")
                passed += 1
            else:
                print(f"  ✗ {concept}: anchor {location} not found in README headings")
                if readme_headings:
                    # Show similar anchors for debugging
                    similar = [a for a in readme_headings.keys() if anchor.replace('-', '') in a.replace('-', '')]
                    if similar:
                        print(f"     Similar anchors: {', '.join(['#' + s for s in similar[:3]])}")
                failed += 1
            continue
        
        # Parse all comma-separated parts for file:line references
        parts = [p.strip() for p in location.split(',')]
        
        all_parts_ok = True
        current_file = None
        
        for part in parts:
            file_path, lines = parse_location_spec(part)
            
            # Use previous file if this is a bare number
            if file_path is None:
                if current_file is None:
                    print(f"  ✗ {concept}: bare line numbers without file: {part}")
                    all_parts_ok = False
                    continue
                file_path = current_file
            else:
                current_file = file_path
            
            if not lines:
                print(f"  ✗ {concept}: invalid line spec: {part}")
                all_parts_ok = False
                continue
            
            # Check file exists
            path = Path(base_path) / file_path
            if not path.exists():
                print(f"  ✗ {concept}: file not found: {file_path}")
                all_parts_ok = False
                continue
            
            # Read file
            try:
                file_lines = path.read_text().splitlines()
            except Exception as e:
                print(f"  ✗ {concept}: error reading {file_path}: {e}")
                all_parts_ok = False
                continue
            
            # Check that all line numbers are valid
            for line_num in lines:
                if line_num < 1 or line_num > len(file_lines):
                    print(f"  ✗ {concept}: {file_path}:{line_num} out of range (file has {len(file_lines)} lines)")
                    all_parts_ok = False
                    break
            
            if not all_parts_ok:
                break
        
        # After validating line ranges, check for expected token
        if all_parts_ok and current_file:
            # Re-collect all lines for this reference
            all_lines = []
            for part in parts:
                file_path, lines = parse_location_spec(part)
                if file_path is None:
                    file_path = current_file
                all_lines.extend(lines)
            
            if not check_token_in_range(concept, current_file, all_lines, base_path):
                expected = EXPECTED_TOKENS.get(concept, "N/A")
                print(f"  ✗ {concept}: expected token '{expected}' not found in {current_file} lines {min(all_lines)}-{max(all_lines)}")
                all_parts_ok = False
        
        if all_parts_ok:
            print(f"  ✓ {concept}: {location}")
            passed += 1
        else:
            failed += 1
    
    return passed, failed

def main():
    readme_path = Path('README.md')
    
    if not readme_path.exists():
        print("Error: README.md not found")
        sys.exit(1)
    
    print("Validating README.md concept mapping tables...\n")
    
    # Extract README headings for anchor validation
    print("Extracting README headings for anchor validation...")
    headings = extract_readme_headings(readme_path)
    print(f"Found {len(headings)} headings\n")
    
    # Parse both tables
    refs = parse_readme_tables(readme_path)
    
    if not refs:
        print("Error: No references found in tables")
        sys.exit(1)
    
    print(f"Found {len(refs)} table rows to check\n")
    
    passed, failed = check_references(refs, readme_headings=headings)
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\nSome references are incorrect, out of range, or missing expected tokens.")
        print("Update README.md mapping tables with correct line numbers and content.")
        sys.exit(1)
    else:
        print("\nAll references validated ✓")
        sys.exit(0)

if __name__ == "__main__":
    main()
