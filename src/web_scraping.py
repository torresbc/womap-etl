from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import glob
import time


def set_prefs():
    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': 'C:/Users/Bruna/Desktop/TCC/TCC_ETL/src'}
    chrome_options.add_experimental_option('prefs', prefs)
    return chrome_options


def start_browser():
    DRIVER_PATH = 'chromedriver.exe'
    driver = webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=chrome_options)
    driver.get('http://www.ssp.sp.gov.br/transparenciassp/Consulta.aspx')
    return driver


def wait_file_download(dataset):
    while not glob.glob(f'*{dataset}*'):
        time.sleep(1)


def confirm_click(driver, xpath):
    confirm = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    confirm.click()


def selection_data(dataset, dataset_values):
    driver = start_browser()
    confirm_click(driver, f'//*[@id="cphBody_{dataset}"]')

    if dataset_values[1]:
        confirm_click(driver, '//*[@id="cphBody_ExportarBOLink"]')

    wait_file_download(dataset_values[0])
    driver.quit()


def download_file():
    dataset_dict = {'btnHomicicio': ['Homicidio', False],
                    'btnFeminicidio': ['Feminicidio', False],
                    'btnLatrocinio': ['Latrocinio', False],
                    'btnLesaoMorte': ['LCSM', False],
                    'btnFurtoVeiculo': ['(FURTO DE VEÍCULOS)', True],
                    'btnRouboVeiculo': ['(ROUBO DE VEÍCULOS)', True],
                    'btnFurtoCelular': ['(FURTO DE CELULAR)', True],
                    'btnRouboCelular': ['(ROUBO DE CELULAR)', True]}

    for dataset in dataset_dict:
        selection_data(dataset, dataset_dict[dataset])


if __name__ == '__main__':
    #Web Scraping Flow
    chrome_options = set_prefs()
    download_file()


    print('chegou')

