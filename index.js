import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import {
    S3Client,
    GetObjectCommand,
    ListObjectsCommand
} from "@aws-sdk/client-s3";

import dotenv from 'dotenv';
import express from "express";
import mongoose from 'mongoose';

import * as swipe from './models/swipe.js';
import * as person from './models/person.js';
import * as product from './models/product.js';

const app = express();

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

dotenv.config();

// Connect to mongodb
mongoose.connect(process.env.dbURL)
	.then(() => {console.log('connected'); app.listen(process.env.PORT);})
	.catch((err) => console.log(err));

// Connect to s3
const client = new S3Client({ region: "eu-north-1" });

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

async function getImages() {

    var params = { Bucket: "tfc-garments", Prefix: "2" };
    const command = new ListObjectsCommand(params);
    return getSignedUrl(client, command, { expiresIn: 3600 });
}

app.get("/getimages", async function(req, res, next) {
    const imgsUrl = await getImages();
    res.send(imgsUrl)
});

async function getImage(key) {
    var params = { Bucket: "tfc-garments", Key: key };
    const command = new GetObjectCommand(params);
    return getSignedUrl(client, command, { expiresIn: 3600 });
}

app.get("/getimage/:key", async function(req, res, next) {
    const imgUrl = await getImage(req.params.key);
    res.send(imgUrl)
});

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
