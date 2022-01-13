
import os
import time
import requests
import tempfile

from typing import Optional

from boto3 import client
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from uuid import uuid4

from selenium import webdriver


class Scraper():
    """Base class for scrapers."""

    def __init__(self, garments_listing_url: str, folder: str):
        self.garments_listing_url = garments_listing_url
        self.folder = folder

        load_dotenv()

        self.headers = {
            "User-agent": os.getenv("USER-AGENT")  # noqa: E501
        }

        self.s3 = client(
            service_name="s3",
            region_name="eu-north-1",
            aws_access_key_id=os.getenv("AWS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_KEY_PASS")
        )

        self.image_tags = None
        self.garment_urls = None
        self.garments = {}

        self.path = os.path.join(os.getcwd(), folder)

    def get_garment_page_urls(self, base_url: str,
                              url: Optional[str] = None,
                              image_listing_tag: str = "products-listing small"): # noqa 3501
        """Scrape page urls."""
        # Fetch image tags
        r = requests.get(self.garments_listing_url, headers=self.headers)
        if r.status_code != 200:
            raise Exception("Request not succesful.")
        garments = BeautifulSoup(r.text, 'html.parser').find(
            "ul",
            attrs={"class": image_listing_tag}
        )
        self.image_tags = garments.find_all("img")

        return [
            base_url + x["href"]
            for x
            in garments.find_all(
                "a",
                attrs={"class": "item-link"}
            )
        ]

    def get_garment_info(self, base_url: str, images_listing_tag: str):
        """Gets data about each garment.

        Meta data such as image urls
        """
        garment_urls = self.get_garment_page_urls(base_url=base_url)

        for gurl in garment_urls:
            # Transform step
            self.transform(gurl)

        self.upload_images_s3()

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

    def upload_data_mongo(self):
        """Uploads metadata about images to mongo"""
        pass

    def upload_images_s3(self):
        """Push images to cloud."""
        for gid in self.garments:

            md = self.garments[gid]
            imgs = md["imgs"]

            for iid, url in imgs.items():

                image = requests.get(url, headers=self.headers).content

                with tempfile.NamedTemporaryFile() as tf:
                    tf.write(image)
                    tf.seek(0)
                    self.s3.upload_file(
                        tf.name,
                        Bucket="tfc-garments",
                        Key=self.folder + "/" + gid + "/" + iid,
                        ExtraArgs={'Metadata': {'garment_id': gid}}
                    )

    def etl(self):
        pass


class HMScraper(Scraper):
    """H&M Scraper."""

    def __init__(self, garments_listing_url: str, folder: str):
        super(HMScraper, self).__init__(garments_listing_url, folder)

        self.base_url = "https://www2.hm.com/"

    def get_images(self):
        return super(HMScraper, self).get_images(base_url=self.base_url)

    def get_garment_info(self):
        return super(HMScraper, self).get_garment_info(
            base_url=self.base_url,
            images_listing_tag="module product-description sticky-wrapper"
        )

    def transform(self, url: str):
        """Transforms the input html to valid load-format."""
        garment_id = uuid4().hex

        driver = webdriver.Chrome(os.getenv("DRIVER_PATH"))
        driver.get(url)
        html = driver.page_source

        # Make sure content is loaded
        time.sleep(1)

        garment_page = BeautifulSoup(html, "html.parser").find(
            "div",
            attrs={"class": "module product-description sticky-wrapper"}
        )
        # Product label
        label_element = garment_page.find(
            "h1",
            attrs={"class": "primary product-item-headline"}
        )
        label = (
            label_element.contents[0]
                         .replace("\t", "")
                         .lstrip()
                         .lower()
                         .replace(" ", "_")
        )
        # Product description
        desc = garment_page.find("p", attrs={"class": "pdp-description-text"})
        # Images
        srcs_html = (
            garment_page.find_all(
                "img",
                attrs={"class": "product-detail-thumbnail-image"}
            )
        )
        srcs = [
            x["src"]
            for x
            in srcs_html
        ]
        imgs_d = {uuid4().hex: "https:" + src for src in srcs}
        meta_data = {
            "label": label,
            "desc": desc.contents[0],
            "imgs": imgs_d
        }
        self.garments[garment_id] = meta_data

        driver.close()


class ZalandoScraper(Scraper):
    """Zalando Scraper"""

    def __init__(self, garments_listing_url: str, folder: str):
        super(ZalandoScraper, self).__init__(garments_listing_url, folder)

    def get_images(self):
        return super(ZalandoScraper, self).get_images()


if __name__ == "__main__":
    # Scrape from H&M
    sc = HMScraper(
        garments_listing_url="https://www2.hm.com/sv_se/herr/produkter/se-alla.html?sort=stock&image-size=small&image=stillLife&offset=0&page-size=2",  # noqa: E501
        folder="hm"
    )
    sc.get_garment_info()
