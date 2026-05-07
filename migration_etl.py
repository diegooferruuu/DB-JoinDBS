"""
Script de Migración ETL: PostgreSQL 9 (Origen) → PostgreSQL 18 (Destino)

Este script implementa un flujo ETL completo para migrar datos entre dos instancias
de PostgreSQL, preservando todos los datos y relaciones de integridad referencial.

Requisitos:
- pandas
- sqlalchemy
- psycopg2-binary
- python-dotenv

Variables de Entorno Requeridas:
- SOURCE_DB_URL: postgresql://user:password@host:port/dbname
- DESTINATION_DB_URL: postgresql://user:password@host:port/dbname

Flujo de Migración:
1. Conexión Dual: Establece conexiones a origen y destino
2. Extracción: Lee las tablas source y file del origen
3. Limpieza: Trunca las tablas en el destino
4. Inserción de source: Copia toda la tabla source preservando IDs
5. Inserción de file: Copia toda la tabla file preservando IDs
6. Actualización de report: Actualiza referencias en tabla report del destino

Nota: Se preservan todos los IDs originales, garantizando integridad referencial completa.
"""

import os
import sys
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import Session
from datetime import datetime

# ============================================================================
# CARGAR VARIABLES DE ENTORNO DESDE ARCHIVO .env
# ============================================================================
# Busca el archivo .env en el directorio actual
load_dotenv()

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configura el logging del script."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


# ============================================================================
# PASO 1: CONEXIÓN DUAL
# ============================================================================

def create_connections() -> tuple:
    """
    Crea conexiones SQLAlchemy separadas para origen y destino.
    
    Las URLs se obtienen de variables de entorno:
    - SOURCE_DB_URL
    - DESTINATION_DB_URL
    
    Returns:
        tuple: (engine_origen, engine_destino)
    
    Raises:
        ValueError: Si las variables de entorno no están configuradas.
        Exception: Si no se puede establecer la conexión.
    """
    try:
        source_db_url = os.getenv('SOURCE_DB_URL')
        destination_db_url = os.getenv('DESTINATION_DB_URL')
        
        if not source_db_url or not destination_db_url:
            raise ValueError(
                "Las variables de entorno SOURCE_DB_URL y DESTINATION_DB_URL son requeridas."
            )
        
        logger.info("Creando conexión con base de datos ORIGEN...")
        engine_source = create_engine(source_db_url, echo=False)
        engine_source.connect().close()
        logger.info("✓ Conexión ORIGEN exitosa")
        
        logger.info("Creando conexión con base de datos DESTINO...")
        engine_destination = create_engine(destination_db_url, echo=False)
        engine_destination.connect().close()
        logger.info("✓ Conexión DESTINO exitosa")
        
        return engine_source, engine_destination
    
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al crear conexiones: {e}")
        sys.exit(1)


# ============================================================================
# PASO 2: EXTRACCIÓN (ORIGEN)
# ============================================================================

def extract_data(engine_source) -> tuple:
    """
    Lee las tablas source y file del origen hacia DataFrames de Pandas.
    
    Args:
        engine_source: Engine de SQLAlchemy para la base de datos origen.
    
    Returns:
        tuple: (df_source, df_file)
    
    Raises:
        Exception: Si hay problemas al leer las tablas.
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("PASO 2: EXTRACCIÓN DE DATOS (ORIGEN)")
        logger.info("="*70)
        
        logger.info("Leyendo tabla 'source' desde origen...")
        df_source = pd.read_sql_table('source', engine_source)
        logger.info(f"✓ {len(df_source)} registros leídos de 'source'")
        
        logger.info("Leyendo tabla 'file' desde origen...")
        df_file = pd.read_sql_table('file', engine_source)
        logger.info(f"✓ {len(df_file)} registros leídos de 'file'")
        
        return df_source, df_file
    
    except Exception as e:
        logger.error(f"Error en extracción: {e}")
        sys.exit(1)


# ============================================================================
# PASO 3: LIMPIEZA (DESTINO)
# ============================================================================

def truncate_destination_tables(engine_destination) -> None:
    """
    Ejecuta un TRUNCATE TABLE file, source CASCADE en la base de datos destino.
    
    Esto limpia todas las tablas para asegurar una migración limpia.
    
    Args:
        engine_destination: Engine de SQLAlchemy para la base de datos destino.
    
    Raises:
        Exception: Si hay problemas al ejecutar el TRUNCATE.
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("PASO 3: LIMPIEZA DE DESTINO (TRUNCATE CASCADE)")
        logger.info("="*70)
        
        with engine_destination.connect() as connection:
            logger.info("Ejecutando TRUNCATE TABLE file CASCADE...")
            connection.execute(text("TRUNCATE TABLE file CASCADE"))
            
            logger.info("Ejecutando TRUNCATE TABLE source CASCADE...")
            connection.execute(text("TRUNCATE TABLE source CASCADE"))
            
            connection.commit()
            logger.info("✓ Truncate completado")
    
    except Exception as e:
        logger.error(f"Error en truncate: {e}")
        sys.exit(1)


# ============================================================================
# PASO 4: INSERCIÓN DE SOURCE (SIN MAPEO DE IDS - COPIA DIRECTA)
# ============================================================================

def insert_source(engine_destination, df_source: pd.DataFrame) -> None:
    """
    Inserta los registros de source en el destino tal como están en el origen.
    
    PASO 4 - LÓGICA SIMPLIFICADA:
    Copia TODO la tabla source directamente, manteniendo los IDs originales.
    De esta forma:
    - No hay conflictos con IDs autogenerados
    - Todos los registros de file que referencian source encontrarán su padre
    - No hay registros huérfanos
    
    Args:
        engine_destination: Engine de SQLAlchemy para la base de datos destino.
        df_source: DataFrame con los datos de source desde origen.
    
    Raises:
        Exception: Si hay problemas en la inserción.
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("PASO 4: INSERCIÓN DE SOURCE (COPIA DIRECTA)")
        logger.info("="*70)
        
        logger.info(f"Insertando {len(df_source)} registros de source...")
        
        # Insertamos source directamente, preservando todos los IDs originales
        df_source.to_sql(
            'source',
            engine_destination,
            if_exists='append',  # Append porque ya hicimos TRUNCATE
            index=False
        )
        
        logger.info(f"✓ Inserción de source completada")
        logger.info(f"✓ {len(df_source)} registros insertados con IDs originales preservados")
    
    except Exception as e:
        logger.error(f"Error en inserción de source: {e}")
        sys.exit(1)


# ============================================================================
# PASO 5: INSERCIÓN DE FILE (COPIA DIRECTA)
# ============================================================================

def insert_file(engine_destination, df_file: pd.DataFrame) -> None:
    """
    Inserta los registros de file en el destino tal como están en el origen.
    
    PASO 5 - LÓGICA SIMPLIFICADA:
    Copia TODO la tabla file directamente, manteniendo los IDs originales.
    Como source ya fue copiada completa, todos los id_source en file encontrarán
    su referencia en source. No hay registros huérfanos.
    
    Args:
        engine_destination: Engine de SQLAlchemy para la base de datos destino.
        df_file: DataFrame con los datos de file desde origen.
    
    Raises:
        Exception: Si hay problemas en la inserción.
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("PASO 5: INSERCIÓN DE FILE (COPIA DIRECTA)")
        logger.info("="*70)
        
        logger.info(f"Insertando {len(df_file)} registros de file...")
        
        # Insertamos file directamente, preservando todos los IDs originales
        df_file.to_sql(
            'file',
            engine_destination,
            if_exists='append',  # Append porque ya hicimos TRUNCATE
            index=False
        )
        
        logger.info(f"✓ Inserción de file completada")
        logger.info(f"✓ {len(df_file)} registros insertados con IDs originales preservados")
    
    except Exception as e:
        logger.error(f"Error en inserción de file: {e}")
        sys.exit(1)


# ============================================================================
# PASO 6: ACTUALIZACIÓN DE REPORT (CORAZÓN LÓGICO #2)
# ============================================================================

def update_report_foreign_keys(engine_destination) -> None:
    """
    Crea y ejecuta una consulta SQL pura mediante SQLAlchemy en la conexión destino
    para actualizar report.
    
    PASO 6 - CORAZÓN LÓGICO:
    Este paso es crítico porque:
    1. Extrae el código base del reporte (ej: "D_BO_000000016_01" → "D_BO_000000016")
    2. Lo busca en la tabla file
    3. Actualiza la FK id_file en report
    
    Lógica SQL:
    - SUBSTRING(r.code, 1, LENGTH(r.code) - POSITION('_' IN REVERSE(r.code)))
      O mejor: REGEXP_REPLACE(r.code, '_[0-9]+$', '')
      Esto remueve el sufijo _XX del código del reporte
    
    - Hacemos un UPDATE con JOIN para setear el nuevo id_file
    - Solo actualizamos registros donde el mapeo existe
    
    Args:
        engine_destination: Engine de SQLAlchemy para la base de datos destino.
    
    Raises:
        Exception: Si hay problemas en la actualización.
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("PASO 6: ACTUALIZACIÓN DE REPORT (LÓGICA CRÍTICA - SQL PURO)")
        logger.info("="*70)
        
        with engine_destination.connect() as connection:
            logger.info("Ejecutando UPDATE en tabla 'report' para mapear id_file...")
            
            # CONSULTA SQL PURA CON LÓGICA CRÍTICA:
            # 1. REGEXP_REPLACE extrae el código base del reporte (sin sufijo _XX)
            # 2. JOIN con file obtiene el id correspondiente
            # 3. UPDATE setea el nuevo id_file
            
            update_query = """
            UPDATE report r
            SET id_file = f.id_file
            FROM file f
            WHERE REGEXP_REPLACE(r.code, '_[0-9]+$', '') = f.code
                AND (r.id_file IS NULL OR r.id_file != f.id_file)
            """
            
            logger.info("Query ejecutada:")
            logger.info(update_query)
            
            result = connection.execute(text(update_query))
            connection.commit()
            
            rows_updated = result.rowcount
            logger.info(f"✓ UPDATE completado: {rows_updated} registros actualizados en 'report'")
    
    except Exception as e:
        logger.error(f"Error en actualización de report: {e}")
        sys.exit(1)


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Ejecuta el flujo completo de migración ETL."""
    try:
        logger.info("\n" + "🚀 "*35)
        logger.info("INICIANDO MIGRACIÓN ETL: PostgreSQL 9 → PostgreSQL 18")
        logger.info("🚀 "*35 + "\n")
        
        # PASO 1: Conexiones
        engine_source, engine_destination = create_connections()
        
        # PASO 2: Extracción
        df_source, df_file = extract_data(engine_source)
        
        # PASO 3: Limpieza
        truncate_destination_tables(engine_destination)
        
        # PASO 4: Inserción de source (copia directa, sin mapeo)
        insert_source(engine_destination, df_source)
        
        # PASO 5: Inserción de file (copia directa, sin mapeo)
        insert_file(engine_destination, df_file)
        
        # PASO 6: Actualización de report (LÓGICA CRÍTICA - SQL PURO)
        update_report_foreign_keys(engine_destination)
        
        logger.info("\n" + "="*70)
        logger.info("✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("="*70)
        logger.info("\nResumen:")
        logger.info(f"  • Registros source migrados: {len(df_source)}")
        logger.info(f"  • Registros file migrados: {len(df_file)}")
        logger.info("\nVerificar integridad de datos en la base de datos destino.\n")
    
    except Exception as e:
        logger.error(f"\n❌ Error crítico en migración: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
