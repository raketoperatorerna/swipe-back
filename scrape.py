import os
import sys
import requests
import tempfile

from boto3 import client
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url


class Scraper():
    """Base class for scrapers."""

    def __init__(self, url: str, folder: str):
        self.url = url
        self.folder = folder

        load_dotenv()

        self.headers = {
            "User-agent": os.getenv("USER-AGENT")  # noqa: E501
        }

        self.s3 = client(
            service_name="s3",
            region_name="eu-north-1",
            aws_access_key_id=os.getenv("AWS-KEY-ID"),
            aws_secret_access_key=os.getenv("AWS-KEY-PASS")
        )

        self.image_tags = None

        self.path = os.path.join(os.getcwd(), folder)

    def get_images(self, image_listing_tag: str = "products-listing small"):
        """Scrape images."""
        try:
            os.mkdir(self.path)
        except FileExistsError:
            pass
        # Fetch image tags
        r = requests.get(self.url, headers=self.headers)
        if r.status_code != 200:
            raise Exception("Request not succesful.")
        garments = BeautifulSoup(r.text, 'html.parser').find(
            "ul",
            attrs={"class": image_listing_tag}
        )
        self.image_tags = garments.find_all("img")

    def write_images(self):
        """Write images to disk."""
        for image_tag in self.image_tags:

            name = image_tag['alt']
            link = image_tag['data-src']
            fn = self.path + "/" + name.replace(" ", "-").replace("/", "") + ".jpg" # noqa 3501

            with open(fn, "wb") as f:
                im = requests.get("https:" + link, headers=self.headers)
                f.write(im.content)
                print("Writing: ", name)

    def upload_images_s3(self):
        """Push images to cloud."""
        for image_tag in self.image_tags:

            name = image_tag['alt']
            link = image_tag['data-src']
            image = requests.get("https:" + link, headers=self.headers).content

            with tempfile.NamedTemporaryFile() as tf:
                tf.write(image)
                tf.seek(0)
                self.s3.upload_file(
                    tf.name,
                    Bucket="tfc-garments",
                    Key=name
                )

    def upload_images_cloudinary(self):
        for image_tag in self.image_tags:

            link = image_tag['data-src']
            image = requests.get("https:" + link, headers=self.headers).content

            with tempfile.NamedTemporaryFile() as tf:
                tf.write(image)
                tf.seek(0)
                response = upload(tf.name, tags="hej")

                url, options = cloudinary_url(
                    response['public_id'],
                    format=response['format'],
                    width=200,
                    height=150,
                    crop="fill"
                )


class HMScraper(Scraper):
    """H&M Scraper."""

    def __init__(self, url: str, folder: str):
        super(HMScraper, self).__init__(url, folder)

    def get_images(self):
        return super(HMScraper, self).get_images()


class ZalandoScraper(Scraper):
    """Zalando Scraper"""

    def __init__(self, url: str, folder: str):
        super(ZalandoScraper, self).__init__(url, folder)

    def get_images(self):
        return super(ZalandoScraper, self).get_images()


if __name__ == "__main__":
    # Scrape from H&M
    sc = HMScraper(
        url="https://www2.hm.com/sv_se/herr/produkter/se-alla.html?sort=stock&image-size=small&image=stillLife&offset=0&page-size=10",  # noqa: E501
        folder="hm"
    )
    sc.get_images()
    sc.upload_images_cloudinary()
