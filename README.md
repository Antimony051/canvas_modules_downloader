# Canvas Module Downloader

A Python utility to download files from Canvas LMS course modules, including files embedded in pages, assignments, and discussions.

## Features

- **Interactive Course Selection**: Browse all your Canvas courses organized by term
- **Module Discovery**: View all modules within a selected course
- **Flexible Downloads**: Download files from a single module or all modules
- **Complete File Detection**: Downloads files from direct attachments, pages, assignments, and discussion topics
- **Smart Organization**: Files are organized by their Canvas folder structure or module name
- **Completeness Report**: Shows how many files were discovered vs. the total in each Canvas folder
- **Duplicate Prevention**: Skips files that already exist

## What Gets Downloaded

- **Direct Files**: Files attached directly to modules
- **Page-Embedded Files**: Files linked within Canvas pages
- **Assignment Files**: Files embedded in assignment descriptions
- **Discussion Files**: Files embedded in discussion topic bodies

## Directory Structure

```
downloads/
└── [Course Name]/
    ├── folders/           # Files whose Canvas folder is known
    │   ├── [folder-path]/
    │   │   ├── document.pdf
    │   │   └── slides.pptx
    │   └── ...
    └── modules/           # Files with no resolvable folder (e.g. locked files)
        └── [Module Name]/
            └── lecture_notes.pdf
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd canvas-module-downloader
   ```

2. **Install Python dependencies**:
   ```bash
   uv sync
   ```

3. **Set up credentials**:
   ```bash
   bash setup.sh
   ```
   This will prompt you for your Canvas URL and API token and write `credentials.yaml` automatically.

## Configuration

### Getting Your Credentials

1. **API_URL**: Your institution's Canvas URL (e.g., `https://school.instructure.com`)

2. **API_KEY**:
   - Log into Canvas
   - Go to Account → Settings
   - Scroll to "Approved Integrations"
   - Click "+ New Access Token"
   - Copy the generated token

### Example credentials.yaml
```yaml
API_URL: https://canvas.university.edu
API_KEY: your_generated_token_here
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
   - Enter module number (1, 2, 3...) for a single module
   - Enter `all` for all modules
   - Enter `q` to quit
4. **Files downloaded**: Check the `downloads/` directory

## Error Handling

- **Authentication errors**: Clear messages for invalid API tokens
- **Locked files**: Two-tier resolution tries the public URL fallback before giving up
- **Network issues**: Graceful handling of download failures
- **Missing content**: Warnings for pages, assignments, or discussions that can't be fetched
- **Duplicate prevention**: Automatic skip of existing files

## Requirements

- Python 3.10+
- Canvas API access token
- Network access to your Canvas instance

## Dependencies

- `beautifulsoup4` - HTML parsing for page/assignment/discussion content
- `requests` - HTTP client (used directly against the Canvas REST API)
- `pyyaml` - Configuration file parsing

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License - see LICENSE file for details

## Inspiration

This project was inspired by [canvas-student-data-export](https://github.com/davekats/canvas-student-data-export)
