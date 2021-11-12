import axios from "axios";
import cheerio from "cheerio";
import { join, dirname } from "path";
import { Low, JSONFile } from "lowdb";
import { fileURLToPath } from "url";
import { v4 as uuid } from "uuid";

const __dirname = dirname(fileURLToPath(import.meta.url));

const file = join(__dirname, "db.json");
const adapter = new JSONFile(file);
const db = new Low(adapter);

async function write(name, imgUri) {
    // Use JSON file for storage

    // Read data from JSON file, this will set db.data content
    await db.read();

    // You can also use this syntax if you prefer
    const { products } = db.data;
    products.push({
        id: uuid(),
        name,
        img: imgUri,
    });

    // Write db.data content to db.json
    await db.write();
}

axios
    .get(
        "https://www2.hm.com/sv_se/herr/produkter/se-alla.html?sort=stock&image-size=small&image=stillLife&offset=0&page-size=2000"
    )
    .then(async (res) => {
        const $ = cheerio.load(res.data);
        // Read data from JSON file, this will set db.data content
        await db.read();

        const { products } = db.data;

        console.log($(".item-link img").length);

        for (const e of $(".item-link img")) {
            products.push({
                id: uuid(),
                name: e.attribs["alt"],
                img: e.attribs["data-src"],
            });
        }

        await db.write();
    });
