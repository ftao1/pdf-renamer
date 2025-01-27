"""
PDF Date Extractor and Renamer

This module provides functionality to rename PDF files by adding a date prefix extracted
from their contents. It supports both single file and directory operations, with automatic
backup creation and comprehensive error handling.

Features:
- Date extraction from PDF contents
- Automatic backup creation
- Preview of proposed changes
- Dry-run mode
- Multi-threaded processing
- Support for various date formats
"""

import os
import re
import logging
import platform
import shutil
import argparse
from datetime import datetime
from dateutil import parser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Script version
VERSION = "1.0.1"


def clear_screen() -> None:
    """Clear the console screen based on the operating system."""
    command = 'cls' if platform.system().lower() == "windows" else 'clear'
    os.system(command)


def find_latest_backup(directory: str) -> Optional[str]:
    """
    Find the most recent backup directory.

    Args:
        directory: Base directory to search for backups

    Returns:
        Path to most recent backup directory or None if no backups exist
    """
    backup_dirs = [d for d in os.listdir(directory) if d.startswith("backup_")]
    if not backup_dirs:
        return None

    # Sort by backup timestamp (backup_YYYYMMDD_HHMMSS format)
    backup_dirs.sort(reverse=True)
    return os.path.join(directory, backup_dirs[0])


def compare_with_backup(directory: str, backup_dir: str) -> bool:
    """
    Compare current directory with backup directory to determine if backup is still valid.

    Args:
        directory: Current directory path
        backup_dir: Backup directory path

    Returns:
        True if backup is valid (matches current files), False otherwise
    """
    current_files = {
        f: os.path.getmtime(os.path.join(directory, f))
        for f in os.listdir(directory) if f.endswith('.pdf')
    }

    backup_files = {
        f: os.path.getmtime(os.path.join(backup_dir, f))
        for f in os.listdir(backup_dir) if f.endswith('.pdf')
    }

    return current_files == backup_files


def backup_needed(directory: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if backup is needed by checking recent backups.

    Args:
        directory: Directory to check for backups

    Returns:
        Tuple of (backup needed, path to recent valid backup)
    """
    latest_backup = find_latest_backup(directory)
    if not latest_backup:
        return True, None

    # Check if backup is recent (within last hour)
    backup_time = os.path.getctime(latest_backup)
    if datetime.now().timestamp() - backup_time > 3600:  # More than 1 hour old
        return True, None

    return not compare_with_backup(directory, latest_backup), latest_backup


def create_backup(directory: str, files: List[str]) -> str:
    """
    Create a backup of specified PDF files in a directory.

    Args:
        directory: Path to the directory containing files
        files: List of files to backup

    Returns:
        Path to the backup directory

    Raises:
        OSError: If backup creation fails
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(directory, f"backup_{timestamp}")

    try:
        os.makedirs(backup_dir)
        for file in files:
            if file.endswith('.pdf'):
                shutil.copy2(
                    os.path.join(directory, file),
                    os.path.join(backup_dir, file)
                )
        logging.info(f"Backup created in: {backup_dir}")
        return backup_dir
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        raise


def handle_backup(directory: str, pdf_files: List[str]) -> Optional[str]:
    """
    Interactive backup handling with user confirmation.

    Args:
        directory: Directory to backup
        pdf_files: List of PDF files to process

    Returns:
        Path to backup directory if created, None otherwise
    """
    needs_backup, recent_backup = backup_needed(directory)

    if not needs_backup and recent_backup:
        backup_time = datetime.fromtimestamp(os.path.getctime(recent_backup))
        minutes_ago = int((datetime.now() - backup_time).total_seconds() / 60)

        print(f"\nRecent backup found ({minutes_ago} minutes ago)")
        print(f"Location: {recent_backup}")
        print(f"{'File' if len(pdf_files) == 1 else 'Files'} unchanged since then")

        if not _get_user_confirmation("Create new backup anyway?", default_yes=False):
            return recent_backup
    else:
        if not _get_user_confirmation("\nDo you want to back up files first?"):
            return None

    try:
        return create_backup(directory, pdf_files)
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        if not _get_user_confirmation("Continue without backup?", default_yes=False):
            raise
        return None


def _get_user_confirmation(prompt: str, default_yes: bool = True) -> bool:
    """
    Get user confirmation with a yes/no prompt.

    Args:
        prompt: Question to ask the user
        default_yes: True if default answer is Yes, False for No

    Returns:
        True if user confirms, False otherwise
    """
    default = "[Yes]" if default_yes else "[No]"
    while True:
        response = input(f"{prompt} (Y)es/(N)o {default}: ").strip().lower()
        if response in ['', 'y', 'yes']:
            return default_yes if response == '' else True
        if response in ['n', 'no']:
            return False
        print("Please enter 'y' for Yes or 'n' for No")


def extract_date_from_text(text: str) -> Optional[str]:
    """
    Extract date from text using multiple patterns and fallback methods.

    Args:
        text: The text to search for dates

    Returns:
        The extracted date in YYYY-MM-DD format, or None if no date is found
    """
    date_patterns = [
        r'\b(\d{1,2}\s+\w{3,}\s+\d{4})\b',  # 12 January 2023
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',      # 12/01/2023
        r'\b(\d{1,2}-\d{1,2}-\d{4})\b',      # 12-01-2023
        r'\b(\d{4}-\d{1,2}-\d{1,2})\b',      # 2023-01-12
        r'\b(\w{3,}\s+\d{1,2},\s+\d{4})\b',  # January 12, 2023
    ]

    def try_parse_date(date_str: str) -> Optional[str]:
        try:
            parsed_date = parser.parse(date_str, dayfirst=True)
            return str(parsed_date.date())
        except (ValueError, TypeError):
            return None

    # Try each pattern in order
    for pattern in date_patterns:
        if match := re.search(pattern, text):
            if date := try_parse_date(match.group(1)):
                return date

    # Fallback: Look for dates in first 10 lines
    for line in text.split('\n')[:10]:
        for pattern in date_patterns:
            if match := re.search(pattern, line):
                if date := try_parse_date(match.group(1)):
                    return date

    return None


def extract_date(pdf_file: str) -> Optional[str]:
    """
    Extract date from a PDF file with improved error handling.

    Args:
        pdf_file: Path to the PDF file

    Returns:
        The extracted date in YYYY-MM-DD format, or None if no date is found
    """
    import pdfplumber  # Import here to avoid overhead if not needed

    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Try first page
            if text := pdf.pages[0].extract_text():
                if date := extract_date_from_text(text):
                    return date

            # Try second page if available
            if len(pdf.pages) > 1:
                if text := pdf.pages[1].extract_text():
                    if date := extract_date_from_text(text):
                        return date

        return None
    except Exception as e:
        logging.error(f"Error processing {pdf_file}: {e}")
        return None


def get_unique_filename(base_name: str, existing_names: Set[str]) -> str:
    """
    Generate a unique filename using Windows-style numbering (n) for duplicates.

    Args:
        base_name: The base filename
        existing_names: Set of all names already assigned

    Returns:
        A unique filename that does not conflict with existing files
    """
    if base_name not in existing_names:
        return base_name

    name, ext = os.path.splitext(base_name)
    counter = 1

    while f"{name}({counter}){ext}" in existing_names:
        counter += 1

    return f"{name}({counter}){ext}"


def is_already_date_formatted(filename: str) -> bool:
    """
    Check if filename already starts with a date in YYYY-MM-DD format.

    Args:
        filename: The filename to check

    Returns:
        True if filename already starts with YYYY-MM-DD format, False otherwise
    """
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}_', filename))


def preview_changes(pdf_files: List[str], directory: str, stats: Dict) -> Tuple[Dict[str, str], bool]:
    """
    Generate and display preview of filename changes.

    Args:
        pdf_files: List of PDF files to process
        directory: Directory containing the files
        stats: Dictionary to track statistics

    Returns:
        Tuple of (changes dict, whether any changes are needed)
    """
    changes: Dict[str, str] = {}
    any_changes_needed = False
    date_counts: Dict[str, int] = {}
    proposed_names: Set[str] = set()

    # First pass - collect all dates
    for file in pdf_files:
        if date := extract_date(os.path.join(directory, file)):
            date_counts[date] = date_counts.get(date, 0) + 1

    # Display preview header
    print("\nPreviewing changes:")
    print("-" * 80)
    print(f"{'Original Name':<50} -> {'New Name':<50}")
    print("-" * 80)

    # Second pass - generate new names
    date_counters: Dict[str, int] = {}
    for file in pdf_files:
        if is_already_date_formatted(file):
            print(f"{file:<50} -> [SKIPPED - Already formatted]")
            stats['skipped_formatted'] += 1
            continue

        any_changes_needed = True
        if date := extract_date(os.path.join(directory, file)):
            # Clean up filename
            base_name = re.sub(r'\(\d+\)', '', file)  # Remove (1), (2), etc.
            base_name = os.path.splitext(base_name)[0]  # Remove extension
            base_name = re.sub(r'\s+', '_', base_name.strip())  # Replace spaces with underscore

            new_name = f"{date}_{base_name}.pdf"

            # Handle duplicates for same date
            if date_counts[date] > 1:
                date_counters[date] = date_counters.get(date, 0) + 1
                if date_counters[date] > 0:
                    new_name = f"{date}_{base_name}({date_counters[date]}).pdf"

            changes[file] = new_name
            proposed_names.add(new_name)
            print(f"{file:<50} -> {new_name:<50}")
        else:
            print(f"{file:<50} -> [SKIPPED - No date found]")
            stats['skipped_no_date'] += 1

    print("-" * 80)
    return changes, any_changes_needed


def process_file(file: str, new_name: str, dry_run: bool = False) -> bool:
    """
    Process an individual PDF file by renaming it.

    Args:
        file: The filename of the PDF to process
        new_name: The new filename to use
        dry_run: If True, simulate renaming without making changes

    Returns:
        True if rename was successful, False otherwise
    """
    file_basename = os.path.basename(file)
    new_name_basename = os.path.basename(new_name)

    if not file_basename.endswith('.pdf'):
        logging.info(f"Skipping non-PDF file: {file_basename}")
        return False

    if dry_run:
        logging.info(f"Would rename: {file_basename} -> {new_name_basename}")
        return True

    try:
        os.rename(file, new_name)
        logging.info(f"Renamed: {file_basename} -> {new_name_basename}")
        return True
    except Exception as e:
        logging.error(f"Error renaming {file_basename}: {e}")
        return False


def main() -> None:
    """Process command line arguments and orchestrate PDF file renaming."""
    clear_screen()

    parser = argparse.ArgumentParser(
        description="Rename PDF files by adding a date prefix extracted from their contents.",
        usage="pdf-renamer.py [-h] [--dry-run] <file or directory>"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to a PDF file or directory containing PDF files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate renaming without making changes"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"pdf-renamer v{VERSION}",
        help="Show program's version number and exit"
    )
    args = parser.parse_args()

    # Normalize path and determine operation mode
    path = os.path.normpath(args.path)
    directory = os.path.dirname(path) or os.getcwd()

    # Check if the input is a single file (either relative or absolute path)
    if os.path.isfile(path):
        # Single file mode
        directory = os.path.dirname(path) or os.getcwd()  # Use current directory if path has no dir
        pdf_files = [os.path.basename(path)]  # Use the filename only
    elif os.path.isdir(path):
        # Directory mode
        directory = path
        pdf_files = sorted([f for f in os.listdir(directory) if f.endswith('.pdf')])
    else:
        # Handle case where the input is a relative path to a file in the current directory
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, path)
        if os.path.isfile(file_path) and file_path.endswith('.pdf'):
            # Single file mode (relative path)
            directory = current_dir
            pdf_files = [path]  # Use the relative path
        else:
            logging.error(f"Invalid path or file not found: {path}")
            return

    if not pdf_files:
        logging.error("No PDF files found in the specified path")
        return

    # Initialize statistics
    stats = {
        'total_files': len(pdf_files),
        'renamed': 0,
        'skipped_formatted': 0,
        'skipped_no_date': 0,
        'errors': 0
    }

    # Handle backup
    try:
        backup_dir = handle_backup(directory, pdf_files)
        if backup_dir:
            print(f"Backup available in: {backup_dir}")
    except Exception as e:
        print(f"Backup creation failed: {e}")
        return

    # Preview changes
    changes, changes_needed = preview_changes(pdf_files, directory, stats)

    # Exit if no changes needed
    if not changes_needed:
        print("\nFiles are already renamed. Exiting.")
        return

    # Ask for confirmation only if changes are needed
    while True:
        response = input("\nProceed with renaming? (Y)es/(N)o [Yes]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            break
        elif response in ['n', 'no']:
            print("Operation cancelled by user")
            return
        else:
            print("Please enter 'y' for Yes or 'n' for No")

    # Process files with the confirmed new names
    with ThreadPoolExecutor() as executor:
        futures = []
        for file, new_name in changes.items():
            future = executor.submit(process_file,
                                  os.path.join(directory, file),
                                  os.path.join(directory, new_name),
                                  args.dry_run)
            futures.append((future, file))

        for future, file in futures:
            try:
                if future.result():
                    stats['renamed'] += 1
                else:
                    stats['errors'] += 1
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                stats['errors'] += 1

    # Print final summary
    print("\nSummary:")
    print(f"- Files processed: {stats['total_files']}")
    print(f"- Successfully renamed: {stats['renamed']}")
    print(f"- Skipped (already formatted): {stats['skipped_formatted']}")
    print(f"- Skipped (no date found): {stats['skipped_no_date']}")
    print(f"- Errors: {stats['errors']}")

if __name__ == "__main__":
    main()
