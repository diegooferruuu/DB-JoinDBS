"""
Script de Prueba Local - Simula el flujo ETL sin base de datos real

Útil para verificar que el script funciona correctamente antes de
ejecutarlo contra bases de datos reales.
"""

import pandas as pd
from io import StringIO
import re

# ============================================================================
# SIMULACIÓN PASO 2: EXTRACCIÓN
# ============================================================================

def simulate_extract():
    """Simula datos extraídos de PostgreSQL 9"""
    
    # Simular tabla source
    source_data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Source_A', 'Source_B', 'Source_C', 'Source_D', 'Source_E'],
        'description': ['Desc A', 'Desc B', 'Desc C', 'Desc D', 'Desc E']
    }
    df_source = pd.DataFrame(source_data)
    
    # Simular tabla file
    file_data = {
        'id': [100, 101, 102, 103, 104, 105],
        'code': ['D_BO_000000001', 'D_BO_000000002', 'D_BO_000000003', 'D_BO_000000004', 'D_BO_000000005', 'D_BO_000000001'],
        'idsource': [1, 1, 2, 3, 4, 5],
        'filename': ['file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', 'file5.txt', 'file6.txt']
    }
    df_file = pd.DataFrame(file_data)
    
    return df_source, df_file


# ============================================================================
# SIMULACIÓN PASO 4: MAPEO DE IDS
# ============================================================================

def simulate_id_mapping(df_source):
    """
    Simula el mapeo de IDs que haría el PASO 4
    
    En realidad, cada INSERT RETURNING generaría un nuevo ID
    Simulamos que los nuevos IDs empiezan desde 1000
    """
    id_mapping = {}
    
    for idx, row in df_source.iterrows():
        original_id = row['id']
        # Simulamos auto-increment que empieza en 1000
        new_id = 1000 + idx
        id_mapping[original_id] = new_id
    
    return id_mapping


# ============================================================================
# SIMULACIÓN PASO 5: MAPEO DE FILE
# ============================================================================

def simulate_file_mapping(df_file, id_mapping):
    """Simula la actualización de idsource en file"""
    df_file['idsource'] = df_file['idsource'].map(id_mapping)
    return df_file


# ============================================================================
# SIMULACIÓN PASO 6: ACTUALIZACIÓN DE REPORT
# ============================================================================

def simulate_report_update(df_file):
    """
    Simula la lógica SQL del PASO 6:
    - Crea tabla report simulada
    - Aplica la lógica de REGEXP_REPLACE
    - Mapea los report.code con file.code
    """
    
    # Simular tabla report (que ya existe en destino)
    report_data = {
        'id': [1, 2, 3, 4, 5, 6],
        'code': ['D_BO_000000001_01', 'D_BO_000000001_02', 'D_BO_000000002_01', 
                 'D_BO_000000003_99', 'D_BO_000000004_05', 'D_BO_000000005_10'],
        'id_file': [None, None, None, None, None, None]  # Inicialmente NULL
    }
    df_report = pd.DataFrame(report_data)
    
    # Aplicar la lógica de actualización REGEXP_REPLACE
    for idx, row in df_report.iterrows():
        # Simulamos REGEXP_REPLACE(code, '_[0-9]+$', '')
        extracted_code = re.sub(r'_[0-9]+$', '', row['code'])
        
        # Buscar el código en file
        matching_files = df_file[df_file['code'] == extracted_code]
        
        if not matching_files.empty:
            # Actualizar con el id_file correspondiente
            df_report.at[idx, 'id_file'] = matching_files.iloc[0]['id']
    
    return df_report


# ============================================================================
# EJECUTAR SIMULACIÓN
# ============================================================================

def main():
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║              SIMULACIÓN DE FLUJO ETL - PRUEBA LOCAL                        ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # PASO 2: Extracción
    print("PASO 2: EXTRACCIÓN")
    print("─" * 80)
    df_source, df_file = simulate_extract()
    
    print("\nTabla SOURCE (origen):")
    print(df_source.to_string(index=False))
    print()
    
    print("Tabla FILE (origen):")
    print(df_file.to_string(index=False))
    print()
    
    # PASO 4: Mapeo de IDs
    print("\nPASO 4: MAPEO DE IDS (LÓGICA CRÍTICA)")
    print("─" * 80)
    id_mapping = simulate_id_mapping(df_source)
    
    print("\nDiccionario de Mapeo: {id_origen: id_destino}")
    for orig_id, new_id in sorted(id_mapping.items()):
        print(f"  {orig_id} → {new_id}")
    print()
    
    # PASO 5: Mapeo de File
    print("\nPASO 5: ACTUALIZACIÓN DE FILE CON NUEVO MAPEO")
    print("─" * 80)
    df_file_updated = df_file.copy()
    df_file_updated = simulate_file_mapping(df_file_updated, id_mapping)
    
    print("\nTabla FILE (después de mapeo de IDs):")
    print(df_file_updated.to_string(index=False))
    print()
    
    # PASO 6: Actualización de Report
    print("\nPASO 6: ACTUALIZACIÓN DE REPORT (LÓGICA CRÍTICA - SQL PURO)")
    print("─" * 80)
    df_report = simulate_report_update(df_file_updated)
    
    print("\nTabla REPORT (después de actualización):")
    print(df_report.to_string(index=False))
    print()
    
    # VALIDACIÓN
    print("\n" + "═" * 80)
    print("VALIDACIÓN FINAL")
    print("═" * 80)
    
    # Validar mapeo de códigos
    print("\nVerificación de mapeo de códigos (report → file):")
    print()
    for idx, row in df_report.iterrows():
        extracted_code = re.sub(r'_[0-9]+$', '', row['code'])
        
        matching_file = df_file_updated[df_file_updated['code'] == extracted_code]
        
        if not matching_file.empty:
            file_id = matching_file.iloc[0]['id']
            mapped_id = row['id_file']
            status = "✓" if file_id == mapped_id else "✗"
            print(f"{status} Report {row['code']:20} → File {extracted_code:20} (id: {mapped_id})")
        else:
            print(f"✗ Report {row['code']:20} → NO ENCONTRADO")
    
    print()
    
    # Contar actualizaciones
    updated_count = df_report['id_file'].notna().sum()
    total_count = len(df_report)
    
    print(f"Registros actualizados: {updated_count}/{total_count}")
    
    if updated_count == total_count:
        print("✓ TODAS LAS REFERENCIAS FUERON MAPEADAS CORRECTAMENTE")
    else:
        print(f"⚠ {total_count - updated_count} registros NO fueron mapeados")
    
    print()
    print("═" * 80)
    print("✓ SIMULACIÓN COMPLETADA")
    print("═" * 80)


if __name__ == "__main__":
    main()
