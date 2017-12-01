import time
import urllib
import re

import requests
import boto3
from bs4 import BeautifulSoup


# dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('catpol_cdep_initiatives')

def get_initiative_dep(url):
    response = requests.get(url)
    bs = BeautifulSoup(response.content)

    initiative = {}
    initiative["url"] = {
        "cdep": url,
        "senat": urllib.parse.urljoin(url, bs.find("td", text="- Senat:").next_sibling.a.attrs["href"])
    }
    initiative["id"] = {
        "cdep": bs.find("td", text="- Camera Deputatilor:").next_sibling.text,
        "senat": bs.find("td", text="- Senat:").next_sibling.text
    }
    initiative["title"] = bs.select_one("#olddiv h4").text.strip()

    initiator = bs.find("td", text="Initiator:").next_sibling
    if initiator.text.strip() == "Guvern":
        initiative["initiator"] = {
            "type": "institution",
            "name": "guvern"
        }
    else:
        initiative["initiator"] = {
            "type": "group",
            "members": []
        }
        for a in initiator.select("a"):
            member = {}
            member["url"] = urllib.parse.urljoin(url, a.attrs["href"])
            o = urllib.parse.urlparse(member["url"])
            cam = int(urllib.parse.parse_qs(o.query)["cam"][0])
            member["camera"] = "senat" if cam == 1 else "cdep"
            member["name"] = a.text.strip()
            initiative["initiator"]["members"].append(member)

    return initiative

def main(event: dict, context):

    initiatives = []
    for year in event["years"]:
        url = "http://www.cdep.ro/pls/proiecte/upl_pck2015.lista?cam=2&anp={year}".format(year=year)
        now = int(time.time())
        response = requests.get(url)
        bs = BeautifulSoup(response.content)
        table_body = bs.select_one("#olddiv > div.grup-parlamentar-list.grupuri-parlamentare-list tbody")

        urls = []
        for tr in table_body.select("tr"):
            url = urllib.parse.urljoin(url, tr.select("td")[1].a.attrs["href"])
            initiative = get_initiative_dep(url)
            print(initiative)



    return initiatives


if __name__ == "__main__":
    main({"years": [2017]}, None)