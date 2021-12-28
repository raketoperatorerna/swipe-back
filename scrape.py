import os
import requests
import tempfile

from boto3 import resource
from bs4 import BeautifulSoup
from dotenv import load_dotenv


class Scraper():
    """Base class for scrapers."""

    def __init__(self, url: str, folder: str):
        self.url = url
        self.folder = folder

        load_dotenv()

        self.headers = {
            "User-agent": os.getenv("USER-AGENT")  # noqa: E501
        }

        self.s3 = resource(
            service_name="s3",
            region_name="eu-north-1",
            aws_access_key_id=os.getenv("AWS-KEY-ID"),
            aws_secret_access_key=os.getenv("AWS-KEY-PASS")
        )

        self.image_tags = None

        self.path = os.path.join(os.getcwd(), folder)

    def get_images(self):
        """Scrape images."""
        try:
            os.mkdir(self.path)
        except FileExistsError:
            pass
        # Fetch image tags
        r = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        garments = soup.find("ul", attrs={"class": "products-listing small"})
        self.image_tags = garments.find_all("img")

    def write_images(self):
        """Write images to disk."""
        for image_tag in self.image_tags:
            name = image_tag['alt']
            link = image_tag['data-src']
            with open(self.path + "/" + name.replace(' ', '-').replace('/', '') + '.jpg', 'wb') as f:  # noqa: E501
                im = requests.get("https:" + link, headers=self.headers)
                f.write(im.content)
                print('Writing: ', name)

    def upload_images(self):
        """Push images to cloud."""
        # Save each image
        for image_tag in self.image_tags:
            name = image_tag['alt']
            link = image_tag['data-src']
            image = requests.get("https:" + link, headers=self.headers).content

            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(image)
                self.s3.Bucket('tfc-garments').upload_file(
                    Filename=tmp.name,
                    Key=name + ".jpg"
                )


class HMScraper(Scraper):
    """H&M Scraper."""

    def __init__(self, url, folder, ):
        super(HMScraper, self).__init__(url, folder)

    def get_images(self):
        return super(HMScraper, self).get_images()


class ZalandoScraper(Scraper):
    """Zalando Scraper"""

    def __init__(self, url, folder):
        super(ZalandoScraper, self).__init__(url, folder)

    def get_images(self):
        return super(ZalandoScraper, self).get_images()


if __name__ == "__main__":
    # Scrape from H&M
    sc = HMScraper(
        url="https://www2.hm.com/sv_se/herr/produkter/se-alla.html?sort=stock&image-size=small&image=stillLife&offset=0&page-size=52",  # noqa: E501
        folder="hm"
    )
    sc.get_images()
    sc.upload_images()

load_dotenv()
