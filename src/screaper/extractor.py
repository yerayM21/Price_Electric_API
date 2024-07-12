import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL = 'https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRECasa/Casa.aspx'
req = requests.get(URL)
soup = BeautifulSoup(req.text,'lxml')

div = soup.find('div',{'class':'col-xs-12'})
links = div.find_all('a')

for link in links:
    name = 'Tarifa '+link.text.strip()  # .strip() para eliminar espacios en blanco
    href = link['href']
    full_url = urljoin(URL, href)  # Combinar URL base con URL relativa
    print(f'Nombre: {name}, URL: {full_url}')
    
