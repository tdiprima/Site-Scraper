#!/usr/bin/env python3
"""
Document Cleaning Script for Open WebUI Knowledge Collection
Fixes encoding and character issues that cause JSON parsing errors

# Clean all documents (with backup)
python document_cleaner.py /path/to/your/documents/folder --backup

# Clean without backup (use with caution)
python document_cleaner.py /path/to/your/documents/folder
"""

import os
import sys
import shutil
import unicodedata
from pathlib import Path
from datetime import datetime

def clean_text_content(content):
    """Clean problematic characters from text content"""
    fixes_applied = []
    
    # Remove null bytes
    if '\x00' in content:
        content = content.replace('\x00', '')
        fixes_applied.append("Removed null bytes")
    
    # Remove other problematic control characters (keep common ones like \n, \t, \r)
    cleaned_content = ""
    for char in content:
        if unicodedata.category(char)[0] == 'C' and char not in '\n\t\r':
            # Skip this control character
            if not any("control characters" in fix for fix in fixes_applied):
                fixes_applied.append("Removed control characters")
            continue
        cleaned_content += char
    content = cleaned_content
    
    # Replace smart quotes with regular quotes
    smart_quote_replacements = {
        '"': '"',  # Left double quotation mark
        '"': '"',  # Right double quotation mark
        ''': "'",  # Left single quotation mark
        ''': "'",  # Right single quotation mark
    }
    
    for smart, regular in smart_quote_replacements.items():
        if smart in content:
            content = content.replace(smart, regular)
            if not any("smart quotes" in fix for fix in fixes_applied):
                fixes_applied.append("Replaced smart quotes with regular quotes")
    
    # Replace problematic special characters
    special_char_replacements = {
        '–': '-',   # En dash
        '—': '--',  # Em dash
        '…': '...',  # Horizontal ellipsis
        '®': '(R)',  # Registered trademark
        '™': '(TM)', # Trademark
        '©': '(C)',  # Copyright
    }
    
    for special, replacement in special_char_replacements.items():
        if special in content:
            content = content.replace(special, replacement)
            if not any("special characters" in fix for fix in fixes_applied):
                fixes_applied.append("Replaced special characters")
    
    # Fix potential JSON-breaking characters by escaping them properly
    # Note: We're being conservative here - only fixing obvious issues
    # Most JSON issues will be resolved by the encoding fixes above
    
    # Normalize line endings to Unix style
    if '\r\n' in content:
        content = content.replace('\r\n', '\n')
        fixes_applied.append("Normalized line endings")
    
    # Remove any remaining carriage returns
    if '\r' in content:
        content = content.replace('\r', '\n')
        if not any("line endings" in fix for fix in fixes_applied):
            fixes_applied.append("Fixed line endings")
    
    return content, fixes_applied

def clean_document(file_path, backup_dir=None):
    """Clean a single document and return results"""
    results = {
        'filename': os.path.basename(file_path),
        'path': str(file_path),
        'original_size': 0,
        'cleaned_size': 0,
        'original_encoding': None,
        'cleaned_encoding': 'utf-8',
        'fixes_applied': [],
        'success': False,
        'error': None
    }
    
    try:
        # Get original file size
        results['original_size'] = os.path.getsize(file_path)
        
        # Create backup if backup directory is provided
        if backup_dir:
            backup_path = backup_dir / results['filename']
            shutil.copy2(file_path, backup_path)
        
        # Try to read the file with various encodings
        content = None
        encodings_to_try = ['utf-8', 'utf-8-sig', 'windows-1252', 'windows-1254', 'macroman', 'latin-1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                results['original_encoding'] = encoding
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            results['error'] = "Could not read file with any encoding"
            return results
        
        # Clean the content
        cleaned_content, fixes_applied = clean_text_content(content)
        results['fixes_applied'] = fixes_applied
        
        # Write the cleaned content back as UTF-8
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(cleaned_content)
        
        results['cleaned_size'] = os.path.getsize(file_path)
        results['success'] = True
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python document_cleaner.py <folder_path> [--backup]")
        print("  --backup: Create backups of original files")
        sys.exit(1)
    
    folder_path = Path(sys.argv[1])
    create_backup = '--backup' in sys.argv
    
    if not folder_path.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        sys.exit(1)
    
    if not folder_path.is_dir():
        print(f"Error: '{folder_path}' is not a directory")
        sys.exit(1)
    
    # Create backup directory if requested
    backup_dir = None
    if create_backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = folder_path / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        print(f"Backups will be saved to: {backup_dir}")
    
    # Common document extensions
    doc_extensions = {'.txt', '.md', '.pdf', '.doc', '.docx', '.rtf', '.html', '.htm', '.xml', '.json', '.csv', '.tsv'}
    
    # Find all documents
    documents = []
    for ext in doc_extensions:
        documents.extend(folder_path.glob(f'*{ext}'))
        documents.extend(folder_path.glob(f'**/*{ext}'))  # Include subdirectories
    
    if not documents:
        print(f"No documents found in '{folder_path}'")
        return
    
    print(f"Found {len(documents)} documents to clean...")
    print("=" * 60)
    
    all_results = []
    successful_cleans = 0
    total_fixes = 0
    
    for doc_path in sorted(documents):
        print(f"\nCleaning: {doc_path.name}")
        result = clean_document(doc_path, backup_dir)
        all_results.append(result)
        
        if result['success']:
            successful_cleans += 1
            if result['fixes_applied']:
                total_fixes += len(result['fixes_applied'])
                print(f"  ✅ Applied {len(result['fixes_applied'])} fixes:")
                for fix in result['fixes_applied']:
                    print(f"     - {fix}")
                
                # Show size change
                size_change = result['cleaned_size'] - result['original_size']
                if size_change != 0:
                    print(f"     - Size change: {size_change:+d} bytes")
                
                # Show encoding change
                if result['original_encoding'] != result['cleaned_encoding']:
                    print(f"     - Encoding: {result['original_encoding']} → {result['cleaned_encoding']}")
            else:
                print("  ✅ No fixes needed")
        else:
            print(f"  ❌ Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("CLEANING SUMMARY")
    print("=" * 60)
    print(f"Total documents processed: {len(all_results)}")
    print(f"Successfully cleaned: {successful_cleans}")
    print(f"Failed to clean: {len(all_results) - successful_cleans}")
    print(f"Total fixes applied: {total_fixes}")
    
    if create_backup:
        print(f"\nOriginal files backed up to: {backup_dir}")
    
    # Show most common fixes
    all_fixes = []
    for result in all_results:
        all_fixes.extend(result['fixes_applied'])
    
    if all_fixes:
        from collections import Counter
        fix_counts = Counter(all_fixes)
        print(f"\nMost common fixes applied:")
        for fix, count in fix_counts.most_common():
            print(f"  {count:3d}x {fix}")
    
    # Show files that still might have issues
    problem_files = []
    for result in all_results:
        if not result['success']:
            problem_files.append(result)
    
    if problem_files:
        print(f"\nFiles that still need attention:")
        for result in problem_files:
            print(f"  - {result['filename']}: {result['error']}")
    else:
        print(f"\n🎉 All files successfully cleaned!")
        print("Your documents should now work better with Open WebUI's knowledge collection.")

if __name__ == "__main__":
    main()