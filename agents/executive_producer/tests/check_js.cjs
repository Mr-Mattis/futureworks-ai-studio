// Executes only reviewed Code-node source in a capability-free VM, never n8n.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(path.join(root, 'validate-plan.js'), 'utf8');
function run(code, globals) {
  const context = vm.createContext(globals, {codeGeneration: {strings: false, wasm: false}});
  return new vm.Script(`(function(){${code}\n})()`).runInContext(context, {timeout: 1000});
}
const cases = input.cases.map(plan => {
  try {
    run(source + '\nreturn validatePlan(plan, manifest, schema);', {plan, manifest: input.manifest, schema: input.schema});
    return true;
  } catch { return false; }
});
const workflow = JSON.parse(fs.readFileSync(path.join(root, 'workflow.inactive.json'), 'utf8'));
const prepare = workflow.nodes.find(n => n.name === 'Synthetic planning input').parameters.jsCode;
const validate = workflow.nodes.find(n => n.name === 'Validate proposal - no dispatch').parameters.jsCode;
const context = run(prepare, {})[0].json;
const responses = input.responses.map(response => {
  try {
    return run(validate, {
      $: name => { if (name !== 'Synthetic planning input') throw new Error('Unknown context'); return {first: () => ({json: context})}; },
      $input: {all: () => response.map(json => ({json}))},
    })[0].json;
  } catch { return null; }
});
console.log(JSON.stringify({cases, responses, context}));
