"""
Drop it in the directory with your cleaned .md files and run it - job's done.
"""

import glob
import os


def strip_header_footer(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # find header range
    start_idx = next(
        (i for i, l in enumerate(lines) if "Skip to main content" in l), None
    )
    end_idx = None
    if start_idx is not None:
        end_idx = next(
            (
                j
                for j in range(start_idx, len(lines))
                if "Google Summer of Code" in lines[j]
            ),
            start_idx,
        )

    # find footer start
    footer_patterns = (
        "Stony Brook Medicine",
        "Stony Brook University Hospital",
        "Stony Brook Children's Hospital",
    )
    footer_idx = next(
        (
            i
            for i, l in enumerate(lines)
            if any(l.startswith(p) for p in footer_patterns)
        ),
        None,
    )

    # build filtered lines
    new_lines = []
    for i, l in enumerate(lines):
        if start_idx is not None and start_idx <= i <= end_idx:
            continue
        if footer_idx is not None and i >= footer_idx:
            continue
        new_lines.append(l)

    # overwrite file
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def main():
    md_files = glob.glob(os.path.join(os.getcwd(), "*.md"))
    if not md_files:
        print("No markdown files found in this directory.")
        return

    for md in md_files:
        strip_header_footer(md)
        print(f"Cleaned: {os.path.basename(md)}")


if __name__ == "__main__":
    main()
