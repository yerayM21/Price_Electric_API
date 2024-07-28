
import requests
import re
import time
import json
import os 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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

def Tarifas_JsonData():
    links = GetsUrls()
    key_to_eliminar = {'Tarifa_1','Tarifa_DAC'}
    links = {key: value for key, value in links.items() if key not in key_to_eliminar}
    
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)
    
    output_dir = os.path.join('sandbox', 'tarifas_json')
    os.makedirs(output_dir, exist_ok=True)
    
    driver.get(links['Tarifa_1C'])
    
    data = []
    
    Years_select = Select(wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))))
    Years_options = {option.get_attribute('value'): option.text for option in Years_select.options if option.get_attribute('value') != '0'}
    
    Summer_Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesVerano'))
    Summer_Month_options = {option.get_attribute('value'): option.text for option in Summer_Month_select.options if option.get_attribute('value') != '0'}
    
    Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano2_ddMesConsulta'))
    Month_options = {option.get_attribute('value'): option.text for option in Month_select.options if option.get_attribute('value') != '0'}
    
    for Month_value, Month_text in Month_options.items():
        try:
            Years_select = Select(wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))))
            Years_select.select_by_value('2024')
            
            Summer_Month_select = Select(wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesVerano'))))
            Summer_Month_select.select_by_value('2')
            
            Month_select = Select(wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_MesVerano2_ddMesConsulta'))))
            Month_select.select_by_value(Month_value)
            
            wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_TemporadaFV')))
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            season_table = soup.find('table', {'id': 'ContentPlaceHolder1_TemporadaFV'})
            new_table = season_table.find('table', {'class': 'table'})
            
            if new_table :
                rows = season_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 3:
                        consumo_tipo = cols[0].get_text(strip=True)
                        tarifa = cols[1].get_text(strip=True)
                        descripcion = cols[2].get_text(strip=True)
                        
                        data.append({
                            'Año': '2024',
                            'MesVerano': '02',
                            'Mes': Month_text,
                            'ConsumoTipo': consumo_tipo,
                            'Tarifa': tarifa,
                            'Descripcion': descripcion
                        })
        except (StaleElementReferenceException, TimeoutException) as e:
            print(f'Error encontrado: {e}. Reintentando la selección para año, mes de verano y mes {Month_text}.')
            time.sleep(5)
    
    file_name = f"prueba.json"
    file_path = os.path.join(output_dir, file_name)
    
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    driver.quit()

Tarifas_JsonData()
