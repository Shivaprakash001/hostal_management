#!/usr/bin/env python3
"""
Build script to prepare frontend files for Netlify deployment.
This script copies static files and templates to the dist directory.
"""

import os
import shutil
from pathlib import Path

def build_frontend():
    """Build frontend files for deployment."""

    # Create dist directory
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Copy static files
    static_src = Path("static")
    static_dst = dist_dir / "static"
    if static_src.exists():
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"✓ Copied static files to {static_dst}")

    # Copy templates
    templates_src = Path("templates")
    templates_dst = dist_dir / "templates"
    if templates_src.exists():
        if templates_dst.exists():
            shutil.rmtree(templates_dst)
        shutil.copytree(templates_src, templates_dst)
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
    <script>
        // Redirect to backend for initial page load
        window.location.href = '/';
    </script>
</head>
<body>
    <p>Loading Hostel Management System...</p>
</body>
</html>""")

    print(f"✓ Created index.html in {dist_dir}")
    print("✓ Frontend build complete!")

if __name__ == "__main__":
    build_frontend()
