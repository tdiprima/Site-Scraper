import os
import re


def clean_file_content(content):
    # Define header pattern (from 'Skip Navigation' to common section markers like 'Home', 'About Us', or 'Research Overview')
    header_pattern = r'^Skip Navigation\n(?:.*\n)*?(?=^(?:Who We Are|Research Overview|About Us|\Z))'

    # Define footer pattern (from 'See pages' or institute name to the end)
    footer_pattern = r'^(See pages|Institute for Engineering-Driven Medicine|Global Health Institute|Stony Brook University\n.*?\nDiscrimination\n.*?\n©\nAdmin Login\n2025\nStony Brook University)$'

    # Remove header
    content = re.sub(header_pattern, '', content, flags=re.MULTILINE)

    # Remove footer
    content = re.sub(footer_pattern, '', content, flags=re.MULTILINE)

    # Clean up any extra blank lines
    content = re.sub(r'\n\s*\n+', '\n', content).strip()

    return content


def process_files_in_folder(input_folder, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.md'):  # Process only markdown files
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"cleaned_{filename}")

            # Read the file content
            with open(input_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Clean the content
            cleaned_content = clean_file_content(content)

            # Write the cleaned content to a new file
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(cleaned_content)

            print(f"Processed {filename} -> {output_path}")


if __name__ == "__main__":
    input_folder = "path/to/your/input/folder"  # Replace with your input folder path
    output_folder = "path/to/your/output/folder"  # Replace with your output folder path
    process_files_in_folder(input_folder, output_folder)
