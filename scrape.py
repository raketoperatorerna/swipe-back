import requests
from bs4 import BeautifulSoup
import os

class Scraper():
    """Base class for scrapers."""

    def __init__(self, url: str, folder: str):
        self.url = url
        self.folder = folder

        self.headers = {
            "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }

        

    def get_images(self):
        path = os.path.join(os.getcwd(), self.folder)
        try:
            os.mkdir(path)
        except:
            pass
        r = requests.get(self.url, headers = self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        garments = soup.find("ul", attrs = {"class" : "products-listing small"})
        images = garments.find_all("img")   
        for image in images:
            name = image['alt']
            link = image['data-src']
            with open(path + "/" + name.replace(' ', '-').replace('/', '') + '.jpg', 'wb') as f:
                im = requests.get("https:" + link, headers = self.headers)
                f.write(im.content)
                print('Writing: ', name)

    def upload_to_cloud(self,)


class HMScraper(Scraper):
    """H&M Scraper."""

    def __init__(self, url, folder):
        super(HMScraper, self).__init__(url, folder)

    def get_images(self):
        return super(HMScraper, self).get_images()

