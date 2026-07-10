#!/usr/bin/env python3
"""Test API pour la signature avec logo"""
import subprocess
import json
from pathlib import Path

# Tester avec curl plutôt que Python
test_img = Path('backend/test_images/sample_01.jpg')
logo_path = Path('frontend/public/logo.png')

if not test_img.exists():
    print(f'❌ Image de test non trouvée: {test_img}')
    exit(1)

print("=" * 70)
print("TEST 1 : Optimisation simple (baseline)")
print("=" * 70)
cmd = [
    'curl', '-X', 'POST',
    'http://localhost:8000/api/optimize',
    '-F', f'files=@{test_img}',
    '-F', 'format=webp',
    '-F', 'quality=75',
    '-F', 'prefix=test',
    '-F', 'watermark_enabled=false',
    '-v'
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stderr)
print(result.stdout)

print("\n" + "=" * 70)
print("TEST 2 : Avec signature texte")
print("=" * 70)
cmd = [
    'curl', '-X', 'POST',
    'http://localhost:8000/api/optimize',
    '-F', f'files=@{test_img}',
    '-F', 'format=webp',
    '-F', 'quality=75',
    '-F', 'prefix=test',
    '-F', 'watermark_enabled=true',
    '-F', 'watermark_type=text',
    '-F', 'watermark_text=ImgOpt 2026',
    '-F', 'watermark_position=bottom-right',
    '-F', 'watermark_opacity=50',
    '-v'
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stderr)
print(result.stdout)

if logo_path.exists():
    print("\n" + "=" * 70)
    print("TEST 3 : Avec logo")
    print("=" * 70)
    cmd = [
        'curl', '-X', 'POST',
        'http://localhost:8000/api/optimize',
        '-F', f'files=@{test_img}',
        '-F', f'watermark_logo=@{logo_path}',
        '-F', 'format=webp',
        '-F', 'quality=75',
        '-F', 'prefix=test',
        '-F', 'watermark_enabled=true',
        '-F', 'watermark_type=image',
        '-F', 'watermark_position=bottom-right',
        '-F', 'watermark_opacity=70',
        '-v'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stderr)
    print(result.stdout)
else:
    print(f"\n❌ Logo non trouvé: {logo_path}")
