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


def GetsUrls():
    url = 'https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRECasa/Casa.aspx'
    req = requests.get(url)
    soup = BeautifulSoup(req.text,'lxml')
    
    div = soup.find('div',{'class':'col-xs-12'})
    links = div.find_all('a')
    
    Urls={}
    
    for link in links:
        name ='Tarifa_'+link.text.strip()
        href = link['href']
        full_url = urljoin(url,href)
        Urls[name] = full_url
    
    return Urls

def Tarifa_1_JsonData():
    link = GetsUrls()
    link =  {key: value for key, value in link.items() if key == 'Tarifa_1'}
    # Configuración del WebDriver
    driver = webdriver.Chrome()
    
    # Crear la carpeta para guardar los archivos JSON
    output_dir = os.path.join('src', 'import', 'tarifas_json')
    os.makedirs(output_dir, exist_ok=True)
    
    for name, url in link.items():
        driver.get(url)
        
        time.sleep(5)
        
        Years_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
        Years_options = {option.get_attribute('value'): option.text for option in Years_select.options if option.get_attribute('value') != '0'}
        
        Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesConsulta'))
        Month_options = {option.get_attribute('value'): option.text for option in Month_select.options if option.get_attribute('value') != '0'}
        
        data = []  # Inicializa el diccionario para cada tarifa
        
        for Year_value, Year_text in Years_options.items():
            data[Year_text] = {}
            
            for Month_value, Month_text in Month_options.items():
                try:
                    # Seleccionar el año
                    Years_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_Fecha_ddAnio'))
                    Years_select.select_by_value(Year_value)
                    
                    # Seleccionar el mes
                    Month_select = Select(driver.find_element(By.ID, 'ContentPlaceHolder1_MesVerano1_ddMesConsulta'))
                    Month_select.select_by_value(Month_value)
                    
                    time.sleep(10)
                    
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    season_table = soup.find('table', {'id': 'ContentPlaceHolder1_TemporadaFV'})
                    
                    if season_table:
                        data[Year_value][Month_value] = {}
                        rows = season_table.find_all('tr')
                        
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) == 3:
                                consumo_tipo = cols[0].get_text(strip=True)
                                tarifa = cols[1].get_text(strip=True)
                                descripcion = cols[2].get_text(strip=True)
                                
                                data[Year_value][Month_value][consumo_tipo] = {
                                    'Tarifa': tarifa,
                                    'descripcion': descripcion
                                }

                except StaleElementReferenceException:
                    print(f"Elemento obsoleto encontrado. Reintentando la selección para año {Year_text} y mes {Month_text}.")
        
        # Guardar los datos en un archivo JSON
        file_name = f"{name.replace(' ', '_')}.json"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    driver.quit()



