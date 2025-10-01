const {PrimaryService} = require('bleno');
const MeasurementCharacteristic = require('./characteristic')

module.exports = function makeService(serviceUuid, charUuid){
    return new PrimaryService({
        uuid: serviceUuid, 
        characteristics:[new MeasurementCharacteristic({uuid: charUuid})]
    });
};