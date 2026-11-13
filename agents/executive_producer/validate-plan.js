// Shared by the candidate n8n Code node and offline VM tests. No capabilities.
function validatePlan(plan, manifest, schema) {
  function reject() { throw new Error('P02.01 candidate rejected'); }
  function validate(value, rule) {
    if (rule.const !== undefined && value !== rule.const) reject();
    if (rule.enum && !rule.enum.includes(value)) reject();
    if (rule.type === 'object') {
      if (value === null || Array.isArray(value) || typeof value !== 'object') reject();
      if ((rule.required || []).some(key => !Object.hasOwn(value, key))) reject();
      if (rule.additionalProperties === false && Object.keys(value).some(key => !Object.hasOwn(rule.properties, key))) reject();
      for (const key of Object.keys(value)) {
        if (rule.properties[key]) validate(value[key], rule.properties[key]);
      }
    } else if (rule.type === 'array') {
      if (!Array.isArray(value) || value.length < (rule.minItems || 0) || value.length > (rule.maxItems ?? Infinity)) reject();
      if (rule.uniqueItems && new Set(value.map(v => JSON.stringify(v))).size !== value.length) reject();
      for (const item of value) validate(item, rule.items);
    } else if (rule.type === 'string') {
      if (typeof value !== 'string' || value.length < (rule.minLength || 0) || value.length > (rule.maxLength ?? Infinity)) reject();
      if (rule.pattern && !new RegExp(rule.pattern).test(value)) reject();
    } else if (rule.type === 'integer') {
      if (!Number.isSafeInteger(value) || value < rule.minimum || value > rule.maximum) reject();
    }
  }
  validate(plan, schema);
  if (plan.project_id !== manifest.project_id || plan.content_type !== manifest.content_type || plan.estimated_scene_count !== manifest.scenes.length) reject();
  const owners = {research: 'research_agent', script: 'creative_director', visual: 'visual_director', avatar: 'avatar_director', budget: 'budget_controller', assembly: 'editing_supervisor', qc: 'quality_control'};
  const ids = new Map(plan.work_packages.map(p => [p.package_id, p]));
  const stages = new Map(plan.work_packages.map(p => [p.stage, p]));
  if (ids.size !== 7 || stages.size !== 7) reject();
  for (const p of plan.work_packages) {
    if (owners[p.stage] !== p.owner || p.dependencies.some(d => !ids.has(d))) reject();
  }
  const visiting = new Set(), visited = new Set();
  function visit(key) {
    if (visiting.has(key)) reject();
    if (visited.has(key)) return;
    visiting.add(key);
    for (const dep of ids.get(key).dependencies) visit(dep);
    visiting.delete(key); visited.add(key);
  }
  for (const key of ids.keys()) visit(key);
  const prerequisites = {script: ['research'], visual: ['script'], avatar: ['script'], budget: ['visual', 'avatar'], assembly: ['visual', 'avatar', 'budget'], qc: ['assembly']};
  for (const [stage, required] of Object.entries(prerequisites)) {
    if (required.some(p => !stages.get(stage).dependencies.includes(stages.get(p).package_id))) reject();
  }
  if (new Set(plan.gates.map(g => g.name)).size !== 3) reject();
  return plan;
}
