import time
import urllib

import requests
import boto3
from bs4 import BeautifulSoup

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('catpol_cdep_initiatives')


def scrape(event: dict, context):

    initiatives = []
    for year in event["years"]:
        url = "http://www.cdep.ro/pls/proiecte/upl_pck2015.lista?cam=2&anp={year}".format(year=year)
        now = int(time.time())
        response = requests.get(url)
        bs = BeautifulSoup(response.content)
        table_body = bs.select_one("#olddiv > div.grup-parlamentar-list.grupuri-parlamentare-list tbody")

        for tr in table_body.select("tr"):
            d = dict()
            d["url"] = urllib.parse.urljoin(url, tr.select("td")[1].a.attrs["href"])
            d["year"] = year
            d["updated"] = now
            if tr.select("td")[1].a.string is not None:
                d["number"] = tr.select("td")[1].a.string.strip().upper()
            if tr.select("td")[2].text is not None:
                d["tile"] = tr.select("td")[2].text.strip()
            initiatives.append(d)
            table.put_item(d)

    return initiatives


if __name__ == "__main__":
    for i in scrape({"years": [2017]}, None):
        print(i)
