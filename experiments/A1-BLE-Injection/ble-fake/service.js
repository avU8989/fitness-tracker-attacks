const { PrimaryService } = require('@abandonware/bleno');
const MeasurementCharacteristic = require('./characteristic')

module.exports = function makeService(serviceUuid, charUuid) {
    return new PrimaryService({
        uuid: serviceUuid,
        characteristics: [new MeasurementCharacteristic({ uuid: charUuid })]
    });
};