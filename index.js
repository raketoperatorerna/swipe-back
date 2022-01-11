import { S3 } from "@aws-sdk/client-s3";

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
const s3 = new S3({
    region: 'eu-north-1',
    accessKeyId: process.env.AWS_KEY_ID,
    secretAccessKey: process.env.AWS_KEY_PASS,
}) 

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

app.get("/getimage", function(req, res, next) {
    var params = { Bucket: "tfc-garments", Key: "10-pack mid trunks i bomull" };

    s3.getObject(params, function(err, data) {
	// Handle any error and exit
	if (err)
            return err;
	// No error happened
	// Convert Body from a Buffer to a String
	console.log(data.Body)
	let objectData = data.Body.toString('utf-8'); // Use the encoding necessary
    });
});

