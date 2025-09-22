# ActiGraph S3 Uploader

A GUI application for uploading ActiGraph files to AWS S3 with subject name mapping functionality and automatic update capabilities.

## Features

- 📁 Select and scan folders containing ActiGraph files (.gt3x)
- 🤖 Automatic subject name extraction from files
- ☁️ AWS S3 integration with configurable credentials
- 🔗 Subject name mapping for new subjects
- 📈 Progress tracking and detailed upload logs
- ⚡ Background upload processing
- 🔄 **Auto-update functionality** - Automatically checks for and downloads new versions
- 🖥️ Cross-platform support (Windows & macOS)
- 📊 Enhanced logging with session tracking

## Quick Start (Executable)

### Download Pre-built Executable

1. Go to the [Releases](https://github.com/SujithChristopher/actigraph_upload/releases) page
2. Download the latest version for your operating system:
   - Windows: `ActiGraphUploader-Windows.zip`
   - macOS: `ActiGraphUploader-macOS.zip`
3. Extract the zip file and run the executable
4. The application will automatically check for updates on startup

### System Requirements
- Windows 10+ or macOS 10.14+
- Internet connection for S3 uploads and auto-updates

## Development Setup

### From Source

1. Clone the repository:
```bash
git clone <repository-url>
cd actigraph_upload
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. AWS credentials are pre-configured in the distributed executable

5. Run the application:
```bash
python main.py
```

### Building Executable

To build your own executable:

```bash
python build.py
```

The executable will be created in the `dist/` folder.

## Usage

1. **Launch the application** (executable or `python main.py`)
2. **Configure AWS** (first time): Go to Settings → AWS Configuration to enter your credentials
3. **Select folder**: Click "Browse Folder" to select a folder containing ActiGraph files
4. **Check subject mapping**: If new subjects are detected, map them to existing S3 folders
5. **Start upload**: Click "Start Upload" to begin the upload process
6. **Monitor progress**: Watch the progress bar and detailed logs
7. **Auto-updates**: The application will check for updates automatically and prompt you to download new versions

### Menu Options

- **Settings → AWS Configuration**: Configure your AWS S3 credentials and settings
- **Help → Check for Updates**: Manually check for application updates
- **Help → About**: View version information and application details

## File Organization

Uploaded files are organized in S3 with the following structure:
```
{BASE_FOLDER}/{subject_name}/{device_name}/{Left|Right}/{filename}
```

## Auto-Update Feature

The application includes a robust auto-update system:

- ✅ **Automatic checking**: Checks for updates on startup (non-intrusive)
- ✅ **Manual checking**: Via Help menu → Check for Updates
- ✅ **Smart downloads**: Downloads the correct version for your operating system
- ✅ **Safe installation**: Backs up current version before updating
- ✅ **Seamless restart**: Automatically restarts with the new version

## Requirements

### Runtime Requirements
- Python 3.8+ (for source code)
- Internet connection for uploads and auto-updates

### Dependencies
- PySide6>=6.5.0
- boto3>=1.26.0
- python-dotenv>=1.0.0
- requests>=2.28.0
- packaging>=21.0

### Build Dependencies (for development)
- pyinstaller>=5.10.0

## License

MIT License 