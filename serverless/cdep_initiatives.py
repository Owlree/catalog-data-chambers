import requests
from bs4 import BeautifulSoup


def scrape(event: dict, context):

    initiatives = []
    for year in event["years"]:
        url = "http://www.cdep.ro/pls/proiecte/upl_pck2015.lista?cam=2&anp={year}".format(year=year)
        response = requests.get(url)
        bs = BeautifulSoup(response.content)
        table_body = bs.select_one("#olddiv > div.grup-parlamentar-list.grupuri-parlamentare-list tbody")

        for tr in table_body.select("tr"):
            d = dict()
            d["url"] = tr.select("td")[1].a.attrs["href"]
            if tr.select("td")[1].a.string is not None:
                d["number"] = tr.select("td")[1].a.string.strip()
            if tr.select("td")[2].string is not None:
                d["tile"] = tr.select("td")[2].string.strip()
            d["year"] = year
            initiatives.append(d)

    return {
        "initiatives": initiatives,
        "function_version": context.function_version
    }


if __name__ == "__main__":
    class Context:
        def __init__(self):
            self.function_version = "DemoTest"
    print(scrape({"years": [2015]}, Context()))