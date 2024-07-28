from screaper.Extraer_Tarifa1 import GetsUrls
import requests
import re
import time
import json
import os 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def Tarifas_JsonData():
    links = GetsUrls()
    key_to_eliminar = {'Tarifa_1','Tarifa_DAC'}
    # Filtrar los links que usaremos
    links = {key: value for key,value in links.items() if key not in key_to_eliminar}
    
    # Configuración del WebDriver
    driver = webdriver.Chrome()
    
    output_dir = os.path.join('src', 'scraper', 'tarifas_json')
    os.makedirs(output_dir, exist_ok=True)
    
    for name, url in links.items():
        driver.get(url)
        
        time.sleep(10)
        
        Years_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
        Years_options = {option.get_attribute('value'): option.text for option in Years_select.options if option.get_attribute('value') != '0'}
        
        Summer_Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesVerano'))
        Summer_Month_options = {option.get_attribute('value'): option.text for option in Summer_Month_select.options if option.get_attribute('value') != '0'}
        
        Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano2_ddMesConsulta'))
        Month_options = {option.get_attribute('value'): option.text for option in Month_select.options if option.get_attribute('value') != '0'}
        
        data = {}
        
        for Year_value, Year_text in Years_options.items():
            data[Year_text] = {}
            
            for Summer_Month_value, Summer_Month_text in Summer_Month_options.items():
                data[Year_text][Summer_Month_value] = {}
                
                for Month_value, Month_text in Month_options.items():
                    retry_count = 0
                    max_retries = 3
                    while retry_count < max_retries:
                        try:
                            Years_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
                            Years_select.select_by_value(Year_value)
                            
                            Summer_Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesVerano'))
                            Summer_Month_select.select_by_value(Summer_Month_value)
                            
                            Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano2_ddMesConsulta'))
                            Month_select.select_by_value(Month_value)
                            
                            time.sleep(10)
                            
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            
                            season_table = soup.find('table', {'id': 'ContentPlaceHolder1_TemporadaFV'})
                            
                            if season_table:
                                data[Year_text][Summer_Month_value][Month_value] = {}
                                rows = season_table.find_all('tr')
                                time.sleep(10)
                                for row in rows:
                                    cols = row.find_all('td')
                                    time.sleep(10)
                                    if len(cols) == 3:
                                        consumo_tipo = cols[0].get_text(strip=True)
                                        tarifa = cols[1].get_text(strip=True)
                                        descripcion = cols[2].get_text(strip=True)
                                        
                                        data[Year_text][Summer_Month_value][Month_value][consumo_tipo] = {
                                            'Tarifa': tarifa,
                                            'descripcion': descripcion
                                        }
                            break
                        except StaleElementReferenceException:
                            retry_count += 1
                            print(f'Elemento obsoleto encontrado. Reintentando la selección para año {Year_text}, mes cae el verano {Summer_Month_text} y mes {Month_text}. Intento {retry_count}/{max_retries}.')
                            time.sleep(5)
                    else:
                        print(f'No se pudo completar la selección después de {max_retries} intentos para año {Year_text}, mes cae el verano {Summer_Month_text} y mes {Month_text}.')
            
        file_name = f"{name.replace(' ', '_')}.json"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    driver.quit()

Tarifas_JsonData()


