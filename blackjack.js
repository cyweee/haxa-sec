const WebSocket = require('ws');
const ws = new WebSocket('ws://63.179.96.42:7681/');
ws.on('open', () => { console.log('OPEN'); ws.send(JSON.stringify({AuthToken:''})); });
ws.on('message', d => console.log('MSG:', d.toString().slice(0,200)));
ws.on('error', e => console.log('ERR:', e.message));
setTimeout(() => process.exit(), 3000);
