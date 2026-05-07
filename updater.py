"""
Script de Actualización: Sincroniza cambios de DB Antigua a DB Nueva

Este script compara fila por fila la tabla 'file' entre la base de datos antigua
y la nueva, identificando cambios por 'code' (no por id_file).

Si hay diferencias en los campos (excepto id_source), actualiza los registros
en la base de datos nueva con los valores de la antigua.

Requisitos:
- pandas
- sqlalchemy
- psycopg2-binary
- python-dotenv

Variables de Entorno Requeridas:
- SOURCE_DB_URL: postgresql://user:password@host:port/dbname (DB antigua)
- DESTINATION_DB_URL: postgresql://user:password@host:port/dbname (DB nueva)
"""

import os
import sys
import logging
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
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
            logging.FileHandler(f'updater_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================================
# CONEXIONES A BASE DE DATOS
# ============================================================================

def create_connections() -> tuple:
    """
    Crea conexiones SQLAlchemy para base de datos antigua (origen) y nueva (destino).
    
    Returns:
        tuple: (engine_old, engine_new)
    
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
        
        logger.info("Creando conexión con base de datos ANTIGUA (origen)...")
        engine_old = create_engine(source_db_url, echo=False)
        engine_old.connect().close()
        logger.info("✓ Conexión DB ANTIGUA exitosa")
        
        logger.info("Creando conexión con base de datos NUEVA (destino)...")
        engine_new = create_engine(destination_db_url, echo=False)
        engine_new.connect().close()
        logger.info("✓ Conexión DB NUEVA exitosa")
        
        return engine_old, engine_new
    
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al crear conexiones: {e}")
        sys.exit(1)


# ============================================================================
# EXTRACCIÓN DE DATOS
# ============================================================================

def extract_file_tables(engine_old, engine_new) -> tuple:
    """
    Extrae la tabla 'file' de ambas bases de datos hacia DataFrames de Pandas.
    
    Args:
        engine_old: Engine para la base de datos antigua.
        engine_new: Engine para la base de datos nueva.
    
    Returns:
        tuple: (df_old, df_new) - DataFrames de ambas bases de datos
    
    Raises:
        Exception: Si hay problemas al leer las tablas.
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("EXTRACCIÓN DE DATOS DE LA TABLA 'file'")
        logger.info("="*70)
        
        logger.info("Leyendo tabla 'file' desde DB ANTIGUA...")
        df_old = pd.read_sql_table('file', engine_old)
        logger.info(f"✓ {len(df_old)} registros leídos de DB antigua")
        
        logger.info("Leyendo tabla 'file' desde DB NUEVA...")
        df_new = pd.read_sql_table('file', engine_new)
        logger.info(f"✓ {len(df_new)} registros leídos de DB nueva")
        
        return df_old, df_new
    
    except Exception as e:
        logger.error(f"Error en extracción: {e}")
        sys.exit(1)


# ============================================================================
# COMPARACIÓN Y DETECCIÓN DE CAMBIOS
# ============================================================================

def detect_changes(df_old: pd.DataFrame, df_new: pd.DataFrame) -> List[Dict]:
    """
    Compara fila por fila ambas tablas por 'code' y detecta cambios.
    
    Excepto el campo 'id_source', compara todos los campos.
    Para cada código encontrado en ambas tablas, verifica si hay diferencias.
    
    Args:
        df_old: DataFrame de la DB antigua
        df_new: DataFrame de la DB nueva
    
    Returns:
        List[Dict]: Lista de cambios detectados con estructura:
                    {
                        'code': str,
                        'old_id': int,
                        'new_id': int,
                        'changes': {
                            'field_name': {'old': old_value, 'new': new_value},
                            ...
                        }
                    }
    """
    logger.info("\n" + "="*70)
    logger.info("DETECCIÓN DE CAMBIOS")
    logger.info("="*70)
    
    changes_detected = []
    
    # Campos a ignorar en la comparación
    IGNORE_FIELDS = {'id_source', 'idsource'}  # En caso de variaciones en nombres
    
    # Obtener columnas comunes entre ambas tablas
    common_columns = set(df_old.columns) & set(df_new.columns)
    compare_columns = [col for col in common_columns if col not in IGNORE_FIELDS]
    
    logger.info(f"Campos a comparar: {compare_columns}")
    logger.info(f"Campos ignorados: {IGNORE_FIELDS}")
    
    # Agrupar por 'code' para comparación
    try:
        old_grouped = df_old.groupby('code')
        new_grouped = df_new.groupby('code')
    except KeyError:
        logger.error("❌ La columna 'code' no existe en una de las tablas")
        sys.exit(1)
    
    total_codes = len(old_grouped)
    codes_with_changes = 0
    
    # Iterar por cada código en la DB antigua
    for code, old_rows in old_grouped:
        if code not in new_grouped.groups:
            logger.warning(f"⚠ Código '{code}' NO existe en DB nueva (será omitido)")
            continue
        
        new_rows = new_grouped.get_group(code)
        
        # Si hay múltiples filas con el mismo código, comparar la primera
        old_row = old_rows.iloc[0] if len(old_rows) > 0 else None
        new_row = new_rows.iloc[0] if len(new_rows) > 0 else None
        
        if old_row is None or new_row is None:
            continue
        
        # Comparar campos (excepto id_source)
        row_changes = {}
        
        for column in compare_columns:
            if column not in old_row.index or column not in new_row.index:
                continue
            
            old_value = old_row[column]
            new_value = new_row[column]
            
            # Comparar valores (manejar NaN)
            values_different = False
            
            if pd.isna(old_value) and pd.isna(new_value):
                values_different = False
            elif pd.isna(old_value) or pd.isna(new_value):
                values_different = True
            else:
                values_different = old_value != new_value
            
            if values_different:
                row_changes[column] = {
                    'old': old_value,
                    'new': new_value
                }
        
        # Si hay cambios, registrarlos
        if row_changes:
            changes_detected.append({
                'code': code,
                'old_id': old_row.get('id', None),
                'new_id': new_row.get('id', None),
                'changes': row_changes
            })
            codes_with_changes += 1
    
    logger.info(f"\n✓ Análisis completado:")
    logger.info(f"  • Códigos totales en DB antigua: {total_codes}")
    logger.info(f"  • Códigos con cambios: {codes_with_changes}")
    logger.info(f"  • Cambios totales detectados: {len(changes_detected)}")
    
    return changes_detected


# ============================================================================
# REPORTE DETALLADO DE CAMBIOS
# ============================================================================

def generate_change_report(changes: List[Dict]) -> None:
    """
    Genera un reporte detallado de los cambios detectados.
    
    Args:
        changes: Lista de cambios detectados
    """
    logger.info("\n" + "="*70)
    logger.info("REPORTE DETALLADO DE CAMBIOS")
    logger.info("="*70)
    
    if not changes:
        logger.info("✓ No hay cambios detectados entre ambas bases de datos")
        return
    
    for idx, change in enumerate(changes, 1):
        logger.info(f"\n[{idx}] Código: {change['code']}")
        logger.info(f"    ID antigua: {change['old_id']} → ID nueva: {change['new_id']}")
        
        for field, values in change['changes'].items():
            old_val = values['old']
            new_val = values['new']
            logger.info(f"    • {field}:")
            logger.info(f"      - Antiguo: {old_val}")
            logger.info(f"      - Nuevo:  {new_val}")


# ============================================================================
# APLICAR CAMBIOS EN DB NUEVA
# ============================================================================

def apply_changes(engine_new, changes: List[Dict]) -> int:
    """
    Aplica los cambios detectados en la base de datos nueva.
    
    Por cada cambio, actualiza los campos en la tabla 'file' usando
    la columna 'code' como identificador (no 'id_file').
    
    Args:
        engine_new: Engine para la base de datos nueva
        changes: Lista de cambios detectados
    
    Returns:
        int: Número de registros actualizados
    
    Raises:
        Exception: Si hay problemas en la actualización
    """
    logger.info("\n" + "="*70)
    logger.info("APLICANDO CAMBIOS EN DB NUEVA")
    logger.info("="*70)
    
    if not changes:
        logger.info("No hay cambios para aplicar")
        return 0
    
    total_updated = 0
    
    try:
        with engine_new.connect() as connection:
            for idx, change in enumerate(changes, 1):
                code = change['code']
                fields_to_update = change['changes']
                
                # Construir la consulta UPDATE dinámicamente
                set_clause = ", ".join([f"{field} = :{field}" for field in fields_to_update.keys()])
                
                update_query = f"""
                UPDATE file
                SET {set_clause}
                WHERE code = :code
                """
                
                # Preparar parámetros
                params = {'code': code}
                params.update({field: values['old'] for field, values in fields_to_update.items()})
                
                try:
                    result = connection.execute(text(update_query), params)
                    rows_affected = result.rowcount
                    
                    if rows_affected > 0:
                        logger.info(f"[{idx}] Actualizado código '{code}': {rows_affected} registro(s)")
                        total_updated += rows_affected
                    else:
                        logger.warning(f"[{idx}] ⚠ Código '{code}' no actualizado (0 registros afectados)")
                
                except Exception as e:
                    logger.error(f"[{idx}] ❌ Error al actualizar código '{code}': {e}")
                    continue
            
            # Confirmar todas las transacciones
            connection.commit()
            logger.info(f"\n✓ Transacción confirmada: {total_updated} registros actualizados")
    
    except Exception as e:
        logger.error(f"Error aplicando cambios: {e}")
        sys.exit(1)
    
    return total_updated


# ============================================================================
# VALIDACIÓN POST-ACTUALIZACIÓN
# ============================================================================

def validate_updates(engine_old, engine_new, changes: List[Dict]) -> None:
    """
    Valida que los cambios se hayan aplicado correctamente.
    
    Args:
        engine_old: Engine para la base de datos antigua
        engine_new: Engine para la base de datos nueva
        changes: Lista de cambios que se aplicaron
    """
    logger.info("\n" + "="*70)
    logger.info("VALIDACIÓN POST-ACTUALIZACIÓN")
    logger.info("="*70)
    
    if not changes:
        logger.info("No hay cambios para validar")
        return
    
    try:
        df_old = pd.read_sql_table('file', engine_old)
        df_new = pd.read_sql_table('file', engine_new)
        
        validation_passed = True
        
        for change in changes:
            code = change['code']
            
            # Obtener filas por código
            old_rows = df_old[df_old['code'] == code]
            new_rows = df_new[df_new['code'] == code]
            
            if old_rows.empty or new_rows.empty:
                continue
            
            old_row = old_rows.iloc[0]
            new_row = new_rows.iloc[0]
            
            # Verificar que los cambios se aplicaron
            for field in change['changes'].keys():
                old_value = old_row[field]
                new_value = new_row[field]
                
                if pd.isna(old_value) and pd.isna(new_value):
                    continue
                
                if old_value != new_value:
                    logger.error(f"❌ Validación FALLÓ para código '{code}', campo '{field}'")
                    logger.error(f"   Esperado (antiguo): {old_value}")
                    logger.error(f"   Obtenido (nuevo): {new_value}")
                    validation_passed = False
                else:
                    logger.info(f"✓ Validado: código '{code}', campo '{field}' = {old_value}")
        
        if validation_passed:
            logger.info("\n✓ VALIDACIÓN EXITOSA: Todos los cambios se aplicaron correctamente")
        else:
            logger.warning("\n⚠ VALIDACIÓN CON ADVERTENCIAS: Revise los errores anteriores")
    
    except Exception as e:
        logger.error(f"Error en validación: {e}")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Ejecuta el flujo completo de actualización."""
    try:
        logger.info("\n" + "🔄 "*35)
        logger.info("INICIANDO ACTUALIZACIÓN: DB ANTIGUA → DB NUEVA")
        logger.info("🔄 "*35 + "\n")
        
        # PASO 1: Conexiones
        engine_old, engine_new = create_connections()
        
        # PASO 2: Extracción
        df_old, df_new = extract_file_tables(engine_old, engine_new)
        
        # PASO 3: Detección de cambios
        changes = detect_changes(df_old, df_new)
        
        # PASO 4: Reporte detallado
        generate_change_report(changes)
        
        # PASO 5: Aplicar cambios automáticamente
        if changes:
            total_updated = apply_changes(engine_new, changes)
            
            # PASO 6: Validación
            validate_updates(engine_old, engine_new, changes)
            
            logger.info("\n" + "="*70)
            logger.info("✓ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("="*70)
            logger.info(f"\nResumen:")
            logger.info(f"  • Cambios detectados: {len(changes)}")
            logger.info(f"  • Registros actualizados: {total_updated}\n")
        else:
            logger.info("\n✓ No hay cambios para aplicar")
    
    except Exception as e:
        logger.error(f"\n❌ Error crítico en actualización: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
