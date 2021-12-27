import os
import requests

from dotenv import load_dotenv
from bs4 import BeautifulSoup


class Scraper():
    """Base class for scrapers."""

    def __init__(self, url: str, folder: str):
        self.url = url
        self.folder = folder

        load_dotenv()

        self.headers = {
            "User-agent": os.getenv("USER-AGENT")  # noqa: E501
        }

    def get_images(self):
        path = os.path.join(os.getcwd(), self.folder)
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        r = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        garments = soup.find("ul", attrs={"class": "products-listing small"})
        images = garments.find_all("img")
        for image in images:
            name = image['alt']
            link = image['data-src']
            with open(path + "/" + name.replace(' ', '-').replace('/', '') + '.jpg', 'wb') as f:  # noqa: E501
                im = requests.get("https:" + link, headers=self.headers)
                f.write(im.content)
                print('Writing: ', name)


class HMScraper(Scraper):
    """H&M Scraper."""

    def __init__(self, url, folder):
        super(HMScraper, self).__init__(url, folder)

    def get_images(self):
        return super(HMScraper, self).get_images()


if __name__ == "__main__":
    sc = HMScraper(
        url="https://www2.hm.com/sv_se/herr/produkter/se-alla.html?sort=stock&image-size=small&image=stillLife&offset=0&page-size=100",  # noqa: E501
        folder="hm"
    )
    sc.get_images()
