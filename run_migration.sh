#!/bin/bash

################################################################################
# Script de Ejecución: Migration ETL PostgreSQL 9 → PostgreSQL 18
# 
# Este script facilita la ejecución del migration_etl.py con variables de
# entorno preconfiguradas.
#
# Uso:
#   chmod +x run_migration.sh
#   ./run_migration.sh
################################################################################

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║       SCRIPT DE MIGRACIÓN ETL: PostgreSQL 9 → PostgreSQL 18               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# CONFIGURACIÓN DE CREDENCIALES
# ============================================================================
# MODIFICA ESTOS VALORES CON TUS CREDENCIALES REALES

# Base de datos ORIGEN (PostgreSQL 9)
export SOURCE_DB_URL="postgresql://postgres:password@localhost:5432/datax_db"

# Base de datos DESTINO (PostgreSQL 18)
export DESTINATION_DB_URL="postgresql://postgres:password@localhost:5433/datax_db"

# ============================================================================
# VALIDACIÓN PREVIA
# ============================================================================

echo "📋 Validando configuración..."
echo ""

if [ -z "$SOURCE_DB_URL" ]; then
    echo "❌ Error: SOURCE_DB_URL no está configurada"
    exit 1
fi

if [ -z "$DESTINATION_DB_URL" ]; then
    echo "❌ Error: DESTINATION_DB_URL no está configurada"
    exit 1
fi

echo "✓ SOURCE_DB_URL: $SOURCE_DB_URL"
echo "✓ DESTINATION_DB_URL: $DESTINATION_DB_URL"
echo ""

# Verificar que Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 no está instalado"
    exit 1
fi

echo "✓ Python $(python3 --version)"
echo ""

# Verificar que las dependencias están instaladas
echo "📦 Verificando dependencias..."
python3 -c "import pandas; import sqlalchemy; import psycopg2" 2>/dev/null || {
    echo "❌ Error: Las dependencias no están instaladas"
    echo ""
    echo "Para instalar, ejecuta:"
    echo "  pip install -r requirements.txt"
    exit 1
}

echo "✓ pandas, sqlalchemy, psycopg2 instalados"
echo ""

# ============================================================================
# CONFIRMACIÓN PREVIA
# ============================================================================

echo "⚠️  ADVERTENCIA IMPORTANTE:"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Este script ejecutará las siguientes operaciones:"
echo ""
echo "  1. TRUNCATE TABLE file CASCADE en DESTINO"
echo "  2. TRUNCATE TABLE source CASCADE en DESTINO"
echo "  3. Migración de datos desde ORIGEN"
echo "  4. Mapeo de claves foráneas"
echo "  5. Actualización de la tabla report"
echo ""
echo "NOTA: Se ELIMINARÁN todos los datos en las tablas file y source del destino"
echo ""
echo "───────────────────────────────────────────────────────────────────────────"
echo ""

read -p "¿Deseas continuar? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operación cancelada por el usuario."
    exit 1
fi

echo ""

# ============================================================================
# EJECUCIÓN
# ============================================================================

echo "🚀 Iniciando migración..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ejecutar el script Python
if python3 migration_etl.py; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✓ MIGRACIÓN COMPLETADA EXITOSAMENTE"
    echo ""
    echo "📋 Próximos pasos:"
    echo "  1. Revisar el archivo de log: migration_*.log"
    echo "  2. Ejecutar validaciones en la base de datos destino"
    echo "  3. Verificar integridad de relaciones (FK)"
    echo ""
    exit 0
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ ERROR EN LA MIGRACIÓN"
    echo ""
    echo "Revisar el archivo de log para más detalles:"
    echo "  tail -f migration_*.log"
    echo ""
    exit 1
fi
