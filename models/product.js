import mongoose from 'mongoose';

const productSchema = new mongoose.Schema({
    product_id : {
	type: String,
	requires: true
    },
    description: {
	type: String,
	required: true
    }
})

export const Product = mongoose.model('Product', productSchema)
