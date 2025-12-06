# Document Vault 🛡️

**"I hate resizing documents for different government portals every single time, so I built this."**

A secure, local **Document Vault** that automates the boring task of formatting files for Indian government services. Upload your master documents once, click a portal (Passport, Aadhaar, NCS, etc.), and instantly get compliant versions in the exact size, format, and dimensions required.

## 🚀 Features
- **Zero-Effort Compliance**: Auto-generates files for **Passport** (51x51mm), **PAN** (3.5x2.5cm), **Aadhaar**, **NCS**, and 20+ others.
- **Document Vault**: Securely store high-quality master copies of your Photo, Signature, Resume, etc. locally.
- **Premium UI**: Immersive **Glassmorphism** design with "Scanner" and "Aurora" animations.
- **Tools**:
    - **Resume Support**: Integrated CV management for job portals.
    - **Custom Generator**: Ad-hoc tool to resize any file to any spec (e.g., "Make this PDF under 2MB").
- **Privacy First**: All processing happens locally in `user_data/`. No data leaves your machine.

## Installation

We recommend using **uv** for ultra-fast package management.

1.  **Install uv** (if not installed):
    ```bash
    # Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Create & Activate Virtual Environment**:
    ```bash
    uv venv
    
    # Windows
    .venv\Scripts\activate
    
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    uv pip install -r requirements.txt
    ```

## Usage

### Web UI (Recommended)
Launch the Vault interface:
```bash
streamlit run webapp/app.py
```
1. Go to **My Documents** tab and upload your master files.
2. Go to **Portals** tab, select a service, and click **Generate**.

### CLI
Compress a single file manually:
```bash
# Syntax: python -m compressor.compress_any <input> <output_folder> <target_size> [target_dims]
python -m compressor.compress_any my_photo.jpg ./output 50kb 3.5x4.5cm
```

### Kiro Hook
Auto-compress files dropped in `incoming/`:
```yaml
hooks:
  - name: "auto-compress"
    trigger: { type: "fs_watch", path: "./incoming", events: ["create"] }
    action: { type: "run_command", command: "python -m compressor.compress_any {file_path} ./compressed_output 100kb" }
```

## Supported Portals
- **Aadhaar**: 3.5x4.5cm Photo, PDF Docs
- **PAN (NSDL)**: 3.5x2.5cm Photo, 4.5x2cm Signature
- **Passport**: 51x51mm Photo
- **NEET/JEE**: Postcard photos, Thumb impressions
- And many more...

## License
MIT License
