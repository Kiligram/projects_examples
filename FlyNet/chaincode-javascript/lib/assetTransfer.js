/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

'use strict';

// Deterministic JSON.stringify()
const stringify  = require('json-stringify-deterministic');
const sortKeysRecursive  = require('sort-keys-recursive');
const { Contract } = require('fabric-contract-api');

class AssetTransfer extends Contract {

    async createFlight(ctx, flyFrom, flyTo, dateTime, availablePlaces){
        const MSPid = ctx.clientIdentity.getMSPID();
        let airline;
        
        availablePlaces = parseInt(availablePlaces);

        if (MSPid == "Org1MSP"){
            airline = "EC"
        }
        else if (MSPid == "Org2MSP"){
            airline = "BS"
        }
        else{
            throw new Error(`Flight can be created only by airline!`);
        }
        
        let flights_num = JSON.parse(await this.getAllFlights(ctx)).length;

        let flightId = airline + stringify(flights_num);

        let available_seats = [];
        for (var i = 0; i < availablePlaces; i++) {
            available_seats.push("free");
        }

        let flight = {
            flightNr: flightId,
            flyFrom: flyFrom,
            flyTo: flyTo,
            dateTime: dateTime,
            availablePlaces: availablePlaces,   // number of all available seats
            seats: available_seats              // list of all seats
        };

        // Buffer.from to convert string to bytes
        await ctx.stub.putState(flightId, Buffer.from(JSON.stringify(flight)));

        return JSON.stringify("Flight " + flight.flightNr + " was created");
    }

    async getAllFlights(ctx) {
        const allResults = [];
        // range query with empty string for startKey and endKey does an open-ended query of all assets in the chaincode namespace.
        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
                if(record.flyFrom){
                    allResults.push(record);
                }
            } catch (err) {
                console.log(err);
                record = strValue;
            }
            result = await iterator.next();
        }
        return JSON.stringify(allResults);
    }

    // getFlight returns the asset stored in the world state with given id.
    async getFlight(ctx, id) {
        const assetJSON = await ctx.stub.getState(id); // get the asset from chaincode state
        if (!assetJSON || assetJSON.length === 0) {
            throw new Error(`The flight ${id} does not exist`);
        }
        return assetJSON.toString();
    }

    async getAllReservations(ctx) {
        const allResults = [];
        // range query with empty string for startKey and endKey does an open-ended query of all assets in the chaincode namespace.
        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
                if(record.customerEmail){
                    allResults.push(record);
                }
            } catch (err) {
                console.log(err);
                record = strValue;
            }
            result = await iterator.next();
        }
        return JSON.stringify(allResults);
    }

    // customerNames must always be array in string format!!! Even if there is only one customer
    // to convert array to string use: JSON.stringify(array);
    async reserveSeats(ctx, flightNr, seatNum, customerNames, customerEmail){
        if(ctx.clientIdentity.getMSPID() != "Org3MSP"){
            throw new Error(`Seats can be reserved only by travel agency!`);
        }

        seatNum = parseInt(seatNum);
        customerNames = JSON.parse(customerNames)
        if(seatNum != customerNames.length){
            throw new Error("Number of customers has to be the same as number of seats!");
        }

        let allReservs = JSON.parse(await this.getAllReservations(ctx)).length;

        let rezervNum = "R" + stringify(allReservs);

        let rezervation = {
            reservationNr: rezervNum,
            customerNames: customerNames,
            customerEmail: customerEmail,
            flightNr: flightNr,
            nrOfSeats: seatNum,
            status: "pending"
        };

        await ctx.stub.putState(rezervNum, Buffer.from(JSON.stringify(rezervation)));
        return JSON.stringify("Rezervation " + rezervNum + " was created");
    }

    async bookSeats(ctx, reservationNr){
        const MSPid = ctx.clientIdentity.getMSPID();

        if(MSPid != "Org1MSP" && MSPid != "Org2MSP"){
            throw new Error(`Seats can be booked only by airlines!`);
        }

        if(!await this.AssetExists(ctx, reservationNr)){ // may cause problems TODO!!
            throw new Error("Reservation " + reservationNr + " does not exist");
        }

        var reservation = JSON.parse(await this.ReadAsset(ctx, reservationNr));

        if(!await this.AssetExists(ctx, reservation.flightNr)){ // may cause problems TODO!!
            throw new Error("Flight " + reservation.flightNr + " does not exist");
        }

        var flight = JSON.parse(await this.ReadAsset(ctx, reservation.flightNr));

        if(flight.flightNr[0] == 'E' && MSPid != "Org1MSP"){
            throw new Error("Only airline that created this fly can book the seats!");
        }

        if(flight.flightNr[0] == 'B' && MSPid != "Org2MSP"){
            throw new Error("Only airline that created this fly can book the seats!");
        }

        if (reservation.status == "pending" && flight.availablePlaces >= reservation.nrOfSeats){
            flight.availablePlaces -= reservation.nrOfSeats;
            reservation.status = "completed";
            await ctx.stub.putState(reservationNr, Buffer.from(JSON.stringify(reservation)));
            await ctx.stub.putState(reservation.flightNr, Buffer.from(JSON.stringify(flight)));
        }
        else {
            if(reservation.status != "pending")
                throw new Error("Seats have been already booked!");
            if(flight.availablePlaces < reservation.nrOfSeats)
                throw new Error("Not enough seats!");
        }

        return JSON.stringify("Seats were successfully booked!");
    }

    // passportIDs and seats must always be arrays in string format!!! Even if there is only one element in array
    // to convert array to string use: JSON.stringify(array);
    // seats is an array with seat numers. Seat numbers can be from 0 to (allSeatsInFlight - 1). 
    // For example, there is a flight with total available 150 seats. In this case array seats can contain numbers from 0 to 149.
    async checkIn(ctx, reservationNr, passportIDs, seats){
        if(ctx.clientIdentity.getMSPID() != "Org3MSP"){
            throw new Error(`Seats can be reserved only by travel agency or customer!`);
        }

        if(!await this.AssetExists(ctx, reservationNr)){ // may cause problems TODO!!
            throw new Error("Reservation " + reservationNr + " does not exist");
        }

        var reservation = JSON.parse(await this.ReadAsset(ctx, reservationNr));

        if (reservation.status != "completed"){
            throw new Error("Reservation " + reservationNr + " has been checked-in or has not been booked yet!");
        }

        var flight = JSON.parse(await this.ReadAsset(ctx, reservation.flightNr));

        // passportIDs format  -> [{name: "Andrej Andrejev", passport: "OP123456"}, {name: "Bohus Bohus", passport: "PA123456"}]
        const parsedPassports = JSON.parse(passportIDs);

        const parsedSeats = JSON.parse(seats);

        if(reservation.seatNum < parsedPassports.length){
            throw new Error("Number of passports has to be the same or less from number of customers in the reservation!");
        }

        function isNameInReservation(cust_name){
            for (var i = 0; i < reservation.customerNames.length; i++) {
                if(reservation.customerNames[i] == cust_name){
                    return true;
                }
            }
            return false;
        }

        for (var i = 0; i < parsedPassports.length; i++) {
            if(isNameInReservation(parsedPassports[i].name)){
                if(flight.seats[parsedSeats[i]] == "free"){
                    flight.seats[parsedSeats[i]] =  parsedPassports[i].name + '/' + parsedPassports[i].passport;
                }
                else{
                    throw new Error("Seat " + parsedSeats[i] + " has already been taken!");
                }
            }
            else{
                throw new Error("No such name in reservation!");
            }
        }

        let tickets = [];
        for (var i = 0; i < parsedPassports.length; i++) {
            const ticket = {
                flightNr: reservation.flightNr,
                dateTime: flight.dateTime,
                seat: parsedSeats[i],
                flyFrom: flight.flyFrom,
                flyTo: flight.flyTo,
                reservationNr: reservationNr,
                passengerName: parsedPassports[i].name,
                passportId: parsedPassports[i].passport
            };
            tickets.push(ticket);
        }

        reservation.status = "Checked-In";
        await ctx.stub.putState(reservation.reservationNr, Buffer.from(JSON.stringify(reservation)));
        await ctx.stub.putState(flight.flightNr, Buffer.from(JSON.stringify(flight)));

        return "Tickets were successfuly created! -> Tickets: " + JSON.stringify(tickets);
    }

    // ReadAsset returns the asset stored in the world state with given id.
    async testF(ctx) {
        return JSON.stringify(ctx.clientIdentity.getMSPID());
    }

    // ReadAsset returns the asset stored in the world state with given id.
    async ReadAsset(ctx, id) {
        const assetJSON = await ctx.stub.getState(id); // get the asset from chaincode state
        if (!assetJSON || assetJSON.length === 0) {
            throw new Error(`The asset ${id} does not exist`);
        }
        return assetJSON.toString();
    }

    // AssetExists returns true when asset with given ID exists in world state.
    async AssetExists(ctx, id) {
        const assetJSON = await ctx.stub.getState(id);
        return assetJSON && assetJSON.length > 0;
    }

    // GetAllAssets returns all assets found in the world state.
    async GetAllAssets(ctx) {
        const allResults = [];
        // range query with empty string for startKey and endKey does an open-ended query of all assets in the chaincode namespace.
        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
            } catch (err) {
                console.log(err);
                record = strValue;
            }
            allResults.push(record);
            result = await iterator.next();
        }
        return JSON.stringify(allResults);
    }
}

module.exports = AssetTransfer;
