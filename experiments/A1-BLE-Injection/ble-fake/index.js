//lab-only ble peripheral to spoof a smartwatch and inject HR/Spo2 metrics

const bleno = require('bleno');
const yargs = require('yargs/yargs');
const {hideBin} = require('yargs/helpers');
const makeService = require('./service');
const { argv } = require('process');

//parse cli flags
const argv = yargs(hideBin(process.argv))
  .option('name', {type: 'string', default: 'Heart Rate', desc: 'Advertised device name'})
  .option('service', {type: 'string', default: '180d', desc: 'Service UUID (180d for Heart Rate'}) //Primary Service
  .option('char', {type: 'string', default: '2a37', desc: 'Characteristic UUID (2a37 for Heart Measurement)'}) //Characteristics
  .option('mode', {choices:['standard', 'custom'], default: 'standard', desc: 'Payload format'})
  .option('pattern', {choices: ['ramp', 'sine', 'fixed'], desc: 'Heart Rate pattern'})
  .option('hz', {type: 'number', default: 2, desc: 'Notifications per second (0.1-10)'})
  .option('fixedHr', {type: 'number', default: 85, desc: 'Heart Rate when pattern=fixed'})
  .help().argv;

//wait for the adapter to be ready
let primaryService;

const SERVICE_UUID = argv.service.toLowerCase();
const CHAR_UUID = argv.char.toLowerCase();
const DEVICE_NAME = argv.name;

//creating handler upon state changes to the systems bluetooth state
//so if bluetooth is on, and we start the fake ble peripheral bleno should start advertising on device name with the specific service uuid
bleno.on('stateChange', (state) => {
  console.log(`Changing state: ${state}`);

  if(state !== 'poweredOn'){
    return bleno.stopAdvertising();
  }

  //build GATT service/characteristics with my options
  primaryService = makeService({
    serviceUuid: SERVICE_UUID,
    charUuid: CHAR_UUID,
    mode: argv.mode,
    hz: argv.hz, 
    pattern: argv.pattern,
    fixedHr: argv.fixedHr,
  });

  console.log('Start advertising.....');
  bleno.startAdvertising(DEVICE_NAME, [SERVICE_UUID]);
})


//handle connections
bleno.on('accept', (addr) => {
  console.log(`[Listening to connection: ${addr} connected]`);
});
bleno.on('disconnect', (addr) => {
  console.log(`[Listening to connection: ${addr} disconnected]`);
});

//error logging on starting the advertiser and on setting the service
bleno.on('advertisingStart', (err) => {
  if(err){
    return console.error('advertisingStart error: ', err)
  }

  bleno.setServices([primaryService], (e)=>{
    if(e){
      console.error('setService error: ', e);
    }

    console.log('GATT Service set.....');
  })
})

//graceful shutdown
process.on('SIGINT', () => {
  console.log('\n[exit] stopping advertising…');
  bleno.stopAdvertising(() => process.exit(0));
});

