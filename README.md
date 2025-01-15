# PDF Renamer Script

This script (`pdf-renamer.py`) is designed to rename PDF files by adding a date prefix extracted from the content of the PDF. It is useful for organizing PDF files chronologically, especially when dealing with invoices, reports, or other documents that contain dates.

## Features

- **Date Extraction**: Extracts dates from the content of PDF files using multiple patterns.
- **Renaming**: Renames PDF files by prefixing them with the extracted date in `YYYY-MM-DD` format.
- **Handles Duplicate Filenames**: Properly handles Windows-style duplicate filenames like `statement(1).pdf`, `statement(2).pdf`, etc.
- **Backup**: Creates a backup of the original files before renaming.
- **Dry Run**: Supports a dry-run mode to preview changes without renaming files.
- **Cross-Platform**: Works on both Windows and Linux.

---

## Prerequisites

Before using the script, ensure you have the following installed:

- **Python 3.7 or higher**
- **Required Python Packages**:
  - `pdfplumber`
  - `dateutil`
  - `argparse`
  - `shutil`
  - `concurrent.futures`

---

## Installation

### 1. Install Python
Make sure Python is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

### 2. Install Required Packages
Install the required Python packages using `pip`. Run the following command in your terminal or command prompt:

```bash
pip install pdfplumber python-dateutil
```

---

## Usage

### Basic Usage

The script can be used to rename PDF files in a directory or a single PDF file. It supports both full paths and relative paths.

#### Rename PDFs in a Directory
To rename all PDF files in a directory, run:

```bash
python pdf-renamer.py /path/to/directory
```

#### Rename a Single PDF File
To rename a single PDF file in the current directory, run:

```bash
python pdf-renamer.py "sample.pdf"
```

#### Dry Run Mode
To preview the changes without renaming files, use the `--dry-run` flag:

```bash
python pdf-renamer.py /path/to/directory --dry-run
```

#### Show Version
To display the script version, use the `-v` or `--version` flag:

```bash
python pdf-renamer.py -v
```

---

## Backup Behavior

- **Directory Mode**: The script creates a backup of all PDF files in the specified directory before renaming them. The backup is stored in a subdirectory named `backup_YYYYMMDD_HHMMSS`.
- **Single File Mode**: The script creates a backup of the single PDF file in the current directory before renaming it. The backup is stored in a subdirectory named `backup_YYYYMMDD_HHMMSS`.

---

## Handling Duplicate Filenames on Windows

On Windows, when you download multiple statements or invoices, they often have duplicate filenames like `statement(1).pdf`, `statement(2).pdf`, etc. This script is designed to handle such cases properly:

1. **Removes Duplicate Indicators**: The script removes the `(1)`, `(2)`, etc., from the filenames before renaming.
2. **Preserves Uniqueness**: If multiple files have the same base name (e.g., `statement.pdf`), the script appends a new counter to ensure unique filenames after renaming.

### Example:
Suppose you have the following files in a directory:
- `statement(1).pdf`
- `statement(2).pdf`

After running the script, they might be renamed to:
- `2023-10-25_statement.pdf`
- `2023-10-25_statement(1).pdf`

This ensures that the files are organized by date while maintaining unique filenames.

---

## Examples

### Example 1: Rename PDFs in a Directory
Suppose you have a directory `/documents` containing the following files:
- `invoice1.pdf`
- `report2.pdf`

Run the script:

```bash
python pdf-renamer.py /documents
```

The script will:
1. Create a backup of the files in `/documents/backup_20231025_123456`.
2. Rename the files based on the extracted dates, e.g., `2023-10-25_invoice1.pdf`.

### Example 2: Rename a Single PDF File
Suppose you have a file `sample.pdf` in the current directory. Run the script:

```bash
python pdf-renamer.py "sample.pdf"
```

The script will:
1. Create a backup of `sample.pdf` in `backup_20231025_123456/sample.pdf`.
2. Rename the file based on the extracted date, e.g., `2023-10-25_sample.pdf`.

### Example 3: Dry Run Mode
To preview the changes without renaming files, run:

```bash
python pdf-renamer.py /documents --dry-run
```

The script will display a preview of the changes without modifying any files.

---

## Command-Line Arguments

| Argument       | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `path`         | Path to a PDF file or directory containing PDF files.                       |
| `--dry-run`    | Simulate renaming without making changes.                                   |
| `-v`, `--version` | Show the script version and exit.                                         |

---

## Supported Date Formats

The script can extract dates in the following formats:
- `12 January 2023`
- `12/01/2023`
- `12-01-2023`
- `2023-01-12`
- `January 12, 2023`

---

## Troubleshooting

### 1. No PDF Files Found
Ensure that the specified directory or file path contains PDF files with valid extensions (`.pdf`).

### 2. Date Not Found
If the script cannot extract a date from a PDF file, it will skip renaming that file. Ensure that the PDF contains a date in one of the supported formats.

### 3. Permission Issues
Ensure that you have read and write permissions for the directory or file you are working with.

---

## License

This script is open-source and available under the [MIT License](LICENSE).

---

## Contributing

If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

---

## Author

[Your Name]
[Your Email]
[Your GitHub Profile]

---

This updated `README.md` now includes a section explaining how the script handles duplicate filenames on Windows, making it clear that the script is well-suited for organizing files like `statement(1).pdf`, `statement(2).pdf`, etc. Let me know if you need further adjustments!
