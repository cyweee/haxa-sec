#!/usr/bin/env node
// Смотрим сырые WS заголовки и ответы + два одновременных соединения
// npm install ws && node ws_recon.js

const WebSocket = require('ws');
const http = require('http');
const URL = 'ws://63.179.96.42';

// 1. Проверяем HTTP заголовки WebSocket upgrade
const req = http.request({
  hostname: '63.179.96.42',
  port: 80,
  path: '/',
  method: 'GET',
  headers: {
    'Upgrade': 'websocket',
    'Connection': 'Upgrade',
    'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
    'Sec-WebSocket-Version': '13',
  }
}, (res) => {
  console.log('HTTP Status:', res.statusCode);
  console.log('Headers:', JSON.stringify(res.headers, null, 2));
  res.on('data', d => console.log('Data:', d.toString()));
});
req.on('error', e => console.log('HTTP err:', e.message));
req.end();

// 2. Два соединения одновременно — может будут делить bankroll?
setTimeout(() => {
  console.log('\n=== Два одновременных WS соединení ===');
  
  let br1 = 0, br2 = 0;
  
  const ws1 = new WebSocket(URL);
  const ws2 = new WebSocket(URL);
  
  function send1(o) { if(ws1.readyState===1){ws1.send(JSON.stringify(o));console.log('[WS1]→',JSON.stringify(o));} }
  function send2(o) { if(ws2.readyState===1){ws2.send(JSON.stringify(o));console.log('[WS2]→',JSON.stringify(o));} }
  
  ws1.on('open', () => { console.log('[WS1] Připojeno'); send1({type:'join'}); });
  ws2.on('open', () => { console.log('[WS2] Připojeno'); send2({type:'join'}); });
  
  ws1.on('message', d => {
    const msg = JSON.parse(d);
    console.log('[WS1]←', JSON.stringify(msg));
    if(msg.type==='state'&&msg.phase==='bet'){
      br1=msg.bankroll;
      console.log(`[WS1] Bankroll: $${br1}`);
      send1({type:'bet',amount:500});
    } else if(msg.type==='state'&&msg.phase==='action'){
      send1({type:'action',move:'stand'});
    } else if(msg.type==='result'){
      br1=msg.bankroll;
      console.log(`[WS1] After result: $${br1}`);
      // Попробуем send2 bet на результат WS1
      send2({type:'bet',amount:500});
    }
  });
  
  ws2.on('message', d => {
    const msg = JSON.parse(d);
    console.log('[WS2]←', JSON.stringify(msg));
    if(msg.type==='state'&&msg.phase==='bet'){
      br2=msg.bankroll;
      console.log(`[WS2] Bankroll: $${br2}`);
    } else if(msg.type==='state'&&msg.phase==='action'){
      send2({type:'action',move:'stand'});
    } else if(msg.type==='result'){
      br2=msg.bankroll;
      console.log(`[WS2] After result: $${br2}`);
    } else if(msg.type==='flag'){
      console.log('FLAG:', msg.message);
    }
  });
  
  ws1.on('error', e => console.log('[WS1] ERR:', e.message));
  ws2.on('error', e => console.log('[WS2] ERR:', e.message));
  
  setTimeout(()=>{ ws1.close(); ws2.close(); }, 10000);
}, 500);
