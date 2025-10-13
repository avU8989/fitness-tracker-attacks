const { Characteristic, Descriptor } = require('@abandonware/bleno');
const fs = require('fs');

const MAX_HEARTRATE = 250;
const MIN_HEARTRATE = 70;
const MAX_HEARTRATE_RAMP = 160;
const MIN_HEARTRATE_RAMP = 40;
const logPath = './logs/peripheral_sent.csv';

//does logs dir exist
fs.mkdirSync('./logs', { recursive: true });

const logStream = fs.createWriteStream(logPath, { flags: 'a' });

try {
    if (fs.statSync(logPath).size === 0) {
        logStream.write('seq,send_ts_ms,hr,payload_hex\n');
    }
} catch (e) {
    logStream.write('seq,send_ts_ms,hr,payload_hex\n');
}

class HeartRateMeasurementCharacteristic extends Characteristic {
    constructor({ uuid }) {
        super({
            uuid,
            properties: ['notify', 'read', 'write'],
            descriptors: [new Descriptor({ uuid: '2901', value: 'Heart Rate Measurement (lab)' })]
        });

        this.intervalMs = 500;
        this.seq = 0;
        this.hr = 200;
        this.dir = +1;
        this.timer = null;
        this.manualHr = null;
    }

    _payload() {
        //standard HR: Flags= 0x00, HR(8-bit)
        let hrNow;
        if (this.manualHr != null) {
            hrNow = this.manualHr;
        } else {
            if (this.hr >= MAX_HEARTRATE_RAMP) {
                this.dir = -1;
            }

            if (this.hr <= MIN_HEARTRATE_RAMP) {
                this.dir = +1;
            }

            this.hr += 3 * this.dir;

            const heartRate = Math.max(MIN_HEARTRATE, Math.min(MAX_HEARTRATE, Math.round(this.hr))) & 0xff;
            this.seq++;
            return Buffer.from([0x00, heartRate]);
        }
    }

    //will perform when the read is performed on the characteristic
    onReadRequest(offset, callback) {
        //dont support partial/long reads
        if (offset) {
            return callback(this.RESULT_ATTR_NOT_LONG);
        }

        console.log('Heart Measurement Characteristic onReadRequest');
        callback(this.RESULT_SUCCESS, this._payload());
    }

    onWriteRequest(data, offset, withoutResponse, callback) {
        if (offset) {
            return callback(this.RESULT_ATTR_NOT_LONG);
        }

        console.log('Heart Measurement Characteristic onWriteRequest');

        try {
            let val;
            if (data.length === 1) {
                //data is a 8Bit Heart Rate
                val = data.readUInt8(0);
            } else {
                //data is ASCII "120"
                const formattedValueInText = data.toString('utf-8').trim();
                const formattedValueInNumber = Number(formattedValueInText);
                if (Number.isFinite(formattedValueInNumber)) {
                    val = formattedValueInNumber;
                }
            }

            this.manualHr = Math.max(MIN_HEARTRATE, Math.min(MAX_HEARTRATE, Math.round(val)));

            callback(this.RESULT_SUCCESS);
        } catch (err) {
            console.error(err);
            callback(this.RESULT_UNLIKELY_ERROR);
        }
    }

    onSubscribe(maxValueSize, updateValueCallback) {
        console.log('Heart Measurement Characteristic onSubscribe');
        if (this.timer) {
            clearInterval(this.timer);
        }

        this.timer = setInterval(() => {
            const payload = this._payload();
            updateValueCallback(payload);

            // Logging
            const ts = Date.now();
            const hr = this.hr;
            const hex = payload.toString('hex');

            logStream.write(`${this.seq},${ts},${hr},${hex}\n`);
            console.log(`[send] seq=${this.seq} ts=${ts} hr=${hr} hex=${hex}`);
        }, this.intervalMs);
    }

    onUnsubscribe() {
        console.log('Heart Measurement Characteristic onUnsubcribe');
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }

        this._updateValueCallback = null;
    }
}

module.exports = HeartRateMeasurementCharacteristic;
