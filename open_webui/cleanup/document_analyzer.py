#!/usr/bin/env python3
"""
Document Analysis Script for Open WebUI Knowledge Collection
Analyzes documents for potential issues that could cause JSON parsing errors
python document_analyzer.py /path/to/your/documents/folder
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
import unicodedata
import chardet

def detect_encoding(file_path):
    """Detect file encoding"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding'], result['confidence']
    except Exception as e:
        return None, 0

def analyze_text_content(content, filename):
    """Analyze text content for potential issues"""
    issues = []
    
    # Check for null bytes
    if '\x00' in content:
        null_count = content.count('\x00')
        issues.append(f"Contains {null_count} null bytes (\\x00)")
    
    # Check for control characters (except common ones like \n, \t, \r)
    control_chars = []
    for i, char in enumerate(content):
        if unicodedata.category(char)[0] == 'C' and char not in '\n\t\r':
            control_chars.append((char, i, ord(char)))
    
    if control_chars:
        unique_controls = set([c[0] for c in control_chars])
        issues.append(f"Contains {len(control_chars)} control characters: {[hex(ord(c)) for c in unique_controls]}")
    
    # Check for smart quotes and problematic Unicode
    smart_quotes = ['"', '"', ''', ''']
    found_smart = [q for q in smart_quotes if q in content]
    if found_smart:
        issues.append(f"Contains smart quotes: {found_smart}")
    
    # Check for other problematic characters
    problematic = ['–', '—', '…', '®', '™', '©']
    found_problematic = [p for p in problematic if p in content]
    if found_problematic:
        issues.append(f"Contains special characters: {found_problematic}")
    
    # Check for potential JSON-breaking characters
    json_breakers = ['\\', '"', '\b', '\f', '\v']
    found_breakers = []
    for char in json_breakers:
        if char in content:
            count = content.count(char)
            found_breakers.append(f"{repr(char)}({count})")
    if found_breakers:
        issues.append(f"JSON-sensitive characters: {found_breakers}")
    
    # Check for very long lines (could cause processing issues)
    lines = content.split('\n')
    long_lines = [i for i, line in enumerate(lines) if len(line) > 10000]
    if long_lines:
        issues.append(f"Very long lines (>10k chars): {len(long_lines)} lines")
    
    # Check for unusual line endings
    if '\r\n' in content and '\n' in content.replace('\r\n', ''):
        issues.append("Mixed line endings (\\r\\n and \\n)")
    
    # Check file size
    size_mb = len(content.encode('utf-8')) / (1024 * 1024)
    if size_mb > 10:
        issues.append(f"Large file size: {size_mb:.1f} MB")
    
    return issues

def analyze_document(file_path):
    """Analyze a single document"""
    results = {
        'filename': os.path.basename(file_path),
        'path': str(file_path),
        'size_bytes': 0,
        'encoding': None,
        'encoding_confidence': 0,
        'readable': False,
        'issues': [],
        'content_preview': ''
    }
    
    try:
        # Get file size
        results['size_bytes'] = os.path.getsize(file_path)
        
        # Detect encoding
        encoding, confidence = detect_encoding(file_path)
        results['encoding'] = encoding
        results['encoding_confidence'] = confidence
        
        # Try to read the file
        encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        
        for enc in encodings_to_try:
            if enc is None:
                continue
            try:
                with open(file_path, 'r', encoding=enc, errors='replace') as f:
                    content = f.read()
                results['encoding'] = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            results['issues'].append("Could not read file with any encoding")
            return results
        
        results['readable'] = True
        results['content_preview'] = content[:200] + ('...' if len(content) > 200 else '')
        
        # Analyze content
        content_issues = analyze_text_content(content, results['filename'])
        results['issues'].extend(content_issues)
        
        # Check if content looks like it might be binary
        if len(content) > 0:
            non_printable_ratio = sum(1 for c in content[:1000] if not c.isprintable() and c not in '\n\t\r') / min(len(content), 1000)
            if non_printable_ratio > 0.1:
                results['issues'].append(f"High ratio of non-printable characters: {non_printable_ratio:.2%}")
        
    except Exception as e:
        results['issues'].append(f"Error analyzing file: {str(e)}")
    
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python document_analyzer.py <folder_path>")
        sys.exit(1)
    
    folder_path = Path(sys.argv[1])
    
    if not folder_path.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        sys.exit(1)
    
    if not folder_path.is_dir():
        print(f"Error: '{folder_path}' is not a directory")
        sys.exit(1)
    
    # Common document extensions
    doc_extensions = {'.txt', '.md', '.pdf', '.doc', '.docx', '.rtf', '.html', '.htm', '.xml', '.json', '.csv', '.tsv'}
    
    # Find all documents
    documents = []
    for ext in doc_extensions:
        documents.extend(folder_path.glob(f'*{ext}'))
        documents.extend(folder_path.glob(f'**/*{ext}'))  # Include subdirectories
    
    if not documents:
        print(f"No documents found in '{folder_path}'")
        print(f"Looking for files with extensions: {', '.join(sorted(doc_extensions))}")
        return
    
    print(f"Analyzing {len(documents)} documents in '{folder_path}'...")
    print("=" * 60)
    
    all_results = []
    problematic_files = []
    
    for doc_path in sorted(documents):
        print(f"\nAnalyzing: {doc_path.name}")
        result = analyze_document(doc_path)
        all_results.append(result)
        
        if result['issues']:
            problematic_files.append(result)
            print(f"  ⚠️  {len(result['issues'])} issues found:")
            for issue in result['issues']:
                print(f"     - {issue}")
        else:
            print("  ✅ No issues detected")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total documents analyzed: {len(all_results)}")
    print(f"Documents with issues: {len(problematic_files)}")
    print(f"Clean documents: {len(all_results) - len(problematic_files)}")
    
    if problematic_files:
        print(f"\nMOST PROBLEMATIC FILES:")
        # Sort by number of issues
        sorted_problematic = sorted(problematic_files, key=lambda x: len(x['issues']), reverse=True)
        for i, result in enumerate(sorted_problematic[:5]):  # Top 5
            print(f"{i+1}. {result['filename']} ({len(result['issues'])} issues)")
            for issue in result['issues'][:3]:  # Show first 3 issues
                print(f"   - {issue}")
            if len(result['issues']) > 3:
                print(f"   ... and {len(result['issues']) - 3} more")
    
    # Save detailed results to JSON
    output_file = folder_path / 'document_analysis_results.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to: {output_file}")
    except Exception as e:
        print(f"\nCould not save results file: {e}")

if __name__ == "__main__":
    main()