import express from "express";
import { join, dirname } from "path";
import { Low, JSONFile } from "lowdb";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const file = join(__dirname, "db.json");
const adapter = new JSONFile(file);
const db = new Low(adapter);

const app = express();

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

async function write(person, c_id, action) {
    // Use JSON file for storage

    // Read data from JSON file, this will set db.data content
    await db.read();

    // You can also use this syntax if you prefer
    const { events } = db.data;
    events.push({
        person: person,
        clothing_id: c_id,
        action: action,
        timestamp: new Date(Date.now()),
    });

    // Write db.data content to db.json
    await db.write();
}

async function getClothing() {
    await db.read();

    // You can also use this syntax if you prefer
    const { products } = db.data;

    return products[parseInt(Math.random() * products.length)];
}

app.post("/event", function (req, res) {
    write(req.body.person, req.body.c_id, req.body.action);
    res.send({ status: "success" });
});

app.get("/get", async function (req, res) {
    const clothing = await getClothing();
    res.send(clothing);
});

app.get("/getdatabase", async function (req, res) {
    await db.read();
    res.send(db.data);
});

app.listen(3002);
