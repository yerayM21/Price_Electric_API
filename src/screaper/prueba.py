import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup

# Configuración del WebDriver
driver = webdriver.Chrome()

# Paso 1: Navegar a la página
url = 'https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRECasa/Tarifas/Tarifa1.aspx'
driver.get(url)

# Esperar a que la página cargue completamente
time.sleep(3)

# Paso 2: Capturar los <option> de <select id='ContentPlaceHolder1_Fecha_ddAnio'>
anio_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
anio_options = {option.get_attribute('value'): option.text for option in anio_select.options if option.get_attribute('value') != '0'}

# Paso 3: Capturar los <option> de <select id='ContentPlaceHolder1_MesVerano1_ddMesConsulta'>
mes_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesConsulta'))
mes_options = {option.get_attribute('value'): option.text for option in mes_select.options if option.get_attribute('value') != '0'}

# Inicializar el diccionario principal
data = {}

# Paso 4: Recorrer las combinaciones de <option> y extraer la tabla correspondiente
for anio_value, anio_text in anio_options.items():
    data[anio_text] = {}
    
    for mes_value, mes_text in mes_options.items():
        try:
            # Seleccionar el año
            anio_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
            anio_select.select_by_value(anio_value)
            
            # Seleccionar el mes
            mes_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesConsulta'))
            mes_select.select_by_value(mes_value)
            
            time.sleep(10)  # Esperar a que la tabla se actualice
            
            # Obtener el HTML actualizado
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Encontrar la tabla actualizada
            temporada_table = soup.find('table', {'id': 'ContentPlaceHolder1_TemporadaFV'})
            
            if temporada_table:
                data[anio_text][mes_text] = {}
                rows = temporada_table.find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 3:
                        consumo_tipo = cols[0].get_text(strip=True)
                        tarifa = cols[1].get_text(strip=True)
                        descripcion = cols[2].get_text(strip=True)
                        
                        data[anio_text][mes_text][consumo_tipo] = {
                            'tarifa': tarifa,
                            'descripcion': descripcion
                        }
        except StaleElementReferenceException:
            print(f"Elemento obsoleto encontrado. Reintentando la selección para año {anio_text} y mes {mes_text}.")

# Cerrar el WebDriver
driver.quit()

# Guardar los datos capturados en un archivo JSON
with open('data.json', 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

# Imprimir los datos capturados (opcional)
import pprint
pprint.pprint(data)
