import pdfplumber
import re
import os
import argparse
import logging
import platform
import shutil
from dateutil import parser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


def clear_screen():
    """Clear the console screen based on the operating system."""
    if platform.system().lower() == "windows":
        os.system('cls')
    else:
        os.system('clear')


# Script version
VERSION = "1.0.0"


def find_latest_backup(directory: str) -> str | None:
    """
    Find the most recent backup directory.

    Args:
        directory (str): Base directory to search for backups

    Returns:
        str | None: Path to most recent backup directory or None if no backups exist
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
        directory (str): Current directory path
        backup_dir (str): Backup directory path

    Returns:
        bool: True if backup is valid (matches current files), False otherwise
    """
    current_files = {f: os.path.getmtime(os.path.join(directory, f))
                    for f in os.listdir(directory)
                    if f.endswith('.pdf')}

    backup_files = {f: os.path.getmtime(os.path.join(backup_dir, f))
                   for f in os.listdir(backup_dir)
                   if f.endswith('.pdf')}

    # Check if files and timestamps match
    return current_files == backup_files


def backup_needed(directory: str) -> tuple[bool, str | None]:
    """
    Determine if backup is needed by checking recent backups.

    Args:
        directory (str): Directory to check for backups

    Returns:
        tuple[bool, str | None]: (backup needed, path to recent valid backup)
    """
    latest_backup = find_latest_backup(directory)
    if not latest_backup:
        return True, None

    # Check if backup is recent (within last hour)
    backup_time = os.path.getctime(latest_backup)
    time_diff = datetime.now().timestamp() - backup_time
    if time_diff > 3600:  # More than 1 hour old
        return True, None

    # Compare files
    if compare_with_backup(directory, latest_backup):
        return False, latest_backup

    return True, None


def create_backup(directory: str) -> str:
    """
    Create a backup of PDF files in the specified directory.

    Args:
        directory (str): Path to the directory containing files

    Returns:
        str: Path to the backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(directory, f"backup_{timestamp}")

    try:
        os.makedirs(backup_dir)
        for file in os.listdir(directory):
            if file.endswith('.pdf'):
                src = os.path.join(directory, file)
                dst = os.path.join(backup_dir, file)
                shutil.copy2(src, dst)
        logging.info(f"Backup created in: {backup_dir}")
        return backup_dir
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        raise


def create_backup_for_single_file(file_path: str, directory: str) -> str:
    """
    Create a backup of a single PDF file in the specified directory.

    Args:
        file_path (str): Path to the PDF file to back up
        directory (str): Directory where the backup should be created

    Returns:
        str: Path to the backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(directory, f"backup_{timestamp}")

    try:
        os.makedirs(backup_dir)
        shutil.copy2(file_path, os.path.join(backup_dir, os.path.basename(file_path)))
        logging.info(f"Backup created in: {backup_dir}")
        return backup_dir
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        raise


def handle_backup(directory: str, pdf_files: list) -> str | None:
    """
    Interactive backup handling with user confirmation.

    Args:
        directory (str): Directory to backup
        pdf_files (list): List of PDF files to process

    Returns:
        str | None: Path to backup directory if created, None otherwise
    """
    if len(pdf_files) == 1:
        # Single file mode
        file_path = os.path.join(directory, pdf_files[0])
        needs_backup, recent_backup = backup_needed(directory)

        if not needs_backup and recent_backup:
            backup_time = datetime.fromtimestamp(os.path.getctime(recent_backup))
            time_diff = datetime.now() - backup_time
            minutes_ago = int(time_diff.total_seconds() / 60)

            print(f"\nRecent backup found ({minutes_ago} minutes ago).")
            print(f"Location: {recent_backup}")
            print("File unchanged since then.")

            while True:
                response = input("Create new backup anyway? (Y)es/(N)o [No]: ").strip().lower()
                if response in ['', 'n', 'no']:
                    return recent_backup
                elif response in ['y', 'yes']:
                    break
                else:
                    print("Please enter 'y' for Yes or 'n' for No")
        else:
            while True:
                response = input("\nDo you want to back up the file first? (Y)es/(N)o [Yes]: ").strip().lower()
                if response in ['', 'y', 'yes']:
                    break
                elif response in ['n', 'no']:
                    return None
                else:
                    print("Please enter 'y' for Yes or 'n' for No")

        try:
            return create_backup_for_single_file(file_path, directory)
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            while True:
                response = input("Continue without backup? (Y)es/(N)o [No]: ").strip().lower()
                if response in ['y', 'yes']:
                    return None
                elif response in ['', 'n', 'no']:
                    raise
                else:
                    print("Please enter 'y' for Yes or 'n' for No")
    else:
        # Directory mode (existing logic)
        needs_backup, recent_backup = backup_needed(directory)

        if not needs_backup and recent_backup:
            backup_time = datetime.fromtimestamp(os.path.getctime(recent_backup))
            time_diff = datetime.now() - backup_time
            minutes_ago = int(time_diff.total_seconds() / 60)

            print(f"\nRecent backup found ({minutes_ago} minutes ago).")
            print(f"Location: {recent_backup}")
            print("Files unchanged since then.")

            while True:
                response = input("Create new backup anyway? (Y)es/(N)o [No]: ").strip().lower()
                if response in ['', 'n', 'no']:
                    return recent_backup
                elif response in ['y', 'yes']:
                    break
                else:
                    print("Please enter 'y' for Yes or 'n' for No")
        else:
            while True:
                response = input("\nDo you want to back up files first? (Y)es/(N)o [Yes]: ").strip().lower()
                if response in ['', 'y', 'yes']:
                    break
                elif response in ['n', 'no']:
                    return None
                else:
                    print("Please enter 'y' for Yes or 'n' for No")

        try:
            return create_backup(directory)
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            while True:
                response = input("Continue without backup? (Y)es/(N)o [No]: ").strip().lower()
                if response in ['y', 'yes']:
                    return None
                elif response in ['', 'n', 'no']:
                    raise
                else:
                    print("Please enter 'y' for Yes or 'n' for No")


def extract_date_from_text(text: str) -> str | None:
    """
    Extract date from text using multiple patterns and fallback methods.

    Args:
        text (str): The text to search for dates.

    Returns:
        str | None: The extracted date in YYYY-MM-DD format, or None if no date is found.
    """
    # Define multiple date patterns to try
    date_patterns = [
        r'\b(\d{1,2}\s+\w{3,}\s+\d{4})\b',  # 12 January 2023
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',     # 12/01/2023
        r'\b(\d{1,2}-\d{1,2}-\d{4})\b',     # 12-01-2023
        r'\b(\d{4}-\d{1,2}-\d{1,2})\b',     # 2023-01-12
        r'\b(\w{3,}\s+\d{1,2},\s+\d{4})\b', # January 12, 2023
    ]

    # Try each pattern in order
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                date_str = match.group(1)
                parsed_date = parser.parse(date_str, dayfirst=True)
                return str(parsed_date.date())
            except (ValueError, TypeError):
                continue

    # Fallback: Look for dates in common positions
    lines = text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    date_str = match.group(1)
                    parsed_date = parser.parse(date_str, dayfirst=True)
                    return str(parsed_date.date())
                except (ValueError, TypeError):
                    continue

    return None


def extract_date(pdf_file: str) -> str | None:
    """
    Extract date from a PDF file with improved error handling.

    Args:
        pdf_file (str): Path to the PDF file.

    Returns:
        str | None: The extracted date in YYYY-MM-DD format, or None if no date is found.
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Try first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            date = extract_date_from_text(text)

            # If not found, try second page
            if not date and len(pdf.pages) > 1:
                second_page = pdf.pages[1]
                text = second_page.extract_text()
                date = extract_date_from_text(text)

            return date
    except Exception as e:
        logging.error(f"Error processing {pdf_file}: {e}")
        return None


def get_unique_filename(base_name: str, all_new_names: set) -> str:
    """
    Generate a unique filename using Windows-style numbering (n) for duplicates.

    Args:
        base_name (str): The base filename.
        all_new_names: Set of all new names already assigned

    Returns:
        str: A unique filename that does not conflict with existing files.
    """
    if base_name not in all_new_names:
        return base_name

    name, ext = os.path.splitext(base_name)
    counter = 1

    while f"{name}({counter}){ext}" in all_new_names:
        counter += 1

    return f"{name}({counter}){ext}"


def is_already_date_formatted(filename: str) -> bool:
    """
    Check if filename already starts with a date in YYYY-MM-DD format.

    Args:
        filename (str): The filename to check

    Returns:
        bool: True if filename already starts with YYYY-MM-DD format, False otherwise
    """
    date_prefix_pattern = r'^\d{4}-\d{2}-\d{2}_'
    return bool(re.match(date_prefix_pattern, filename))


def preview_changes(pdf_files: list, directory: str, stats: dict) -> tuple[dict, bool]:
    """
    Generate and display preview of filename changes.

    Args:
        pdf_files (list): List of PDF files to process
        directory (str): Directory containing the files
        stats (dict): Dictionary to track statistics

    Returns:
        tuple[dict, bool]: (changes dict, whether any changes are needed)
    """
    changes = {}
    any_changes_needed = False
    date_counts = {}  # Track number of files per date
    proposed_names = set()  # Track all proposed names to avoid duplicates

    # First pass - collect all dates
    for file in pdf_files:
        full_path = os.path.join(directory, file)
        extracted_date = extract_date(full_path)
        if extracted_date:
            date_counts[extracted_date] = date_counts.get(extracted_date, 0) + 1

    print("\nPreviewing changes:")
    print("-" * 80)
    print(f"{'Original Name':<50} -> {'New Name':<50}")
    print("-" * 80)

    # Second pass - generate new names
    date_counters = {}  # Track counter per date
    for file in pdf_files:
        # Skip if file is already properly formatted
        if is_already_date_formatted(file):
            print(f"{file:<50} -> [SKIPPED - Already formatted]")
            stats['skipped_formatted'] += 1
            continue

        any_changes_needed = True
        full_path = os.path.join(directory, file)
        extracted_date = extract_date(full_path)

        if extracted_date:
            # Remove Windows-style duplicate numbers and clean up the filename
            base_name = re.sub(r'\(\d+\)', '', file)  # Remove (1), (2), etc.
            base_name = base_name.replace('.pdf', '')  # Remove .pdf extension
            base_name = re.sub(r'\s+', '_', base_name.strip())  # Replace spaces with underscore

            # Create new filename with date prefix
            new_name = f"{extracted_date}_{base_name}.pdf"

            # Handle duplicates for same date
            if date_counts[extracted_date] > 1:
                if extracted_date not in date_counters:
                    date_counters[extracted_date] = 0
                else:
                    date_counters[extracted_date] += 1
                    new_name = f"{extracted_date}_{base_name}({date_counters[extracted_date]}).pdf"

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
    Process an individual PDF file by renaming it to the new name.

    Args:
        file (str): The filename of the PDF to process.
        new_name (str): The new filename to use.
        dry_run (bool): If True, simulate renaming without making changes.

    Returns:
        bool: True if rename was successful, False otherwise
    """
    # Get just the filenames for logging
    file_basename = os.path.basename(file)
    new_name_basename = os.path.basename(new_name)

    if not file_basename.endswith('.pdf'):
        logging.info(f"Skipping non-PDF file: {file_basename}")
        return False

    if dry_run:
        logging.info(f"Would rename: {file_basename} -> {new_name_basename}")
        return True
    else:
        try:
            os.rename(file, new_name)
            logging.info(f"Renamed: {file_basename} -> {new_name_basename}")
            return True
        except Exception as e:
            logging.error(f"Error renaming {file_basename}: {e}")
            return False


def main() -> None:
    """
    Main function to parse arguments and process PDF files in a directory.
    """
    # Clear the screen first
    clear_screen()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Rename PDF files by adding a date prefix.",
        usage="pdf_renamer.py [-h] [--dry-run] <file or directory>"
    )
    parser.add_argument("path", type=str, help="Path to a PDF file or directory containing PDF files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate renaming without making changes")
    parser.add_argument("-v", "--version", action="version", version=f"pdf_renamer v{VERSION}",
                       help="Show program's version number and exit")
    args = parser.parse_args()

    path = os.path.normpath(args.path)

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

