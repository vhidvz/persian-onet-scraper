import re
import time
import json
import hashlib
import requests
from lxml import html
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By

START = "http://demo.idealms.ir/onet/Browse.aspx"


def getLnks(start_point: str = START) -> list:
    try:
        driver = webdriver.Firefox()

        driver.get(start_point)

        links = []
        while True:

            _links = driver.find_elements(by=By.XPATH,
                                          value="/html/body/form/center/div[1]/table/tbody/tr/td[2]/div/div[2]/table/tbody/tr/td[4]/a")
            for el in _links:
                links.append(el.get_attribute('href'))
            _next = driver.find_elements(by=By.XPATH,
                                         value="//following::td/span/../following-sibling::td[1]/a")

            if _next == []:
                break
            else:
                _next = _next[0].get_attribute('href')

            driver.execute_script(_next)
            time.sleep(3)

    finally:
        driver.quit()

    return links


def getContent(tree, url: str) -> list or dict:
    _id = tree.xpath('./table')[0]
    _fb = tree.cssselect('#'+_id.attrib['id'].replace('dlst', 'rbl'))

    if len(_fb) > 0:  # Has A Bug ### Needs Dynamic Web Scraping
        results = {}

        ### Must Be For All Label ###
        lbl = _fb[0].xpath('.//label/text()')[0]
        results.update({lbl: []})

        tdi = _id.xpath('.//tr/td/span[1]/text()')
        tdd = _id.xpath('.//tr/td/span[2]/text()')
        for index, description in zip(tdi, tdd):
            results[lbl].append((index, description))
    else:
        results = []
        if not _id.attrib['id'] == 'MainContent_dlstJobZone':
            tdi = _id.xpath('.//tr/td/span[1]//text()')
            tdd = _id.xpath('.//tr/td/span[2]/text()')
        else:
            tdi = _id.xpath('.//tr/td[1]/text()')
            i = 0
            while i < len(tdi):
                tdi[i] = re.sub(r'/(\\r|\\n|(  ))+/g', '', tdi[i]).strip()
                if tdi[i] == '':
                    del tdi[i]
                else:
                    i += 1
            tdd = _id.xpath('.//tr/td[2]/span/text()')
        for index, description in zip(tdi, tdd):
            results.append((index, description))

    return results


def getInformation(url: str) -> dict:
    page = requests.get(url)
    page.raise_for_status()

    parser = html.HTMLParser(encoding='utf-8')
    tree = html.fromstring(page.content, parser=parser)

    contents = {}
    contents.update({'title': tree.cssselect('#MainContent_lblTitle')[0].text})
    contents.update({'description': tree.cssselect(
        '#MainContent_lblDescription')[0].text})
    contents.update({'subjects': []})
    for content in tree.xpath('/html/body/form/center/div[1]/table//tr/td/div/div/div/div'):
        contents['subjects'].append({
            'title': content.cssselect('.SubTitleBar')[0].text,
            'content': getContent(content, url),
        })

    return contents


if __name__ == "__main__":
    # links = getLnks()

    import _pickle

    # with open('links.pkl', 'wb') as f:
    #     _pickle.dump(links, f)

    with open('links.pkl', 'rb') as f:
        links = _pickle.load(f)

    for url in tqdm(links):
        info = getInformation(url)
        f_name = hashlib.sha1(
            (info['title']+info['description']).encode()).hexdigest()
        with open('./jobs/'+f_name+'.json', 'wt', encoding='utf8') as f:
            f.write(json.dumps(info, ensure_ascii=False, indent=4))
