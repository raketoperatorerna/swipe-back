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
import * as garment from './models/garment.js';

const app = express();

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

dotenv.config();

// Connect to mongodb
mongoose.connect(process.env.MONGODB_URL)
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

function getGarments() {
    const garments = garment.Garment.find({})
    return garments
}

app.get("/getgarments", async function(req, res, next) {
    const garments = await getGarments();
    res.send(garments)
});

app.get("/getrandomgarment", async function(req, res, next) {
    const garments = await getGarments();
    const randomGarmentObject = garments[parseInt(Math.random() * garments.length)]
    res.send(randomGarmentObject)
});

async function getImage(gid, iid) {
    var params = { Bucket: "tfc-garments", Key: `hm/${gid}/${iid}` };
    const command = new GetObjectCommand(params);
    return getSignedUrl(client, command, { expiresIn: 3600 });
}

app.get("/getimage", async function(req, res, next) {
    const imgUrl = await getImage(req.query.gid, req.query.iid);
    res.send(imgUrl)
});

async function getGarmentImages(gid) {
    var params = { Bucket: "tfc-garments", Prefix: `hm/${gid}/` };
    const command = new ListObjectsCommand(params);
    return getSignedUrl(client, command, { expiresIn: 3600 });
}

app.get("/getimageS3", async function(req, res, next) {
    const imgUrls = await getGarmentImages(req.query.gid);
    res.send(imgUrls)
});
