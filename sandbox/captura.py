import requests
import os
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time

def GetsUrls():
    url = 'https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRECasa/Casa.aspx'
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'lxml')
    
    div = soup.find('div', {'class': 'col-xs-12'})
    links = div.find_all('a')
    
    Urls = {}
    
    for link in links:
        name = 'Tarifa_' + link.text.strip()
        href = link['href']
        full_url = urljoin(url, href)
        Urls[name] = full_url
    
    return Urls

def generate_json_files():
    links = GetsUrls()
    key_to_eliminar = {'Tarifa_1', 'Tarifa_DAC'}
    links = {key: value for key, value in links.items() if key not in key_to_eliminar}
    
    output_dir = os.path.join('sandbox', 'tarifas_json')
    os.makedirs(output_dir, exist_ok=True)
    
    for name, url in links.items():
        data = initialize_data_structure(url)
        file_name = f"{name.replace(' ', '_')}.json"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

def initialize_data_structure(url):
    driver = webdriver.Chrome()
    driver.get(url)
    data = {}
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Fecha_ddAnio')))
        
        Years_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
        Years_options = {option.get_attribute('value'): option.text for option in Years_select.options if option.get_attribute('value') != '0'}
        
        Summer_Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesVerano'))
        Summer_Month_options = {option.get_attribute('value'): option.text for option in Summer_Month_select.options if option.get_attribute('value') != '0'}
        
        Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano2_ddMesConsulta'))
        Month_options = {option.get_attribute('value'): option.text for option in Month_select.options if option.get_attribute('value') != '0'}
        
        for Year_value, Year_text in Years_options.items():
            data[Year_text] = {}
            
            for Summer_Month_value, Summer_Month_text in Summer_Month_options.items():
                data[Year_text][Summer_Month_value] = {}
                
                for Month_value, Month_text in Month_options.items():
                    data[Year_text][Summer_Month_value][Month_value] = {}
    
    except TimeoutException:
        print(f"No se pudo cargar la página para la URL: {url}")
    
    driver.quit()
    return data

def update_json_files():
    output_dir = os.path.join('sandbox', 'tarifas_json')
    driver = webdriver.Chrome()

    links = GetsUrls()

    for json_file in os.listdir(output_dir):
        if json_file.endswith(".json"):
            file_path = os.path.join(output_dir, json_file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = json_file.replace('.json', '')
            
            if name not in links:
                print(f"No se encontró la URL para {name}")
                continue
            
            url = links[name]
            driver.get(url)
            
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Fecha_ddAnio')))
                
                for Year_value in data.keys():
                    for Summer_Month_value in data[Year_value].keys():
                        # Reload the page for each year and summer month combination
                        driver.get(url)
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Fecha_ddAnio')))
                        
                        Years_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
                        Summer_Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesVerano'))
                        Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano2_ddMesConsulta'))

                        Years_select.select_by_value(Year_value)
                        Summer_Month_select.select_by_value(Summer_Month_value)

                        # Get available months
                        available_months = [option.get_attribute('value') for option in Month_select.options if option.get_attribute('value') != '0']
                        print(f"Available months for {name}, Year: {Year_value}, Summer Month: {Summer_Month_value}: {available_months}")

                        for Month_value in available_months:
                            if Month_value not in data[Year_value][Summer_Month_value]:
                                data[Year_value][Summer_Month_value][Month_value] = {}
                            
                            try:
                                Month_select.select_by_value(Month_value)
                            except NoSuchElementException:
                                print(f"No se pudo seleccionar el mes {Month_value} para {name}, Year: {Year_value}, Summer Month: {Summer_Month_value}")
                                continue
                            
                            time.sleep(5)
                            
                            try:
                                table = WebDriverWait(driver, 20).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'table'))
                                )
                                
                                rows = table.find_elements(By.TAG_NAME, 'tr')
                                
                                for row in rows:
                                    cols = row.find_elements(By.TAG_NAME, 'td')
                                    if len(cols) == 3:
                                        consumo_tipo = cols[0].text.strip()
                                        tarifa = cols[1].text.strip()
                                        descripcion = cols[2].text.strip()
                                        
                                        data[Year_value][Summer_Month_value][Month_value][consumo_tipo] = {
                                            'Tarifa': tarifa,
                                            'descripcion': descripcion
                                        }
                                
                                print(f"Data captured for {name}, Year: {Year_value}, Summer Month: {Summer_Month_value}, Month: {Month_value}")
                            
                            except TimeoutException:
                                print(f"Timeout waiting for table to load for {name}, Year: {Year_value}, Summer Month: {Summer_Month_value}, Month: {Month_value}")
                            except Exception as e:
                                print(f"Unexpected error for {name}, Year: {Year_value}, Summer Month: {Summer_Month_value}, Month: {Month_value}: {str(e)}")
            
            except TimeoutException:
                print(f"No se pudo cargar la página para {name}")
            except StaleElementReferenceException:
                print(f"Referencia a elemento obsoleta para {name}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    
    driver.quit()

# Primero generamos los archivos JSON con la estructura inicial
#generate_json_files()

# Luego actualizamos los archivos JSON con los datos de la tabla
update_json_files()