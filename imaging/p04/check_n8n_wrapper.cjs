// Networkless P04 n8n Code-node evaluation. No require in VM sandbox.
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const req = JSON.parse(fs.readFileSync(0,'utf8'));
const box = {
  $input: { all:()=>req.items.map(json=>({json})), first:()=>({json:req.items[0]}) }
};
try {
  const result = vm.runInNewContext('(function(){'+req.code+'\n})()',box,{timeout:1000});
  process.stdout.write(JSON.stringify({ok:true,result}));
} catch (exc) {
  process.stdout.write(JSON.stringify({ok:false,error:String(exc)}));
}
