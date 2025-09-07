#!/usr/bin/env python3
"""
Build script to prepare frontend files for Netlify deployment.
This script copies static files and templates to the dist directory.
SECURITY: This script only copies frontend assets and does not include any sensitive files.
"""

import os
import shutil
from pathlib import Path

# List of files/patterns to exclude from build (security)
EXCLUDE_PATTERNS = [
    '.env',
    '.env.local',
    '.env.production',
    '.env.staging',
    '.env.development',
    '*.db',
    '*.sqlite',
    '*.sqlite3',
    'chroma_db/',
    '__pycache__/',
    '.git/',
    '.venv/',
    'venv/',
    'node_modules/',
    '*.log',
    'database/',
    'agent/',
    'utils/',
    'services/',
    'routes/',
    'schemas/',
    'models/',
    'alembic/',
    'tests/',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
    'Thumbs.db'
]

def should_exclude(path):
    """Check if a file/path should be excluded from the build."""
    path_str = str(path)

    # Check exact matches and patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith('/'):
            # Directory pattern
            if pattern.rstrip('/') in path_str:
                return True
        elif pattern.startswith('*'):
            # Wildcard pattern
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            # Exact match
            return True

    return False

def copy_tree_secure(src, dst):
    """Securely copy a directory tree, excluding sensitive files."""
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if should_exclude(item):
            print(f"⚠️  Skipping sensitive file: {item.name}")
            continue

        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            copy_tree_secure(item, dst / item.name)

def build_frontend():
    """Build frontend files for deployment."""

    print("🔒 Starting secure frontend build...")

    # Create dist directory
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # Copy static files securely
    static_src = Path("static")
    static_dst = dist_dir / "static"
    if static_src.exists():
        copy_tree_secure(static_src, static_dst)
        print(f"✓ Copied static files to {static_dst}")

    # Copy templates securely
    templates_src = Path("templates")
    templates_dst = dist_dir / "templates"
    if templates_src.exists():
        copy_tree_secure(templates_src, templates_dst)
        print(f"✓ Copied templates to {templates_dst}")

    # Create a simple index.html for Netlify (will redirect to backend)
    index_html = dist_dir / "index.html"
    with open(index_html, 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hostel Management System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .loading {
            text-align: center;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    <script>
        // Redirect to backend for initial page load
        window.location.href = '/';
    </script>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <h2>Loading Hostel Management System...</h2>
        <p>Please wait while we connect to the server.</p>
    </div>
</body>
</html>""")

    print(f"✓ Created secure index.html in {dist_dir}")
    print("🔒 Frontend build complete! All sensitive files excluded.")

if __name__ == "__main__":
    build_frontend()
