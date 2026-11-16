"""Generate credential-free P02.03–P02.10 n8n development workflow hardening patches.

Reads the inspected, synthetic 2026-11-15 inventory and pinned P01.02 registry.
Never sends requests to n8n or providers. Write operations must be reviewed
and executed only against the specific *inactive* development workflow IDs.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from role_validation import INVENTORY, REGISTRY, records, registry, schema

AGENT_NODE_NAMES = {
    "research_agent": "Research Agent",
    "visual_director": "Visual Director Agent",
    "avatar_director": "Avatar Director Agent",
    "budget_controller": "Budget Controller Agent",
    "editing_supervisor": "Editing Supervisor Agent",
    "quality_control": "Quality Control Agent",
    "growth_strategist": "Growth Strategist Agent",
    "sop_knowledge": "SOP & Knowledge Agent",
}


def js_literal(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def strict_validator_js(role):
    """Core JSON-schema keyword validator and role policy (candidate-only)."""
    return """
const ctx=$('Prepare input').first().json;const rows=$input.all();
if(rows.length!==1)throw Error('Exactly one response required');
let candidate=rows[0].json.output??rows[0].json.text??rows[0].json;
if(typeof candidate==='string')candidate=JSON.parse(candidate);
const SCHEMA=__SCHEMA__;
function reject(){throw Error('P02 specialist proposal rejected')}
function check(value,rule){
 if(rule.const!==undefined&&JSON.stringify(value)!==JSON.stringify(rule.const))reject();
 if(rule.enum&&!rule.enum.includes(value))reject();
 if(rule.type==='object'){
  if(!value||typeof value!=='object'||Array.isArray(value))reject();
  if((rule.required||[]).some(k=>!Object.hasOwn(value,k)))reject();
  if(rule.additionalProperties===false&&Object.keys(value).some(k=>!Object.hasOwn(rule.properties||{},k)))reject();
  for(const [key,item] of Object.entries(value))if((rule.properties||{})[key])check(item,rule.properties[key]);
 }else if(rule.type==='array'){
  if(!Array.isArray(value)||value.length<(rule.minItems||0)||value.length>(rule.maxItems??Infinity))reject();
  if(rule.items)for(const item of value)check(item,rule.items);
 }else if(rule.type==='string'){if(typeof value!=='string'||value.length<(rule.minLength||0))reject();}
 else if(rule.type==='boolean'){if(typeof value!=='boolean')reject();}
 else if(rule.type==='number'){if(typeof value!=='number'||!Number.isFinite(value))reject();}
 else if(rule.type==='integer'){if(!Number.isSafeInteger(value))reject();}
}
check(candidate,SCHEMA);
if(ctx.scope==='episode'){
 if(candidate.project_id!==ctx.project_id||ctx.input_manifest?.project_id!==ctx.project_id)reject();
}else if(ctx.scope!=='studio'||ctx.input_manifest!==null)reject();
const input=ctx.role_input; const ROLE=__ROLE__;
if(ROLE==='research_agent'){
 if(!input.sources?.length&&candidate.verified_claims.length)reject();
 if(!candidate.unverified_claims.length)reject();
}
if(ROLE==='growth_strategist'){
 if(!input.video_metrics&&candidate.observed_patterns.length)reject();
 if(!candidate.data_gaps.length)reject();
}
if(ROLE==='sop_knowledge'&&candidate.owner_approval_required!==true)reject();
if(ROLE==='budget_controller'){
 if(candidate.currency!=='USD'||candidate.approval_required!==true)reject();
 if(!Object.keys(input.provider_rates||{}).length&&!candidate.missing_rates.length)reject();
}
if(ROLE==='avatar_director'){
 if(!input.approved_asset_ids?.length&&!candidate.missing_assets.length)reject();
 if(!input.avatar_profile&&!candidate.required_consents.length)reject();
}
if(ROLE==='quality_control'&&!input.ffprobe_report&&candidate.overall_verdict==='pass')reject();
if(ROLE==='editing_supervisor'&&!input.media_inspection&&candidate.manual_review_required!==true)reject();
if(ROLE==='visual_director'){
 if(!candidate.shots?.length)reject();
 if(input.scene_ids?.length&&candidate.shots.some(s=>!input.scene_ids.includes(s.scene_id)))reject();
}
const blockers=['Independent canonical contract validation and owner approval required'];
if(ROLE==='research_agent')blockers.push('Claims without evidence remain unverified');
if(ROLE==='budget_controller')blockers.push('Spending caps enforced outside this model; no rates assumed');
if(ROLE==='avatar_director')blockers.push('Presenter likeness/voice consent must be independently verified');
if(ROLE==='quality_control')blockers.push('QC media evidence must be independently inspected');
if(ROLE==='growth_strategist')blockers.push('No real YouTube analytics were provided');
if(ROLE==='sop_knowledge')blockers.push('SOP changes are only proposals, not applied');
return [{json:{checkpoint:'__CHECKPOINT__',is_test:true,scope:ctx.scope,
 status:'candidate_requires_canonical_validation',input_manifest:ctx.input_manifest,candidate,
 blockers,authorization:{production_approved:false,spend_authorized:false,publish_authorized:false},
 dispatch_performed:false}}];
""".replace("__SCHEMA__", js_literal(schema(role))).replace(
        "__ROLE__", js_literal(role)).replace(
        "__CHECKPOINT__", records()[role]["checkpoint"])


def patch(role):
    item = records()[role]
    if role not in AGENT_NODE_NAMES or item["active"]:
        raise ValueError("Never patch production or unknown roles")
    expected = item["fixture"]
    if not expected or expected["scope"] not in ("episode", "studio"):
        raise ValueError("Missing inspected frozen development fixture")
    freeze_js = "return [{json:" + js_literal(expected) + "}];"
    prepare_js = (
        "const expected=" + js_literal(expected) + ";const items=$input.all();"
        "if(items.length!==1||JSON.stringify(items[0].json)!==JSON.stringify(expected))"
        "throw Error('Only frozen role fixture permitted');"
        "return [{json:{...expected,prepared_at:new Date().toISOString()}}];"
    )
    sys = registry()[role]["output_instructions"] + (
        "\nDevelopment only; strictly one role-native JSON object. "
        "No tools, external effects, fabricated sources or approval. "
        "All actual provider submissions, publication, SOP writes, and expenses are forbidden. "
        "No extra root properties; meet required uncertainty and consent disclosures."
    )
    if role == "budget_controller":
        sys += (
            "\\nBUDGET ACCEPTANCE: approval_required MUST be true even if the spending "
            "cap and planned costs are zero; this model never grants financial approval. "
            "With an empty provider_rates object, missing_rates MUST be a non-empty "
            "array describing unavailable independently verified provider pricing, "
            "even when proposed_assets is empty. Do not infer rates or permission."
        )
    agent = AGENT_NODE_NAMES[role]
    operations = [
        {"type": "updateNodeParameters", "nodeName": "Manual role fixture",
         "parameters": {"mode": "runOnceForAllItems", "jsCode": freeze_js}, "replace": True},
        {"type": "updateNodeParameters", "nodeName": "Prepare input",
         "parameters": {"mode": "runOnceForAllItems", "jsCode": prepare_js}, "replace": True},
        {"type": "updateNodeParameters", "nodeName": "Structured Output Parser",
         "parameters": {"schemaType": "manual", "inputSchema": js_literal(schema(role)),
                        "autoFix": False}, "replace": True},
        {"type": "updateNodeParameters", "nodeName": "Ollama Chat Model",
         "parameters": {"model": "qwen3.6:latest",
                        "options": {"think": False, "format": "json",
                                    "temperature": 0, "numPredict": 6000,
                                    "numCtx": 16384}}, "replace": True},
        {"type": "updateNodeParameters", "nodeName": "Validate and return agent_result",
         "parameters": {"mode": "runOnceForAllItems", "jsCode": strict_validator_js(role)},
         "replace": True},
        {"type": "removeConnection", "source": "Called by orchestrator",
         "target": "Prepare input", "connectionType": "main"},
        {"type": "setNodeDisabled", "nodeName": "Called by orchestrator", "disabled": True},
        {"type": "renameNode", "oldName": "Validate and return agent_result",
         "newName": "Validate canonical proposal - no dispatch"},
        {"type": "removeNode", "nodeName": agent},
        {"type": "addNode", "node": {
            "id": "fwai-dev-" + role.replace("_", "-"),
            "name": agent,
            "type": "@n8n/n8n-nodes-langchain.chainLlm",
            "typeVersion": 1.6,
            "position": [672, 112],
            "parameters": {
                "promptType": "define", "text": "={{ JSON.stringify($json.role_input) }}",
                "hasOutputParser": True, "needsFallback": False,
                "messages": {"messageValues": [{
                    "type": "SystemMessagePromptTemplate", "message": sys}]},
            },
        }},
        {"type": "addConnection", "source": "Prepare input", "target": agent},
        {"type": "addConnection", "source": agent,
         "target": "Validate canonical proposal - no dispatch"},
        {"type": "addConnection", "source": "Ollama Chat Model", "target": agent,
         "connectionType": "ai_languageModel"},
        {"type": "addConnection", "source": "Structured Output Parser", "target": agent,
         "connectionType": "ai_outputParser"},
        {"type": "setNodeSettings", "nodeName": agent,
         "settings": {"retryOnFail": False, "onError": "stopWorkflow"}},
    ]
    return {
        "workflowId": item["id"],
        "operations": operations,
        "versionName": item["checkpoint"] + " canonical specialist development",
        "versionDescription": "Frozen manual fixture, local Ollama, strict role output, "
            "blocked candidate, disconnected orchestrator entry, no provider/publishing actions.",
    }


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("role", choices=AGENT_NODE_NAMES)
    args = p.parse_args()
    print(json.dumps(patch(args.role), separators=(",", ":")))


if __name__ == "__main__":
    main()
