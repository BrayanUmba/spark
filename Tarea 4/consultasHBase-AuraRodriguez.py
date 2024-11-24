¡import happybase
import pandas as pd
from datetime import datetime

# Bloque principal de ejecución
try:
    # 1. Establecer conexión con HBase
    connection = happybase.Connection('localhost')
    print("Conexión establecida con HBase")
    
    # 2. Crear la tabla con las familias de columnas
    table_name = 'electric_power_consumption'
    families = {
        'datetime': dict(),  # información de fecha y hora
        'measurements': dict()  # mediciones de consumo eléctrico
    }
    
    # Eliminar la tabla si ya existe
    if table_name.encode() in connection.tables():
        print(f"Eliminando tabla existente - {table_name}")
        connection.delete_table(table_name, disable=True)
    
    # Crear nueva tabla
    connection.create_table(table_name, families)
    table = connection.table(table_name)
    print("Tabla 'electric_power_consumption' creada exitosamente")
    
    # 3. Cargar datos del CSV
    power_data = pd.read_csv('household_power_consumption.txt', sep=';', 
                             parse_dates={'datetime': ['Date', 'Time']}, 
                             infer_datetime_format=True, 
                             low_memory=False, 
                             na_values=['nan','?'])
    
    # Iterar sobre el DataFrame usando el índice
    for index, row in power_data.iterrows():
        # Generar row key basado en el índice
        row_key = f'power_{index}'.encode()
        
        # Organizar los datos en familias de columnas
        data = {
            b'datetime:timestamp': str(row['datetime']).encode(),
            b'measurements:global_active_power': str(row['Global_active_power']).encode(),
            b'measurements:global_reactive_power': str(row['Global_reactive_power']).encode(),
            b'measurements:voltage': str(row['Voltage']).encode(),
            b'measurements:global_intensity': str(row['Global_intensity']).encode(),
            b'measurements:sub_metering_1': str(row['Sub_metering_1']).encode(),
            b'measurements:sub_metering_2': str(row['Sub_metering_2']).encode(),
            b'measurements:sub_metering_3': str(row['Sub_metering_3']).encode()
        }
        
        table.put(row_key, data)
    
    print("Datos cargados exitosamente")
    
    # 4. Consultas y Análisis de Datos
    print("\n=== Primeros 3 registros en la base de datos ===")
    count = 0
    for key, data in table.scan():
        if count < 3:  # Limitamos a 3 para el ejemplo
            print(f"\nRegistro ID: {key.decode()}")
            print(f"Timestamp: {data[b'datetime:timestamp'].decode()}")
            print(f"Global Active Power: {data[b'measurements:global_active_power'].decode()}")
            count += 1
    
    # 5. Análisis de consumo por rango de tiempo
    print("\n=== Consumo en un rango de tiempo específico ===")
    start_time = '2007-02-01 00:00:00'
    end_time = '2007-02-02 00:00:00'
    for key, data in table.scan():
        timestamp = data[b'datetime:timestamp'].decode()
        if start_time <= timestamp <= end_time:
            print(f"\nRegistro ID: {key.decode()}")
            print(f"Timestamp: {timestamp}")
            print(f"Global Active Power: {data[b'measurements:global_active_power'].decode()}")
    
    # 6. Análisis de consumo por tipo de submedición
    print("\n=== Consumo por tipo de submedición ===")
    sub_metering_stats = {'sub_metering_1': 0, 'sub_metering_2': 0, 'sub_metering_3': 0}
    for key, data in table.scan():
        sub_metering_stats['sub_metering_1'] += float(data[b'measurements:sub_metering_1'].decode())
        sub_metering_stats['sub_metering_2'] += float(data[b'measurements:sub_metering_2'].decode())
        sub_metering_stats['sub_metering_3'] += float(data[b'measurements:sub_metering_3'].decode())
    
    for sub_metering, total in sub_metering_stats.items():
        print(f"{sub_metering}: {total:.2f} unidades")
    
    # 7. Ejemplo de actualización de un valor
    record_to_update = 'power_0'
    new_value = 1.234
    table.put(record_to_update.encode(), {b'measurements:global_active_power': str(new_value).encode()})
    print(f"\nValor actualizado para el registro ID: {record_to_update}")
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    # Cerrar la conexión
    connection.close()
```

Este código sigue los mismos pasos que el ejemplo original, pero adaptado para trabajar con el dataset de consumo eléctrico de Kaggle[1](https://www.kaggle.com/datasets/fedesoriano/electric-power-consumption). ¡Espero que te sea útil! Si tienes alguna pregunta o necesitas más ayuda, no dudes en decírmelo.

[1](https://www.kaggle.com/datasets/fedesoriano/electric-power-consumption): [Kaggle: Electric Power Consumption](https://www.kaggle.com/datasets/fedesoriano/electric-power-consumption)