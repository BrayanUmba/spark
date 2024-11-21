import happybase
import pandas as pd
from datetime import datetime

try:
    # 1. Establecer conexión con HBase
    connection = happybase.Connection('localhost')
    print("Conexión establecida con HBase")

    # 2. Crear la tabla con las familias de columnas
    table_name = 'subsidios_vivienda'
    families = {
        'ubicacion': dict(),    # información geográfica
        'programa': dict(),     # detalles del programa
        'asignacion': dict(),   # información de asignación
        'financiero': dict()    # información financiera
    }

    # Eliminar la tabla si ya existe
    if table_name.encode() in connection.tables():
        print(f"Eliminando tabla existente - {table_name}")
        connection.delete_table(table_name, disable=True)

    # Crear nueva tabla
    connection.create_table(table_name, families)
    table = connection.table(table_name)
    print("Tabla 'subsidios_vivienda' creada exitosamente")

    # 3. Cargar datos del CSV con la codificación correcta
    subsidios_data = pd.read_csv('h2yr-zfb2.csv', encoding='latin1')

    # Renombrar las columnas para evitar problemas con caracteres especiales
    subsidios_data.columns = [
        'Departamento',
        'Codigo_Divipola_Departamento',
        'Municipio',
        'Codigo_Divipola_Municipio',
        'Programa',
        'Anio_Asignacion',
        'Estado_Postulacion',
        'Hogares',
        'Valor_Asignado'
    ]

    print("Columnas del DataFrame:", subsidios_data.columns.tolist())

    # Iterar sobre el DataFrame usando el índice
    for index, row in subsidios_data.iterrows():
        try:
            # Generar row key basado en departamento, municipio y año
            row_key = f"{row['Codigo_Divipola_Departamento']}_{row['Codigo_Divipola_Municipio']}_{row['Anio_Asignacion']}_{index}".encode('utf-8')

            # Organizar los datos en familias de columnas
            data = {
                b'ubicacion:departamento': str(row['Departamento']).encode('utf-8'),
                b'ubicacion:cod_departamento': str(row['Codigo_Divipola_Departamento']).encode('utf-8'),
                b'ubicacion:municipio': str(row['Municipio']).encode('utf-8'),
                b'ubicacion:cod_municipio': str(row['Codigo_Divipola_Municipio']).encode('utf-8'),

                b'programa:nombre': str(row['Programa']).encode('utf-8'),
                b'programa:estado': str(row['Estado_Postulacion']).encode('utf-8'),

                b'asignacion:anio': str(row['Anio_Asignacion']).encode('utf-8'),
                b'asignacion:hogares': str(row['Hogares']).encode('utf-8'),

                b'financiero:valor': str(row['Valor_Asignado']).encode('utf-8')
            }

            table.put(row_key, data)

        except Exception as e:
            print(f"Error procesando fila {index}: {str(e)}")
            continue

    print("Datos cargados exitosamente")

    # 4. Análisis de Datos

    # 4.1 Subsidios por departamento
    print("\n=== Total de subsidios por departamento ===")
    dept_stats = {}
    for key, data in table.scan():
        dept = data[b'ubicacion:departamento'].decode('utf-8')
        hogares = int(data[b'asignacion:hogares'].decode('utf-8'))
        dept_stats[dept] = dept_stats.get(dept, 0) + hogares

    for dept, total in sorted(dept_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{dept}: {total} hogares beneficiados")

    # 4.2 Análisis por programa
    print("\n=== Valor total asignado por programa ===")
    program_stats = {}
    for key, data in table.scan():
        programa = data[b'programa:nombre'].decode('utf-8')
        valor = float(data[b'financiero:valor'].decode('utf-8'))
        program_stats[programa] = program_stats.get(programa, 0) + valor

    for programa, valor in sorted(program_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{programa}: ${valor:,.2f}")

    # 4.3 Evolución temporal
    print("\n=== Evolución de asignaciones por año ===")
    year_stats = {}
    for key, data in table.scan():
        anio = int(data[b'asignacion:anio'].decode('utf-8'))
        hogares = int(data[b'asignacion:hogares'].decode('utf-8'))
        year_stats[anio] = year_stats.get(anio, 0) + hogares

    for anio in sorted(year_stats.keys()):
        print(f"{anio}: {year_stats[anio]} hogares")

    # 4.4 Estado de postulaciones
    print("\n=== Estados de postulación ===")
    estado_stats = {}
    for key, data in table.scan():
        estado = data[b'programa:estado'].decode('utf-8')
        hogares = int(data[b'asignacion:hogares'].decode('utf-8'))
        estado_stats[estado] = estado_stats.get(estado, 0) + hogares

    for estado, total in sorted(estado_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{estado}: {total} hogares")

    # 4.5 Top 5 municipios con mayor inversión
    print("\n=== Top 5 municipios con mayor inversión ===")
    muni_stats = {}
    for key, data in table.scan():
        muni_key = f"{data[b'ubicacion:departamento'].decode('utf-8')} - {data[b'ubicacion:municipio'].decode('utf-8')}"
        valor = float(data[b'financiero:valor'].decode('utf-8'))
        muni_stats[muni_key] = muni_stats.get(muni_key, 0) + valor

    for muni, valor in sorted(muni_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{muni}: ${valor:,.2f}")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    # Cerrar la conexión
    connection.close()
