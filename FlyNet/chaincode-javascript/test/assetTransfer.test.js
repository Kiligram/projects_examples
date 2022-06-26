/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
*/

'use strict';
const sinon = require('sinon');
const chai = require('chai');
const sinonChai = require('sinon-chai');
const expect = chai.expect;

const { Context } = require('fabric-contract-api');
const { ChaincodeStub, ClientIdentity } = require('fabric-shim');

const AssetTransfer = require('../lib/assetTransfer.js');

let assert = sinon.assert;
chai.use(sinonChai);

describe('Asset Transfer Events Tests', () => {
	let transactionContext, chaincodeStub, clientIdentity, flight;

    transactionContext = new Context();

    chaincodeStub = sinon.createStubInstance(ChaincodeStub);
    transactionContext.setChaincodeStub(chaincodeStub);

    clientIdentity = sinon.createStubInstance(ClientIdentity);
    transactionContext.clientIdentity = clientIdentity;

    chaincodeStub.putState.callsFake((key, value) => {
        if (!chaincodeStub.states) {
            chaincodeStub.states = {};
        }
        chaincodeStub.states[key] = value;
    });

    chaincodeStub.getState.callsFake(async (key) => {
        let ret;
        if (chaincodeStub.states) {
            ret = chaincodeStub.states[key];
        }
        return Promise.resolve(ret);
    });

    chaincodeStub.deleteState.callsFake(async (key) => {
        if (chaincodeStub.states) {
            delete chaincodeStub.states[key];
        }
        return Promise.resolve(key);
    });

    chaincodeStub.getStateByRange.callsFake(async () => {
        function* internalGetStateByRange() {
            if (chaincodeStub.states) {
                // Shallow copy
                const copied = Object.assign({}, chaincodeStub.states);

                for (let key in copied) {
                    yield {value: copied[key]};
                }
            }
        }

        return Promise.resolve(internalGetStateByRange());
    });

    flight = {
        flightNr: "EC0",
        flyFrom: "TXD",
        flyTo: "BTS",
        dateTime: "05032021-1034",
        availablePlaces: 5,   // number of all available seats
        seats: ["free", "free", "free", "free", "free"] 
    };

    let assetTransfer = new AssetTransfer();
	describe('Test createFlight', () => {
		it('should return error on createFlight (create flight by GladlyAbroad)', async () => {
            transactionContext.clientIdentity.getMSPID.returns("Org3MSP");
			try {
				await assetTransfer.createFlight(transactionContext, "TXD", "BTS", "05032021-1034", "5");
				assert.fail('createFlight should have failed');
			} catch(err) {
				expect(err.message).to.equal('Flight can be created only by airline!');
			}
		});

		it('should return success on createFlight', async () => {
			transactionContext.clientIdentity.getMSPID.returns("Org1MSP");

			await assetTransfer.createFlight(transactionContext, flight.flyFrom, flight.flyTo, flight.dateTime, flight.availablePlaces);

			let ret = JSON.parse((await chaincodeStub.getState(flight.flightNr)).toString());
			expect(ret).to.eql(flight);
		});
	});

	describe('Test reserveSeats', () => {
		it('should return success on reserveSeats', async () => {
            transactionContext.clientIdentity.getMSPID.returns("Org3MSP");

            let reservation = {
                reservationNr: "R0",
                customerNames: ["Andrii", "Sergii"],
                customerEmail: "example@gmail.com",
                flightNr: "EC0",
                nrOfSeats: 2,
                status: "pending"
            };

            await assetTransfer.reserveSeats(transactionContext, reservation.flightNr, reservation.nrOfSeats, JSON.stringify(reservation.customerNames), reservation.customerEmail);
            let ret = JSON.parse((await chaincodeStub.getState(reservation.reservationNr)).toString());
            //console.log(JSON.parse((await assetTransfer.GetAllAssets(transactionContext))));
            expect(ret).to.eql(reservation);
		});
	});

	describe('Test bookSeats', () => {
		it('should return success on bookSeats', async () => {
			transactionContext.clientIdentity.getMSPID.returns("Org1MSP");
            await assetTransfer.bookSeats(transactionContext, "R0");
            
            let ret = JSON.parse((await chaincodeStub.getState("R0")).toString());
            expect(ret.status).to.eql('completed');
		});
    });

	describe('Test checkIn', () => {
		it('should return success on checkIn', async () => {
			transactionContext.clientIdentity.getMSPID.returns("Org3MSP");
            let passports = [{name: "Andrii", passport: "OP123456"}, {name: "Sergii", passport: "PA123456"}];
            let seats = [0, '4']
            await assetTransfer.checkIn(transactionContext, "R0", JSON.stringify(passports), JSON.stringify(seats));
            
            let ret = JSON.parse((await chaincodeStub.getState("R0")).toString());
            //console.log(JSON.parse((await assetTransfer.GetAllAssets(transactionContext))));
            expect(ret.status).to.eql('Checked-In');
		});
    });

    describe('Check the whole ledger content', () => {
		it('Check the whole ledger content', async () => {          
            let ret = JSON.parse((await assetTransfer.GetAllAssets(transactionContext)));

            let right_res = [
                {
                  flightNr: 'EC0',
                  flyFrom: 'TXD',
                  flyTo: 'BTS',
                  dateTime: '05032021-1034',
                  availablePlaces: 3,
                  seats: [ 'Andrii/OP123456', 'free', 'free', 'free', 'Sergii/PA123456' ]
                },
                {
                  reservationNr: 'R0',
                  customerNames: [ 'Andrii', 'Sergii' ],
                  customerEmail: 'example@gmail.com',
                  flightNr: 'EC0',
                  nrOfSeats: 2,
                  status: 'Checked-In'
                }
            ]

            expect(ret).to.eql(right_res);
		});
    });
});
