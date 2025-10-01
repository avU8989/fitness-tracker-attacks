const {Characteristic, Descriptor} = require('bleno');

class HeartRateMeasurementCharacteristic extends Characteristic{
    constructor({uuid}){
        super({
            uuid,
            properties: ['notify', 'read'],
            descriptors: [new Descriptor({uuid: 2901, value: 'Heart Rate Measurement (lab)'})]
        });

        this.intervalMs = 500;
        this.seq = 0;
        this.hr = 80;
        this.dir = +1;
        this.timer = null;
    }

    _payload(){

    }

    onReadRequest(offset, callback){

    }

    onSubscribe(){

    }

    onUnsubscribe(){
        
    }
}