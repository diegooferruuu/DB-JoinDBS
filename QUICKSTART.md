# 🚀 INICIO RÁPIDO - Migration ETL

## 5 Pasos para Ejecutar la Migración

### 1️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Esto instala:**
- pandas (manipulación de datos)
- sqlalchemy (conexión a BD)
- psycopg2-binary (driver PostgreSQL)
- python-dotenv (carga de variables desde .env)

### 2️⃣ Configurar Credenciales en `.env`

El archivo `.env` ya existe. Edita con tus credenciales:

```bash
nano .env
```

O con VS Code:
```bash
code .env
```

Modifica:
```ini
SOURCE_DB_URL=postgresql://postgres:password@localhost:5432/datax_db
DESTINATION_DB_URL=postgresql://postgres:password@localhost:5433/datax_db
```

⚠️ **Nota:** El archivo `.env` está en `.gitignore` automáticamente (no se comitea a git)

### 3️⃣ Ejecutar el Script

```bash
python migration_etl.py
```

El script cargará automáticamente las credenciales desde `.env` y ejecutará los 6 pasos de migración.

### 4️⃣ Monitorear el Log

En otra terminal:
```bash
tail -f migration_*.log
```

### 5️⃣ Verificar Resultados

En PostgreSQL 18 (destino):
```sql
SELECT COUNT(*) as source_count FROM source;
SELECT COUNT(*) as file_count FROM file;
SELECT COUNT(*) as report_updated FROM report WHERE id_file IS NOT NULL;
```

---

## ✨ Opciones Alternativas

### Con Script Bash

```bash
chmod +x run_migration.sh
./run_migration.sh
```

### Con Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python migration_etl.py
```

### Prueba Local (Sin BD Real)

```bash
python test_simulation.py
```

---

## 📁 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| `.env` | ⚙️ Credenciales (EDITA ESTO) |
| `.env.example` | 📋 Plantilla de referencia |
| `migration_etl.py` | 🔥 Script principal |
| `requirements.txt` | 📦 Dependencias |
| `run_migration.sh` | 🎯 Script ejecutable |
| `test_simulation.py` | 🧪 Prueba sin BD |

---

## ⚠️ Antes de Ejecutar

- ✓ Hacer backup de la base de datos destino
- ✓ Verificar conexión a ambas bases de datos
- ✓ Tener credenciales correctas en `.env`
- ✓ Ejecutar en horario de bajo tráfico (TRUNCATE CASCADE)

---

## 🆘 Problemas Comunes

**"ModuleNotFoundError: No module named 'dotenv'"**
```bash
pip install python-dotenv
```

**"Cannot locate PostgreSQL installation"**
```bash
pip install psycopg2-binary
```

**"FATAL: Ident authentication failed"**
- Verificar usuario/contraseña en `.env`
- Probar conexión manual: `psql -h localhost -U postgres -d dbname`

**"relation 'source' does not exist"**
- Verificar que las tablas existen en la BD origen

---

## 📖 Documentación Completa

Ver [README.md](README.md) para documentación detallada con:
- Explicación de cada paso
- Queries de validación SQL
- Troubleshooting completo
- Casos de prueba

---

**¡Listo! 🎉 Ahora ejecuta: `python migration_etl.py`**
