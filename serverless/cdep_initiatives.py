import requests
from bs4 import BeautifulSoup


def scrape(event: dict, context):
    response = requests.get("http://www.cdep.ro/pls/proiecte/upl_pck2015.lista?cam=2&anp=2017")
    bs = BeautifulSoup(response.content)
    return "Hello, World!"
