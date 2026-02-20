"""
Solution for Exercise 1.2: Verify File Connector Round-Trip

Reads the original input file and the sink output file, then compares
their contents to verify the full round-trip pipeline works correctly.

Usage:
    # Make sure connectors are deployed first (see exercise 01)
    python solutions/01-verify-roundtrip.py
"""

import json
import os
import sys
import time


# Paths relative to the module-04 directory
INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "input.txt")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "output.txt")


def read_lines(filepath: str) -> list[str]:
    """
    Read non-empty lines from a file.

    Args:
        filepath: Path to the file to read.

    Returns:
        List of stripped, non-empty lines.
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
    with open(filepath, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def try_decode_json_line(line: str) -> str:
    """
    Attempt to decode a JSON-encoded string line.

    If the line is a JSON string (e.g., '"Hello from Kafka Connect"'),
    decode it. Otherwise, return the line as-is.

    Args:
        line: A line that may or may not be JSON-encoded.

    Returns:
        The decoded string content.
    """
    try:
        decoded = json.loads(line)
        if isinstance(decoded, str):
            return decoded
    except (json.JSONDecodeError, TypeError):
        pass
    return line


def verify_roundtrip():
    """
    Compare input and output files to verify the round-trip pipeline.

    Reads both files, normalizes the output (handles JSON encoding),
    and reports whether the content matches.
    """
    print("=" * 60)
    print("File Connector Round-Trip Verification")
    print("=" * 60)

    input_lines = read_lines(INPUT_FILE)
    output_lines = read_lines(OUTPUT_FILE)

    if not input_lines:
        print(f"\nERROR: Input file is empty or missing: {INPUT_FILE}")
        print("Create the input file first:")
        print('  echo "Hello from Kafka Connect" > data/input.txt')
        sys.exit(1)

    if not output_lines:
        print(f"\nWARNING: Output file is empty or missing: {OUTPUT_FILE}")
        print("The sink connector may not have written yet. Waiting 10 seconds ...")
        time.sleep(10)
        output_lines = read_lines(OUTPUT_FILE)
        if not output_lines:
            print("Still empty. Make sure the sink connector is running.")
            sys.exit(1)

    # Normalize output lines (handle potential JSON encoding)
    normalized_output = [try_decode_json_line(line) for line in output_lines]

    print(f"\nInput file:  {INPUT_FILE}")
    print(f"  Lines: {len(input_lines)}")
    for i, line in enumerate(input_lines):
        print(f"  [{i}] {line}")

    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"  Lines: {len(output_lines)}")
    for i, line in enumerate(output_lines):
        print(f"  [{i}] {line}")

    if normalized_output != output_lines:
        print(f"\nNormalized output (JSON-decoded):")
        for i, line in enumerate(normalized_output):
            print(f"  [{i}] {line}")

    # Compare
    print("\n" + "-" * 60)
    print("Comparison Results:")

    if len(input_lines) != len(normalized_output):
        print(f"  LINE COUNT MISMATCH: input={len(input_lines)}, output={len(normalized_output)}")
        # Check if output is a subset
        if len(normalized_output) < len(input_lines):
            print("  Output has fewer lines. Sink may still be catching up.")
        else:
            print("  Output has more lines. There may be duplicate messages.")
    else:
        print(f"  Line count matches: {len(input_lines)}")

    matches = 0
    mismatches = 0
    for i, input_line in enumerate(input_lines):
        if i < len(normalized_output):
            if input_line == normalized_output[i]:
                matches += 1
            else:
                mismatches += 1
                print(f"  MISMATCH at line {i}:")
                print(f"    Input:  '{input_line}'")
                print(f"    Output: '{normalized_output[i]}'")
        else:
            mismatches += 1
            print(f"  MISSING at line {i}: '{input_line}'")

    print(f"\n  Matches: {matches}/{len(input_lines)}")

    if mismatches == 0 and len(input_lines) == len(normalized_output):
        print("\n  RESULT: Round-trip SUCCESSFUL! All lines match.")
        return True
    else:
        print(f"\n  RESULT: Round-trip INCOMPLETE. {mismatches} issue(s) found.")
        return False


if __name__ == "__main__":
    success = verify_roundtrip()
    sys.exit(0 if success else 1)
