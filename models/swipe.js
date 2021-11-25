import mongoose from 'mongoose';

const swipeSchema = new mongoose.Schema({
    person_name : {
	type: String,
	required: true
    },
    garment_id: {
	type: String,
	required: true
    },    
    action: {
	type: String,
	required: true
    }
}, { timestamps: true })


export const Swipe = mongoose.model('Swipe', swipeSchema);
