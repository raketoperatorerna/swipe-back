import dotenv from 'dotenv';
import express from "express";
import mongoose from 'mongoose';

import { join, dirname } from "path";
import { Low, JSONFile } from "lowdb";
import { fileURLToPath } from "url";

import * as swipe from './models/swipe.js';
import * as person from './models/person.js';
import * as product from './models/product.js';

const app = express();

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

dotenv.config();
mongoose.connect(process.env.dbURL)
    .then(() => {console.log('connected'); app.listen(process.env.PORT);})
    .catch((err) => console.log(err));

app.post('/event', (req, res) => {
    const s = swipe.Swipe({
	person_name: req.body.person_name,
	garment_id: req.body.garment_id,
	action: req.body.action
    })
    s.save().then((result) => {
	res.send(result)
    }).catch((err) => console.log(err))
})

async function getClothing() {
    await db.read();

    // You can also use this syntax if you prefer
    const { products } = db.data;

    return products[parseInt(Math.random() * products.length)];
}

app.get("/get", async function (req, res) {
    const clothing = await getClothing();
    res.send(clothing);
});

app.get("/getdatabase", async function (req, res) {
    await db.read();
    res.send(db.data);
});
