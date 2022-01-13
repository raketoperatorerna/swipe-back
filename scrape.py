
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

from pymongo import MongoClient


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

        self.mdb = MongoClient(os.getenv("MONGODB-URL")).tfc

        self.image_tags = None
        self.garment_urls = None
        self.garments = []

        self.path = os.path.join(os.getcwd(), folder)

    def get_garment_page_urls(self, base_url: str,
                              image_listing_tag: str,
                              url: Optional[str] = None):
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

    def get_garment_info(self, base_url: str,
                         image_listing_tag: str):
        """Gets data about each garment."""
        garment_urls = self.get_garment_page_urls(
            base_url=base_url,
            image_listing_tag=image_listing_tag
        )

        for gurl in garment_urls:
            # Transform step
            self.transform(gurl)

        # Upload image links and garment data to mongo
        self.load_mongo()
        # Upload images to s3
        self.load_s3()

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

    def load_mongo(self):
        """Uploads metadata about images to mongo."""
        self.mdb.garments.insert_many(self.garments)

    def load_s3(self):
        """Push images to cloud."""
        for garment in self.garments:

            gid = garment["garment_id"]
            images = garment["garment_urls"]

            for iid, url in images.items():

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

    def get_garment_page_urls(self, base_url: str, image_listing_tag):
        return super(HMScraper, self).get_garment_page_urls(
            base_url=self.base_url,
            image_listing_tag="products-listing small"
        )

    def get_garment_info(self):
        return super(HMScraper, self).get_garment_info(
            base_url=self.base_url,
            image_listing_tag="products-listing small"
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
            class_="module product-description sticky-wrapper"
        )
        # Product label
        label = garment_page.find(
            "h1",
            class_="primary product-item-headline"
        ).contents[0].replace("\t", "").lstrip()
        # Product price
        price = garment_page.find(
            "div",
            class_="ProductPrice-module--productItemPrice__2i2Hc"   
        ).find("span").contents[0]
        price = int(price.split(",")[0])
        priced = {"price": price, "currency": "SEK"}
        # Product description
        desc = garment_page.find(
            "p",
            class_="pdp-description-text"
        ).contents[0]
        # Main image
        main_img_element = garment_page.find(
            "div",
            class_="product-detail-main-image-container"
        ).find("img")
        main_src = [main_img_element["src"]]
        # Images
        img_elements = (
            garment_page.find_all(
                "img",
                class_="product-detail-thumbnail-image"
            )
        )
        srcs = main_src + [
            x["src"]
            for x
            in img_elements
        ]
        srcs = {uuid4().hex: "https:" + src for src in srcs}
        garment = {
            "garment_id": garment_id,
            "garment_price": priced,
            "garment_label": label,
            "garment_desc": desc,
            "garment_urls": srcs
        }
        self.garments.append(garment)

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
