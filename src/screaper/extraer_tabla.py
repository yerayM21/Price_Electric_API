import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
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
    anio_select.select_by_value(anio_value)
    
    for mes_value, mes_text in mes_options.items():
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
                table = row.find('table', {'align': 'center'})
                
                if table:
                    tbody = table.find('tbody')
                    
                    if tbody:
                        tr_list = tbody.find_all('tr')
                        
                        for tr in tr_list:
                            tds = tr.find_all('td')
                            
                            if len(tds) >= 3:
                                key = tds[0].find('b').text.strip() if tds[0].find('b') else 'N/A'
                                value = tds[1].text.strip() if tds[1] else 'N/A'
                                condition = tds[2].text.strip() if tds[2] else 'N/A'
                                
                                data[anio_text][mes_text][key] = {
                                    'value': value,
                                    'condition': condition
                                }
                    else:
                        print(f"No se encontró el tbody en la tabla para año {anio_text} y mes {mes_text}.")
                else:
                    print(f"No se encontró la tabla con class 'table' para año {anio_text} y mes {mes_text}.")
        else:
            print(f"No se encontró la tabla con id 'ContentPlaceHolder1_TemporadaFV' para año {anio_text} y mes {mes_text}.")

# Cerrar el navegador
driver.quit()

# Imprimir el diccionario resultante
import pprint
pprint.pprint(data)
