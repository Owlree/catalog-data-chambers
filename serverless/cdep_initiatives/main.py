import time
import urllib

import requests
import boto3
from bs4 import BeautifulSoup


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('catpol_cdep_initiatives')

class Fields:
    SENAT = "- Senat:"
    CDEP = "- Camera Deputatilor:"
    INITIATORS = "Initiator:"
    DECISION = "Camera decizionala:"

def get_field_url(bs, field, url, default=None):
    field = bs.find("td", text=field)
    if field is not None:
        return urllib.parse.urljoin(url, field.next_sibling.a.attrs["href"])
    return default

def get_field(bs, field, default=None):
    field = bs.find("td", text=field)
    if field is not None:
        return field.next_sibling.text.strip()
    return default

def transform_registration_number(s):
    return s[:s.find("/") + 1] + s[-4:]

def get_initiative_dep(url):
    response = requests.get(url)
    bs = BeautifulSoup(response.content)

    o = urllib.parse.urlparse(url)
    page_type = int(urllib.parse.parse_qs(o.query)["cam"][0])

    # initialize empty initiative
    initiative = dict()

    # create and store unique id
    cdep_field = get_field(bs, Fields.CDEP)
    cdep_registration_number = "0/0"
    if cdep_field is not None:
        cdep_registration_number = transform_registration_number(cdep_field)
    senat_field = get_field(bs, Fields.SENAT)
    senat_registration_number = "0/0"
    if senat_field is not None:
        senat_registration_number = transform_registration_number(senat_field)
    initiative["id"] = "{senat}+{cdep}".format(senat=senat_registration_number, cdep=cdep_registration_number)

    # store initiative urls for each camera
    initiative["url"] = dict()
    if page_type == 1:
        url_cdep = get_field_url(bs, Fields.CDEP, url)
        if url_cdep is not None:
            initiative["url"]["cdep"] = url_cdep
        initiative["url"]["senat"] =  url
    elif page_type == 2:
        initiative["url"]["cdep"] =  url
        url_senat = get_field_url(bs, Fields.SENAT, url)
        if url_senat is not None:
            initiative["url"]["senat"] = url_senat

    # store title
    initiative["title"] = bs.select_one("#olddiv h4").text.strip()

    # store decision camera
    initiative["decision"] = get_field(bs, Fields.DECISION).lower()

    # store initiators
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
            member["name"] = a.text.strip().replace("\xa0", " ")
            initiative["initiator"]["members"].append(member)

    return initiative

def main(event: dict, context):

    count = 0
    for year in event["years"]:
        count += 1
        for camera in event["cameras"]:
            url = "http://www.cdep.ro/pls/proiecte/upl_pck2015.lista?cam={camera}&anp={year}".format(camera=camera, year=year)
            now = int(time.time())
            response = requests.get(url)
            bs = BeautifulSoup(response.content)
            table_body = bs.select_one("#olddiv > div.grup-parlamentar-list.grupuri-parlamentare-list tbody")

            urls = []
            for tr in table_body.select("tr"):
                url = urllib.parse.urljoin(url, tr.select("td")[1].a.attrs["href"])
                initiative = get_initiative_dep(url)
                table.put_item(Item=initiative)
    return count


if __name__ == "__main__":
    main({"years": [2017], "cameras": [2]}, None)