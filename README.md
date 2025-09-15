# Canvas Module Downloader

A Python utility to download files from Canvas LMS course modules, including files embedded in pages.

## Features

- **Interactive Course Selection**: Browse all your Canvas courses organized by term
- **Module Discovery**: View all modules within a selected course  
- **Flexible Downloads**: Download files from a single module or all modules
- **Complete File Detection**: Downloads both direct file attachments AND files linked within pages
- **Smart Organization**: Files are organized in a clean directory structure
- **Duplicate Prevention**: Skips files that already exist

## What Gets Downloaded

- **Direct Files**: Files attached directly to modules
- **Page-Embedded Files**: Files linked within Canvas pages (handles `instructure_file_holder` structures)
- **Organized Storage**: Files are saved in structured directories by course and module

## Directory Structure

```
downloads/
└── [Course Name]/
    └── modules/
        └── [Module Name]/
            ├── files/           # Direct file attachments
            │   ├── document1.pdf
            │   └── spreadsheet.xlsx
            └── pages/           # Files found in pages
                ├── lecture_notes.pdf
                └── assignment.docx
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd canvas-module-downloader
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up credentials**:
   ```bash
   cp credentials.yaml.example credentials.yaml
   # Edit credentials.yaml with your Canvas details
   ```

## Configuration

### Getting Your Credentials

1. **API_URL**: Your institution's Canvas URL (e.g., `https://school.instructure.com`)

2. **API_KEY**: 
   - Log into Canvas
   - Go to Account → Settings  
   - Scroll to "Approved Integrations"
   - Click "+ New Access Token"
   - Copy the generated token

3. **USER_ID**:
   - After logging into Canvas, visit: `https://<your-canvas-url>/api/v1/users/self`
   - Find the `id` field in the JSON response

### Example credentials.yaml
```yaml
API_URL: https://canvas.university.edu
API_KEY: your_generated_token_here
USER_ID: 12345
```

## Usage

### Interactive Mode (Recommended)
```bash
python canvas_module_downloader.py
```
This will:
1. Show all your courses organized by term
2. Let you select a course
3. Display all modules in that course
4. Allow you to download from one module or all modules

### Direct Course Access
```bash
# Skip course selection if you know the course ID
python canvas_module_downloader.py --course-id 12345
```

### Custom Output Directory
```bash
python canvas_module_downloader.py -o /path/to/downloads
```

### Help
```bash
python canvas_module_downloader.py --help
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-c`, `--config` | Path to credentials YAML file | `credentials.yaml` |
| `--course-id` | Skip to specific course ID | Interactive selection |
| `-o`, `--output` | Download directory | `./downloads` |

## Example Workflow

1. **Run the script**: `python canvas_module_downloader.py`
2. **Select course**: Enter course number from the displayed list
3. **Choose download option**:
   - Enter module number (1, 2, 3...) for single module
   - Enter 'all' for all modules  
   - Enter 'q' to quit
4. **Files downloaded**: Check the `downloads/` directory

## File Types Handled

- **Direct Module Files**: Any file directly attached to a module
- **Page-Embedded Files**: Canvas file links found in page content, including:
  - `instructure_file_holder` structures
  - Direct Canvas file URLs
  - Download links

## Error Handling

- **Authentication errors**: Clear messages for invalid API tokens
- **Network issues**: Graceful handling of download failures
- **Missing files**: Warnings for files that can't be accessed
- **Duplicate prevention**: Automatic skip of existing files

## Requirements

- Python 3.6+
- Canvas API access token
- Network access to your Canvas instance

## Dependencies

- `canvasapi` - Canvas LMS API wrapper
- `beautifulsoup4` - HTML parsing for page content
- `requests` - HTTP downloads
- `pyyaml` - Configuration file parsing

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License - see LICENSE file for details

## Inspiration

This project was inspired by [canvas-student-data-export](https://github.com/davekats/canvas-student-data-export)