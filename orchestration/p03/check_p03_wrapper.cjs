// VM sandbox for evaluating n8n P03 Code nodes without network/require.
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const sandbox = {
  $input: { all: () => input.items.map(json => ({json})),
            first: () => ({json: input.items[0]}) },
  $: (name) => {
    if(name !== 'Validate brief') throw Error('Unknown node reference');
    return {first: () => ({json: input.context})};
  },
};
try {
  const output = vm.runInNewContext(
    '(function(){' + input.code + '\n})()', sandbox, {timeout: 1000});
  process.stdout.write(JSON.stringify({ok: true, output}));
} catch(e) {
  process.stdout.write(JSON.stringify({ok: false, error: String(e)}));
}
