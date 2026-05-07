# 🚀 Script de Migración ETL: PostgreSQL 9 → PostgreSQL 18

Script profesional de migración ETL en Python para migrar datos de PostgreSQL 9 a PostgreSQL 18, manteniendo integridad de relaciones y mapeo de claves foráneas.

## 📋 Tabla de Contenidos

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Flujo de Migración](#flujo-de-migración)
- [Pasos Críticos](#pasos-críticos)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos

- Python 3.8+
- PostgreSQL 9 (origen)
- PostgreSQL 18 (destino)
- pip (gestor de paquetes Python)

## 📦 Instalación

### 1. Crear un entorno virtual (recomendado)

```bash
cd /Users/diegoferrufino/Documents/Datax/Software/DATAXDBSAVIOR
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o en Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- **pandas**: Manipulación y análisis de datos
- **sqlalchemy**: ORM y toolkit SQL
- **psycopg2-binary**: Driver PostgreSQL para Python

---

## ⚙️ Configuración

### Variables de Entorno desde Archivo `.env`

El script carga las variables de entorno automáticamente desde un archivo `.env`:

#### 1. Crear archivo `.env` desde la plantilla

```bash
cd /Users/diegoferrufino/Documents/Datax/Software/DATAXDBSAVIOR
cp .env.example .env
```

#### 2. Editar el archivo `.env` con tus credenciales

```bash
# Editar .env con tu editor favorito
nano .env
# o
code .env
```

#### 3. Configurar las URLs

```ini
# Base de Datos ORIGEN (PostgreSQL 9)
SOURCE_DB_URL=postgresql://usuario:contraseña@localhost:5432/base_origen

# Base de Datos DESTINO (PostgreSQL 18)
DESTINATION_DB_URL=postgresql://usuario:contraseña@localhost:5433/base_destino
```

⚠️ **IMPORTANTE:** El archivo `.env` contiene credenciales sensibles y **NO debe ser commiteado a git**. Ya está añadido a `.gitignore` automáticamente.

### Estructura de la URL de Conexión

```
postgresql://usuario:contraseña@host:puerto/nombre_base_datos
```

**Componentes:**
- `usuario`: Usuario de PostgreSQL
- `contraseña`: Contraseña del usuario (si tiene caracteres especiales, usar URL-encoding: @ → %40, : → %3A)
- `host`: Dirección IP o hostname (localhost, 127.0.0.1, etc.)
- `puerto`: Puerto de PostgreSQL (por defecto 5432)
- `nombre_base_datos`: Nombre de la base de datos

### Ejemplos de Archivo `.env`

**Ejemplo 1: Conexiones Locales**
```ini
SOURCE_DB_URL=postgresql://postgres:pass123@localhost:5432/datax_old
DESTINATION_DB_URL=postgresql://postgres:pass123@localhost:5433/datax_new
```

**Ejemplo 2: Conexiones Remotas**
```ini
SOURCE_DB_URL=postgresql://dbuser:secure_pwd@192.168.1.100:5432/production_db
DESTINATION_DB_URL=postgresql://dbuser:secure_pwd@migration.example.com:5432/staging_db
```

**Ejemplo 3: Con caracteres especiales en contraseña**
```ini
# @ en contraseña → %40
# : en contraseña → %3A
# # en contraseña → %23
SOURCE_DB_URL=postgresql://user:pass%40word@localhost:5432/db
DESTINATION_DB_URL=postgresql://user:pass%40word@localhost:5433/db
```

---

## 🏃 Ejecución

### Opción 1: Ejecución Simple (Recomendado)

```bash
# Asegúrate de tener .env configurado en el directorio actual
python migration_etl.py
```

El script cargará automáticamente las variables desde el archivo `.env`.

### Opción 2: Usar el script bash wrapper

```bash
# Hacer ejecutable
chmod +x run_migration.sh

# Ejecutar (pide confirmación interactiva)
./run_migration.sh
```

### Opción 3: Crear entorno virtual (Best Practice)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar el entorno
source venv/bin/activate  # macOS/Linux
# o en Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar y configurar .env
cp .env.example .env
nano .env  # Editar con tus credenciales

# Ejecutar
python migration_etl.py
```

---

## 🔄 Flujo de Migración

El script ejecuta 6 pasos secuenciales:

```
┌─────────────────────────────────────────────────────────────┐
│           FLUJO COMPLETO DE MIGRACIÓN ETL                   │
└─────────────────────────────────────────────────────────────┘

PASO 1: CONEXIÓN DUAL
├─ Crea engine SQLAlchemy para PostgreSQL 9 (origen)
├─ Crea engine SQLAlchemy para PostgreSQL 18 (destino)
└─ Valida que ambas conexiones funcionan ✓

PASO 2: EXTRACCIÓN (ORIGEN)
├─ Lee tabla 'source' → DataFrame
├─ Lee tabla 'file' → DataFrame
└─ Almacena en memoria ✓

PASO 3: LIMPIEZA (DESTINO)
├─ TRUNCATE TABLE file CASCADE
├─ TRUNCATE TABLE source CASCADE
└─ Borra todos los datos previos ✓

┌─────────────────────────────────────────────────────────────┐
│  PASO 4: INSERCIÓN Y MAPEO DE SOURCE (🔥 CRÍTICO)          │
├─ Para cada fila en df_source:                              │
│   ├─ INSERT INTO source (...) RETURNING id                 │
│   ├─ Captura nuevo_id autogenerado                         │
│   ├─ Crea mapeo: {id_origen: id_destino}                   │
│   └─ Itera hasta completar todos los registros             │
├─ Resultado: Diccionario con todos los mapeos               │
└─ Ejemplo: {1: 1001, 2: 1002, 3: 1003}                      │
└─ ✓

PASO 5: MAPEO E INSERCIÓN DE FILE
├─ Reemplaza column 'idsource' en df_file usando id_mapping
├─ Transforma IDs: {idsource_antiguo → idsource_nuevo}
├─ INSERT INTO file (...) con IDs actualizados
└─ ✓

┌─────────────────────────────────────────────────────────────┐
│  PASO 6: ACTUALIZACIÓN DE REPORT (🔥 CRÍTICO - SQL PURO)   │
├─ Para cada registro en report:                             │
│   ├─ Extrae código base: "D_BO_000000016_01" → remover "_01"
│   ├─ Busca en file por código coincidente                  │
│   ├─ Obtiene el id_file correcto                           │
│   └─ UPDATE report.id_file = file.id                       │
├─ Query: UPDATE ... FROM file WHERE REGEXP_REPLACE(...)     │
└─ ✓

RESULTADO FINAL
└─ Todas las tablas migradas con integridad de relaciones
```

---

## 🔥 Pasos Críticos

### PASO 4: Inserción y Mapeo de SOURCE

**¿Por qué es crítico?**
- Los IDs en origin y destino serán DIFERENTES
- source es la tabla padre
- file depende de source (FK)
- Debemos capturar el mapeo nuevo → antiguo para actualizar file

**Cómo funciona:**
1. Extraemos cada fila de source
2. Hacemos INSERT sin especificar 'id' (autogenerado)
3. Usamos RETURNING id para obtener el nuevo ID
4. Creamos diccionario: `{id_origen: id_destino_nuevo}`

**Ejemplo:**
```python
# Origen tenía:
# id=1, name='Source1'  
# id=2, name='Source2'

# Destino ahora tendrá:
# id=101, name='Source1'  ← autogenerado
# id=102, name='Source2'  ← autogenerado

# Mapeo creado:
# {1: 101, 2: 102}
```

### PASO 6: Actualización de REPORT

**¿Por qué es crítico?**
- report ya existe en destino
- Sus file codes tienen sufijos: "D_BO_000000016_01"
- file codes NO tienen sufijos: "D_BO_000000016"
- Debemos remover el sufijo y hacer join

**Cómo funciona:**
```sql
UPDATE report r
SET id_file = f.id
FROM file f
WHERE REGEXP_REPLACE(r.code, '_[0-9]+$', '') = f.code
  AND (r.id_file IS NULL OR r.id_file != f.id)
```

**Desglose:**
- `REGEXP_REPLACE(r.code, '_[0-9]+$', '')`: Remueve `_XX` del final
  - "D_BO_000000016_01" → "D_BO_000000016"
  - "D_BO_000000016_99" → "D_BO_000000016"
- `= f.code`: Busca coincidencia exacta en file
- `SET id_file = f.id`: Actualiza con el ID correcto

---

## 📊 Logs y Salida

El script genera dos tipos de salida:

### 1. Consola (stdout)
```
2024-01-15 10:23:45,123 - INFO - ✓ Conexión ORIGEN exitosa
2024-01-15 10:23:47,456 - INFO - ✓ Conexión DESTINO exitosa
2024-01-15 10:23:48,789 - INFO - ✓ 1500 registros leídos de 'source'
...
```

### 2. Archivo de Log
`migration_20240115_102345.log`

Se genera automáticamente con timestamp, contiene:
- Todos los mensajes INFO, WARNING, ERROR
- Timestamps de cada operación
- Resumen final de registros procesados

---

## ✅ Verificación Post-Migración

Después de ejecutar el script, verifica la integridad:

### Verificar conteo de registros

```sql
-- Destino
SELECT COUNT(*) as total_source FROM source;
SELECT COUNT(*) as total_file FROM file;
SELECT COUNT(*) as updated_reports FROM report WHERE id_file IS NOT NULL;
```

### Verificar integridad de relaciones

```sql
-- Verificar que todos los file.idsource apuntan a source válido
SELECT COUNT(*) as invalid_fk_file
FROM file f
LEFT JOIN source s ON f.idsource = s.id
WHERE s.id IS NULL;

-- Verificar que todos los report.id_file apuntan a file válido
SELECT COUNT(*) as invalid_fk_report
FROM report r
LEFT JOIN file f ON r.id_file = f.id
WHERE r.id_file IS NOT NULL AND f.id IS NULL;
```

### Verificar mapeo de códigos

```sql
-- Verificar que los códigos reportados coinciden después del mapeo
SELECT r.code, f.code, r.id_file
FROM report r
JOIN file f ON r.id_file = f.id
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'pandas'"

**Solución:**
```bash
pip install pandas sqlalchemy psycopg2-binary
```

### Problema: "FATAL: Ident authentication failed for user 'postgres'"

**Solución:** Verificar credenciales en URL
```bash
# Verifica conexión manual
psql -h localhost -U postgres -d base_datos
```

### Problema: "Cannot locate PostgreSQL installation"

**Solución:** Instalar driver PostgreSQL
```bash
pip install psycopg2-binary
```

### Problema: "ERROR: relation 'source' does not exist"

**Solución:** Verificar que las tablas existen en origen
```sql
-- En PostgreSQL 9 (origen)
SELECT * FROM information_schema.tables WHERE table_name IN ('source', 'file', 'report');
```

### Problema: "Foreign key violation in file"

**Solución:** El mapeo de IDs falló. Verificar:
1. ¿Todos los source fueron insertados? `SELECT COUNT(*) FROM source;`
2. ¿El diccionario de mapeo está completo?
3. ¿Hay source.id duplicados en origen?

### Problema: "deadlock detected"

**Solución:** Reducir concurrencia o ejecutar en horario de bajo tráfico
- El script es secuencial, no paralelo
- Usa un único worker por ejecución
- Ejecuta en horarios de poca carga

---

## 📝 Notas Importantes

1. **Backup:** SIEMPRE hace backup antes de ejecutar TRUNCATE
2. **Transacciones:** El script usa transacciones, pero TRUNCATE es DDL
3. **Monitoreo:** Usa `tail -f migration_*.log` para monitorear en tiempo real
4. **Pausa/Resume:** El script actual no tiene resume. Para tablas muy grandes, considerar chunks
5. **Validación:** Después de migrar, ejecutar queries de verificación

---

## 🎯 Optimizaciones Futuras

- [ ] Migración por lotes (chunks) para tablas muy grandes
- [ ] Soporte para resume si falla a medio camino
- [ ] Paralelización con worker pools
- [ ] Validación automática post-migración
- [ ] Soporte para más tablas dinámicamente

---

## 📞 Soporte

Para issues o dudas:
1. Revisar los logs: `migration_YYYYMMDD_HHMMSS.log`
2. Verificar variables de entorno: `echo $SOURCE_DB_URL`
3. Testear conexiones manualmente con psql
4. Revisar documentación de PostgreSQL 9 vs 18

---

**Creado por:** Data Engineering Team  
**Versión:** 1.0  
**Última actualización:** 2024-01-15
# DB-JoinDBS
