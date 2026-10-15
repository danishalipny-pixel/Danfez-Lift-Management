import glob
import re
import os

html_files = glob.glob('frontend/*.html')
js_files = glob.glob('frontend/assets/js/*.js')

print(f"Total HTML files found: {len(html_files)}")
print(f"Total JS files found: {len(js_files)}")

# Check absolute links
target_prefixes = [
    '/assets/',
    '/dashboard.html',
    '/lifts.html',
    '/simulator.html',
    '/maintenance.html',
    '/alerts.html',
    '/technicians.html',
    '/reports.html',
    '/users.html',
    '/settings.html',
    '/profile.html',
    '/login.html',
    '/register.html',
    '/forgot-password.html',
    '/reset-password.html',
    '/verify-email.html',
    '/offline.html',
    '/manifest.json',
    '/service-worker.js',
    '/index.html'
]

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    count = 0
    for prefix in target_prefixes:
        count += content.count(f'"{prefix}')
        count += content.count(f"'{prefix}")
    if count > 0:
        print(f"{file_path}: {count} absolute references")
