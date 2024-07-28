import pymongo
import json
import os
from pymongo import MongoClient, InsertOne
from pymongo.errors import ConfigurationError

try:
    # Conexión a MongoDB
    client = MongoClient('mongodb://localhost/')
    print("Conexión exitosa a MongoDB")
    
    # Selección de la base de datos y colección
    db = client["Tarifas_Electricas"]
    col = db["Tarifa_1"]
    
    # Lista para almacenar las solicitudes de inserción
    requesting = []


    # Lectura y carga de datos JSON
    with open(r'src\Import\tarifas_json\Tarifa_1.json') as f:
        data = json.load(f)

    # Verificar el tipo de datos cargados
    if not isinstance(data, dict):
        raise TypeError("El archivo JSON no contiene un diccionario en el nivel superior.")

    # Transformar la estructura anidada en documentos planos
    for year, months in data.items():
        if not isinstance(months, dict):
            raise TypeError(f"Los datos para el año {year} no son un diccionario.")
        for month, tarifas in months.items():
            if not isinstance(tarifas, dict):
                raise TypeError(f"Los datos para el mes {month} no son un diccionario.")
            for tipo_consumo, detalle in tarifas.items():
                if not isinstance(detalle, dict):
                    raise TypeError(f"Los datos para el tipo de consumo {tipo_consumo} no son un diccionario.")
                document = {
                    'year': year,
                    'month': month,
                    'tipo_consumo': tipo_consumo,
                    'tarifa': detalle['Tarifa'],
                    'descripcion': detalle['descripcion']
                }
                requesting.append(InsertOne(document))
    
    # Inserción masiva de datos
    if requesting:
        result = col.bulk_write(requesting)
        print("Inserción masiva completada con éxito")
    else:
        print("No se encontraron documentos válidos para insertar.")
    
except ConfigurationError as e:
    print(f"Error de configuración de MongoDB: {e}")
except FileNotFoundError as e:
    print(f"Archivo no encontrado: {e}")
except json.JSONDecodeError as e:
    print(f"Error decodificando JSON: {e}")
except TypeError as e:
    print(f"Error de tipo de datos: {e}")
except Exception as e:
    print(f"Se produjo un error: {e}")
finally:
    # Cierre de la conexión a MongoDB
    client.close()
    print("Conexión a MongoDB cerrada")
