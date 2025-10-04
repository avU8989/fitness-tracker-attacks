//lab-only ble peripheral to spoof a smartwatch and inject HR/Spo2 metrics

const bleno = require('@abandonware/bleno');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const makeService = require('./service');

//parse cli flags
const argv = yargs(hideBin(process.argv))
  .option('name', { type: 'string', default: 'Heart Rate', desc: 'Advertised device name' })
  .option('service', { type: 'string', default: '180d', desc: 'Service UUID (180d for Heart Rate' }) //Primary Service
  .option('char', { type: 'string', default: '2a37', desc: 'Characteristic UUID (2a37 for Heart Measurement)' }) //Characteristics
  .help().argv;

//wait for the adapter to be ready
let primaryService;

const SERVICE_UUID = String(argv.service).toLowerCase();
const CHAR_UUID = String(argv.char).toLowerCase();
const DEVICE_NAME = argv.name;

//creating handler upon state changes to the systems bluetooth state
//so if bluetooth is on, and we start the fake ble peripheral bleno should start advertising on device name with the specific service uuid
bleno.on('stateChange', (state) => {
  console.log(`Changing state: ${state}`);

  if (state !== 'poweredOn') {
    return bleno.stopAdvertising();
  }

  //build GATT service/characteristics with my options
  primaryService = makeService(
    SERVICE_UUID,
    CHAR_UUID,
  );

  console.log('Start advertising.....');
  bleno.startAdvertising(DEVICE_NAME, [SERVICE_UUID], (err) => {
    if (err) {
      console.log('Advertising start error');
    }
  });
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
  if (err) {
    return console.error('advertisingStart error: ', err)
  }

  bleno.setServices([primaryService], (e) => {
    if (e) {
      console.error('setService error: ', e);
    }

    console.log('GATT Service set.....');
  })
})

//graceful shutdown
let shuttingDown = false;
process.on('SIGINT', () => {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log('\n[exit] stopping advertising…');
  bleno.stopAdvertising(() => process.exit(0));
});

