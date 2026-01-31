#!/bin/bash
# Monitor de progreso - VERSIÓN SIMPLIFICADA Y ROBUSTA

export LC_ALL=C
export LANG=C

OUTPUT_DIR="$HOME/Documents/processed_json"
TOTAL_PDFS=5286

last_count=0
last_time=$(date +%s)

while true; do
    clear
    printf "\033[3J"
    
    # Contador de JSONs
    total=$(find "$OUTPUT_DIR" -name "*.json" -type f ! -name "._*" 2>/dev/null | wc -l | tr -d ' ')
    success=$(grep -l '"success": true' "$OUTPUT_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')
    failed=$((total - success))

    # Progreso
    progress=$(awk "BEGIN {printf \"%.2f\", $total * 100.0 / $TOTAL_PDFS}")

    # Calcular velocidad
    current_time=$(date +%s)
    time_diff=$((current_time - last_time))
    count_diff=$((total - last_count))

    if [ "$time_diff" -gt 0 ] && [ "$count_diff" -ge 0 ]; then
        speed=$(awk "BEGIN {printf \"%.2f\", $count_diff / $time_diff}")
    else
        speed="0.00"
    fi

    last_count=$total
    last_time=$current_time

    # Tiempo restante
    speed_val=$(awk "BEGIN {print $speed}")
    if awk "BEGIN {exit !($speed_val > 0.01)}"; then
        remaining=$(awk "BEGIN {printf \"%.0f\", ($TOTAL_PDFS - $total) / $speed_val}")
        hours=$((remaining / 3600))
        minutes=$(((remaining % 3600) / 60))
        time_remaining="${hours}h ${minutes}m"
    else
        time_remaining="Calculando..."
    fi

    # Proceso activo
    process_running=$(ps aux | grep "process_to_json.py" | grep -v grep | wc -l | tr -d ' ')

    # Último archivo
    last_file=$(find "$OUTPUT_DIR" -name "*.json" -type f ! -name "._*" -exec ls -lt {} + 2>/dev/null | head -1 | awk '{print $NF}')
    if [ -n "$last_file" ]; then
        last_time_str=$(stat -f "%Sm" -t "%H:%M:%S" "$last_file" 2>/dev/null)
        last_name=$(basename "$last_file")
    else
        last_time_str="N/A"
        last_name="N/A"
    fi

    # Header
    printf "\n"
    printf "════════════════════════════════════════════════════════════════\n"
    printf "      🔄 MONITOR DE PROCESAMIENTO DE PDFs                       \n"
    printf "════════════════════════════════════════════════════════════════\n"
    printf "\n"

    # Progreso
    printf "📊 PROGRESO GENERAL\n"
    printf "┌──────────────────────────────────────────────────────────┐\n"
    printf "│ Progreso: %6.2f%% (%5d/%5d PDFs)                    │\n" "$progress" "$total" "$TOTAL_PDFS"
    printf "├──────────────────────────────────────────────────────────┤\n"
    printf "│ ✅ Exitosos: %5d   ❌ Errores: %5d                    │\n" "$success" "$failed"
    printf "└──────────────────────────────────────────────────────────┘\n"
    printf "\n"

    # Velocidad
    printf "⚡ RENDIMIENTO\n"
    printf "┌──────────────────────────────────────────────────────────┐\n"
    printf "│ Velocidad actual: %6s PDFs/minuto                    │\n" "$speed"
    printf "│ Tiempo restante: %-20s                       │\n" "$time_remaining"
    if [ "$process_running" -gt 0 ]; then
        printf "│ Proceso activo: Sí ✅                                      │\n"
    else
        printf "│ Proceso activo: No ❌                                      │\n"
    fi
    printf "└──────────────────────────────────────────────────────────┘\n"
    printf "\n"

    # Última actividad
    printf "🕐 ÚLTIMA ACTIVIDAD\n"
    printf "┌──────────────────────────────────────────────────────────┐\n"
    printf "│ Archivo: %-50s│\n" "$last_name"
    printf "│ Hora: %-20s                               │\n" "$last_time_str"
    printf "└──────────────────────────────────────────────────────────┘\n"
    printf "\n"

    # Advertencia si está bloqueado
    if [ "$process_running" -eq 0 ]; then
        printf "⚠️  ADVERTENCIA: El proceso NO está corriendo\n"
        printf "\n"
    fi

    # Timestamp
    printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    printf "Actualizado: $(date '+%H:%M:%S') | Refrescando cada 30 segundos\n"
    printf "Presiona Ctrl+C para salir\n"
    printf "\n"

    sleep 30
done
