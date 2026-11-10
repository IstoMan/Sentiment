#!/usr/bin/env python3
"""
Validate README.md concept mapping table file:line references.
Parses the table from README.md and verifies all line references.
"""
import re
import sys
from pathlib import Path

def parse_readme_table(readme_path):
    """Extract all file:line references from the README table."""
    content = Path(readme_path).read_text()
    
    # Find the concept mapping table
    table_match = re.search(
        r'\| \*\*Multi-stage Containerfile\*\*.*?\n\n',
        content,
        re.DOTALL
    )
    if not table_match:
        print("Error: Could not find concept mapping table in README")
        return []
    
    table_text = table_match.group(0)
    
    # Parse table rows
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
        
        # Skip if location doesn't have backticks (likely a header or separator)
        if '`' not in location:
            continue
        
        # Extract all file:line references from backticks
        file_refs = re.findall(r'`([^`]+)`', location)
        for ref in file_refs:
            refs.append((concept, ref, line))
    
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

def check_references(refs, base_path='.'):
    """Check all file:line references."""
    passed = 0
    failed = 0
    
    for concept, location, _ in refs:
        # Parse all comma-separated parts
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
    
    print("Validating README.md concept mapping table references...\n")
    
    refs = parse_readme_table(readme_path)
    
    if not refs:
        print("Error: No references found in table")
        sys.exit(1)
    
    print(f"Found {len(refs)} table rows to check\n")
    
    passed, failed = check_references(refs)
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\nSome references are incorrect or out of range.")
        print("Update README.md mapping table with correct line numbers.")
        sys.exit(1)
    else:
        print("\nAll references validated ✓")
        sys.exit(0)

if __name__ == "__main__":
    main()
