# Guía de Inicio Rápido

## 1. Instalar Ollama

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## 2. Descargar un modelo

```bash
# Modelo recomendado (ligero)
ollama pull llama3.2:3b

# O si prefieres más precisión (requiere más recursos)
ollama pull llama3.2
```

## 3. Verificar que Ollama funciona

```bash
# Ejecutar Ollama (si no está corriendo)
ollama serve

# En otra terminal, probar el modelo
ollama run llama3.2:3b "Hola, ¿quién eres?"
```

## 4. Instalar dependencias Python

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 5. Iniciar la aplicación

```bash
python app/main.py
```

## 6. Usar la aplicación

1. Abre el navegador en `http://localhost:5000`
2. Sube un PDF con una ficha técnica
3. Selecciona el modelo de Ollama a usar
4. Descarga el archivo BC3 generado

---

## Solución de problemas

### Error conectando con Ollama

Asegúrate de que Ollama está ejecutándose:
```bash
ollama serve
```

Verifica que el modelo esté instalado:
```bash
ollama list
```

### Error de memoria

Si el modelo consume demasiada memoria, prueba con el modelo de 3B:
```bash
ollama pull llama3.2:3b
```

### El PDF no se procesa correctamente

- Verifica que el PDF tenga texto extraíble (no solo imágenes)
- Prueba con diferentes modelos de Ollama
- Revisa la consola para ver mensajes de error detallados
