"""
EJEMPLOS DE USO Y CASOS DE PRUEBA

Este archivo contiene ejemplos prácticos de cómo ejecutar el script de migración
ETL y cómo verificar los resultados.
"""

# ============================================================================
# EJEMPLO 1: Ejecución básica con variables de entorno
# ============================================================================

"""
# En terminal:

# Paso 1: Configurar variables de entorno
export SOURCE_DB_URL="postgresql://postgres:password@localhost:5432/source_db"
export DESTINATION_DB_URL="postgresql://postgres:password@localhost:5433/dest_db"

# Paso 2: Ejecutar el script
cd /Users/diegoferrufino/Documents/Datax/Software/DATAXDBSAVIOR
python migration_etl.py

# Salida esperada:
# 2024-01-15 10:30:00 - INFO - 🚀 INICIANDO MIGRACIÓN ETL...
# 2024-01-15 10:30:01 - INFO - ✓ Conexión ORIGEN exitosa
# 2024-01-15 10:30:02 - INFO - ✓ Conexión DESTINO exitosa
# 2024-01-15 10:30:05 - INFO - PASO 2: EXTRACCIÓN DE DATOS
# ... (continúa con todos los pasos)
# 2024-01-15 10:35:42 - INFO - ✓ MIGRACIÓN COMPLETADA EXITOSAMENTE
"""

# ============================================================================
# EJEMPLO 2: Ejecución con script wrapper (run_migration.sh)
# ============================================================================

"""
# Paso 1: Hacer ejecutable el script
chmod +x run_migration.sh

# Paso 2: Ejecutar
./run_migration.sh

# El script te pedirá confirmación interactiva antes de ejecutar
# Presiona 's' para continuar o 'n' para cancelar
"""

# ============================================================================
# EJEMPLO 3: Ejecución con archivo .env
# ============================================================================

"""
# Paso 1: Crear archivo .env
cat > .env << 'EOF'
SOURCE_DB_URL=postgresql://postgres:password@localhost:5432/source_db
DESTINATION_DB_URL=postgresql://postgres:password@localhost:5433/dest_db
EOF

# Paso 2: Instalar python-dotenv
pip install python-dotenv

# Paso 3: Modificar el script para cargar .env (opcional)
# Añadir al inicio de migration_etl.py:
# from dotenv import load_dotenv
# load_dotenv()

# Paso 4: Ejecutar
python migration_etl.py
"""

# ============================================================================
# EJEMPLO 4: Ejecución en una línea
# ============================================================================

"""
SOURCE_DB_URL="postgresql://postgres:pw@localhost:5432/db" \\
DESTINATION_DB_URL="postgresql://postgres:pw@localhost:5433/db" \\
python migration_etl.py
"""

# ============================================================================
# EJEMPLO 5: Monitoreo de logs en tiempo real
# ============================================================================

"""
# En una terminal
python migration_etl.py

# En otra terminal, monitorear logs
tail -f migration_*.log

# O con menos (paginador)
less +F migration_*.log
"""

# ============================================================================
# QUERIES DE VERIFICACIÓN POST-MIGRACIÓN
# ============================================================================

"""
NOTA: Ejecutar estas queries en PostgreSQL 18 (destino) para validar

1. Contar registros migrados:
   ─────────────────────────────
   SELECT 
       (SELECT COUNT(*) FROM source) as source_count,
       (SELECT COUNT(*) FROM file) as file_count,
       (SELECT COUNT(*) FROM report) as report_count;
   
   Resultado esperado:
   source_count | file_count | report_count
   ─────────────┼────────────┼──────────────
          1500 |       3200 |         4100

2. Verificar integridad de FK en file:
   ───────────────────────────────────
   SELECT COUNT(*) as invalid_references
   FROM file f
   LEFT JOIN source s ON f.idsource = s.id
   WHERE s.id IS NULL;
   
   Resultado esperado: 0 (sin referencias inválidas)

3. Verificar integridad de FK en report:
   ────────────────────────────────────
   SELECT COUNT(*) as invalid_references
   FROM report r
   LEFT JOIN file f ON r.id_file = f.id
   WHERE r.id_file IS NOT NULL AND f.id IS NULL;
   
   Resultado esperado: 0 (sin referencias inválidas)

4. Verificar mapeo de códigos en report:
   ────────────────────────────────────
   -- Este query verifica que los códigos se mapearon correctamente
   SELECT 
       r.code as report_code,
       REGEXP_REPLACE(r.code, '_[0-9]+$', '') as extracted_code,
       f.code as file_code,
       r.id_file as mapped_id_file,
       f.id as actual_id_file,
       CASE 
           WHEN f.id = r.id_file THEN '✓ CORRECTO'
           ELSE '✗ ERROR'
       END as status
   FROM report r
   LEFT JOIN file f ON REGEXP_REPLACE(r.code, '_[0-9]+$', '') = f.code
   ORDER BY r.id
   LIMIT 10;
   
   Resultado esperado: Todos los status deben ser '✓ CORRECTO'

5. Resumen de actualización de report:
   ────────────────────────────────────
   SELECT 
       COUNT(*) as total_records,
       COUNT(id_file) as with_mapping,
       COUNT(CASE WHEN id_file IS NULL THEN 1 END) as without_mapping
   FROM report;
   
   Resultado esperado: 
   - total_records > 0
   - with_mapping > 0
   - without_mapping ≈ 0 (o muy bajo si hay reportes sin archivo)

6. Ejemplo de datos específicos:
   ──────────────────────────────
   SELECT 
       s.id as source_id,
       s.name as source_name,
       f.id as file_id,
       f.code as file_code,
       f.idsource as file_idsource,
       r.id as report_id,
       r.code as report_code,
       r.id_file as report_id_file
   FROM source s
   LEFT JOIN file f ON f.idsource = s.id
   LEFT JOIN report r ON r.id_file = f.id
   WHERE s.id = 1  -- Cambiar el 1 por un ID real
   LIMIT 5;
"""

# ============================================================================
# SCRIPT DE VALIDACIÓN COMPLETA (SQL)
# ============================================================================

"""
-- Ejecutar en PostgreSQL 18 (destino)
-- Este script realiza validación completa

BEGIN;

-- 1. Conteos
DO $$ 
DECLARE
    v_source_count INT;
    v_file_count INT;
    v_report_count INT;
    v_invalid_file_fk INT;
    v_invalid_report_fk INT;
    v_unmapped_report INT;
BEGIN
    SELECT COUNT(*) INTO v_source_count FROM source;
    SELECT COUNT(*) INTO v_file_count FROM file;
    SELECT COUNT(*) INTO v_report_count FROM report;
    
    -- FK validation
    SELECT COUNT(*) INTO v_invalid_file_fk
    FROM file f
    LEFT JOIN source s ON f.idsource = s.id
    WHERE s.id IS NULL;
    
    SELECT COUNT(*) INTO v_invalid_report_fk
    FROM report r
    LEFT JOIN file f ON r.id_file = f.id
    WHERE r.id_file IS NOT NULL AND f.id IS NULL;
    
    SELECT COUNT(*) INTO v_unmapped_report
    FROM report WHERE id_file IS NULL;
    
    RAISE NOTICE '═══════════════════════════════════════════════';
    RAISE NOTICE 'VALIDACIÓN POST-MIGRACIÓN';
    RAISE NOTICE '═══════════════════════════════════════════════';
    RAISE NOTICE 'source registros: %', v_source_count;
    RAISE NOTICE 'file registros: %', v_file_count;
    RAISE NOTICE 'report registros: %', v_report_count;
    RAISE NOTICE '';
    RAISE NOTICE 'INTEGRIDAD DE FK:';
    RAISE NOTICE 'invalid file.idsource: %', v_invalid_file_fk;
    RAISE NOTICE 'invalid report.id_file: %', v_invalid_report_fk;
    RAISE NOTICE 'report sin mapeo: %', v_unmapped_report;
    RAISE NOTICE '═══════════════════════════════════════════════';
    
    IF v_invalid_file_fk > 0 THEN
        RAISE WARNING 'ALERTA: Hay referencias inválidas en file.idsource';
    END IF;
    
    IF v_invalid_report_fk > 0 THEN
        RAISE WARNING 'ALERTA: Hay referencias inválidas en report.id_file';
    END IF;
    
    RAISE NOTICE 'VALIDACIÓN COMPLETADA';
END $$;

ROLLBACK;
"""

# ============================================================================
# CASOS DE PRUEBA UNITARIOS
# ============================================================================

"""
Para verificar que el script funciona correctamente, puedes crear
tablas de prueba y ejecutar el script en ellas.

-- Crear tablas de prueba en origin
CREATE TABLE source_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT
);

CREATE TABLE file_test (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50),
    idsource INT REFERENCES source_test(id),
    filename VARCHAR(255)
);

-- Insertar datos de prueba
INSERT INTO source_test (name, description) VALUES 
    ('Source 1', 'Description 1'),
    ('Source 2', 'Description 2'),
    ('Source 3', 'Description 3');

INSERT INTO file_test (code, idsource, filename) VALUES 
    ('D_BO_000000001', 1, 'file1.txt'),
    ('D_BO_000000002', 1, 'file2.txt'),
    ('D_BO_000000003', 2, 'file3.txt');

-- Crear tabla report_test en destino
CREATE TABLE report_test (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50),
    id_file INT REFERENCES file_test(id)
);

INSERT INTO report_test (code) VALUES 
    ('D_BO_000000001_01'),
    ('D_BO_000000001_02'),
    ('D_BO_000000002_01'),
    ('D_BO_000000003_99');

-- Luego ejecutar el script y validar los resultados
"""

# ============================================================================
# TROUBLESHOOTING: DIAGNÓSTICO
# ============================================================================

"""
Si algo falla, ejecutar estos diagnosticos:

1. Verificar conexiones:
   ──────────────────────
   # Terminal
   psql "postgresql://user:pass@localhost:5432/db" -c "SELECT version();"
   psql "postgresql://user:pass@localhost:5433/db" -c "SELECT version();"

2. Verificar tablas en origen:
   ──────────────────────────
   psql "postgresql://user:pass@localhost:5432/db" -c "\\dt"

3. Verificar estructuras de tablas:
   ───────────────────────────────
   psql "postgresql://user:pass@localhost:5432/db" -c "\\d source"
   psql "postgresql://user:pass@localhost:5432/db" -c "\\d file"

4. Verificar logs:
   ────────────────
   # Terminal en carpeta del script
   tail -100 migration_*.log
   
5. Comprobar que Truncate funcionó:
   ────────────────────────────────
   psql "postgresql://user:pass@localhost:5433/db" -c "SELECT COUNT(*) FROM source;"
   # Debe devolver 0 antes de iniciar la migración

6. Ver el mapeo de IDs (si el script lo publica):
   ──────────────────────────────────────────────
   # Buscar en los logs líneas con "Mapeo"
   grep "Mapeo" migration_*.log
"""

# ============================================================================
# NOTAS Y CONSIDERACIONES
# ============================================================================

"""
IMPORTANTE:

1. TRUNCATE CASCADE
   - El comando TRUNCATE TABLE file CASCADE también truncará report si tiene FK
   - Eso es por qué el script setea id_file a NULL en report antes
   - O puedes revisar el orden de truncate si es necesario

2. Mapeo de IDs
   - El diccionario se crea en PASO 4 y se usa en PASO 5
   - Si falla PASO 4, PASO 5 fallará también
   - El mapeo es esencial para mantener la integridad

3. Códigos de Report
   - El script asume que report.code tiene formato: "BASE_CODE_SUFFIX"
   - El SUFFIX es siempre _[0-9]+ (guión bajo + números)
   - Si tienes formatos diferentes, modificar REGEXP_REPLACE

4. Rendimiento
   - Para tablas grandes (>100K registros), el script puede tardar
   - El PASO 4 (iterativo) es el más lento
   - Considera optimizar con INSERT ... SELECT si la FK lo permite

5. Rollback
   - Si necesitas volver atrás, tener backup de destino
   - El script actual no soporta rollback
   - Ejecutar en horario de bajo tráfico
"""
