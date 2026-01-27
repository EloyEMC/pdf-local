#!/usr/bin/env python3
"""Script de diagnóstico para problemas del frontend."""

import sys
import os

# Añadir el directorio app al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("DIAGNÓSTICO - PDF to BC3")
print("="*60)

# 1. Verificar imports
print("\n1. Verificando imports...")
try:
    from flask import Flask
    print("   ✅ Flask importado correctamente")
except ImportError as e:
    print(f"   ❌ Error importando Flask: {e}")
    sys.exit(1)

try:
    from app.main import app
    print("   ✅ App importada correctamente")
except Exception as e:
    print(f"   ❌ Error importando app: {e}")
    sys.exit(1)

# 2. Verificar template
print("\n2. Verificando template...")
template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'index.html')
if os.path.exists(template_path):
    print(f"   ✅ Template encontrado: {template_path}")
    with open(template_path, 'r') as f:
        content = f.read()
        print(f"   - Tamaño: {len(content)} bytes")
        print(f"   - Contiene '<!DOCTYPE html>': {'<!DOCTYPE html>' in content}")
        print(f"   - Contiene '<h1>PDF to BC3</h1>': {'<h1>PDF to BC3</h1>' in content}")
        print(f"   - Contiene CSS inline: {'<style>' in content}")
else:
    print(f"   ❌ Template NO encontrado: {template_path}")

# 3. Verificar respuesta del servidor
print("\n3. Verificando respuesta del servidor...")
with app.test_client() as client:
    # Test route /
    response = client.get('/')
    print(f"   - Status code: {response.status_code}")
    print(f"   - Content length: {len(response.data)} bytes")

    content = response.data.decode('utf-8')
    print(f"   - Contiene 'PDF to BC3': {'PDF to BC3' in content}")
    print(f"   - Contiene '<form': {'<form' in content}")
    print(f"   - Contiene CSS: {'<style>' in content}")

    # Test route /test
    test_response = client.get('/test')
    print(f"\n   Route /test - Status: {test_response.status_code}")

# 4. Verificar directorios
print("\n4. Verificando directorios...")
for dir_name in ['uploads', 'outputs', 'app/templates', 'app/static']:
    path = os.path.join(os.path.dirname(__file__), dir_name)
    if os.path.exists(path):
        print(f"   ✅ {dir_name}/ existe")
    else:
        print(f"   ❌ {dir_name}/ NO existe")

print("\n" + "="*60)
print("DIAGNÓSTICO COMPLETADO")
print("="*60)
print("\nSi todo está en ✅, el problema es del navegador.")
print("\nPasos a seguir:")
print("1. Abre http://localhost:5000/test en tu navegador")
print("2. Si /test se ve bien, el problema es en index.html")
print("3. Abre la consola del navegador (F12) y busca errores")
print("4. Haz Ctrl+F5 (o Cmd+Shift+R) para recargar sin caché")
print("="*60)
