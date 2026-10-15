import glob
import re

replacements = [
    (r'\"/assets/', '\"assets/'),
    (r'\'/assets/', '\'assets/'),
    (r'\"/dashboard\.html\"', '\"dashboard.html\"'),
    (r'\'/dashboard\.html\'', '\'dashboard.html\''),
    (r'\"/lifts\.html\"', '\"lifts.html\"'),
    (r'\'/lifts\.html\'', '\'lifts.html\''),
    (r'\"/simulator\.html\?', '\"simulator.html\?'),
    (r'\'/simulator\.html\?', '\'simulator.html\?'),
    (r'\"/simulator\.html\"', '\"simulator.html\"'),
    (r'\'/simulator\.html\'', '\'simulator.html\''),
    (r'\"/maintenance\.html\"', '\"maintenance.html\"'),
    (r'\'/maintenance\.html\'', '\'maintenance.html\''),
    (r'\"/alerts\.html\"', '\"alerts.html\"'),
    (r'\'/alerts\.html\'', '\'alerts.html\''),
    (r'\"/technicians\.html\"', '\"technicians.html\"'),
    (r'\'/technicians\.html\'', '\'technicians.html\''),
    (r'\"/reports\.html\"', '\"reports.html\"'),
    (r'\'/reports\.html\'', '\'reports.html\''),
    (r'\"/users\.html\"', '\"users.html\"'),
    (r'\'/users\.html\'', '\'users.html\''),
    (r'\"/settings\.html\"', '\"settings.html\"'),
    (r'\'/settings\.html\'', '\'settings.html\''),
    (r'\"/profile\.html\"', '\"profile.html\"'),
    (r'\'/profile\.html\'', '\'profile.html\''),
    (r'\"/login\.html\"', '\"login.html\"'),
    (r'\'/login\.html\'', '\'login.html\''),
    (r'\"/register\.html\"', '\"register.html\"'),
    (r'\'/register\.html\'', '\'register.html\''),
    (r'\"/forgot-password\.html\"', '\"forgot-password.html\"'),
    (r'\'/forgot-password\.html\'', '\'forgot-password.html\''),
    (r'\"/reset-password\.html\"', '\"reset-password.html\"'),
    (r'\'/reset-password\.html\'', '\'reset-password.html\''),
    (r'\"/verify-email\.html\"', '\"verify-email.html\"'),
    (r'\'/verify-email\.html\'', '\'verify-email.html\''),
    (r'\"/offline\.html\"', '\"offline.html\"'),
    (r'\'/offline\.html\'', '\'offline.html\''),
    (r'\"/manifest\.json\"', '\"manifest.json\"'),
    (r'\'/manifest\.json\'', '\'manifest.json\''),
    (r'\"/service-worker\.js', '\"service-worker.js'),
    (r'\'/service-worker\.js', '\'service-worker.js'),
    (r'\"/index\.html\"', '\"index.html\"'),
    (r'\'/index\.html\'', '\'index.html\'')
]

files = glob.glob('frontend/*.html') + glob.glob('frontend/assets/js/*.js')
for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)
    if content != orig:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {file_path}')
