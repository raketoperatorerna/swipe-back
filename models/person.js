import mongoose from 'mongoose';

const personSchema = new mongoose.Schema({
    person_id : {
	type: String,
	requires: true
    },
    name : {
	type: String,
	required: true
    }
}, { timestamps: true })

export const Person = mongoose.model('Person', personSchema)
