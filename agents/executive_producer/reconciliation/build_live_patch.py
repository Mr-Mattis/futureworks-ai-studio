"""Build credential-free parameter updates for the existing inactive development workflow."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from planner import HERE, REPO, build_request, schema

WORKFLOW_ID = "HBvqaDLfhurpNLlu"


def parameters():
    context = build_request(REPO / "contracts/production-manifest/v1.0.0/example.valid.json")
    context["planning_schema"] = schema()
    expected = json.dumps(context, ensure_ascii=True)
    fixture = "return [{json: " + expected + "}];"
    prepare = (
        "const items=$input.all(); const expected=" + expected + ";"
        "if(items.length!==1 || JSON.stringify(items[0].json)!==JSON.stringify(expected)) "
        "throw new Error('Only the frozen synthetic development fixture is allowed');"
        "return [{json:expected}];"
    )
    validate = (HERE / "validate-plan.js").read_text() + """
const context=$('Prepare input').first().json;
const items=$input.all();
if(items.length!==1) throw new Error('Expected one model response');
const response=items[0].json;
const plan=response.output ?? response.text ?? response;
if(plan===null || Array.isArray(plan) || typeof plan!=='object')
  throw new Error('Structured object response required');
validatePlan(plan,context.manifest,context.planning_schema);
return [{json:{
  checkpoint:'P02.01',is_test:true,status:'candidate_requires_canonical_validation',
  input_manifest:context.input_manifest,candidate:plan,
  blockers:[...plan.blockers,'Canonical worker validation and independent approvals required'],
  authorization:{production_approved:false,spend_authorized:false,publish_authorized:false},
  dispatch_performed:false
}}];
"""
    return {
        "Manual role fixture": {"mode": "runOnceForAllItems", "jsCode": fixture},
        "Prepare input": {"mode": "runOnceForAllItems", "jsCode": prepare},
        "Executive Producer Agent": {
            "promptType": "define", "text": "={{ $json.prompt }}", "hasOutputParser": True,
            "needsFallback": False,
            "messages": {"messageValues": [{
                "type": "SystemMessagePromptTemplate", "message": "={{ $json.system_prompt }}"
            }]},
        },
        "Ollama Chat Model": {"model": "qwen3.6:latest", "options": {
            "think": False, "format": "json", "temperature": 0, "numPredict": 6000, "numCtx": 16384
        }},
        "Structured Output Parser": {
            "schemaType": "manual", "inputSchema": json.dumps(schema()), "autoFix": False
        },
        "Validate and return agent_result": {"mode": "runOnceForAllItems", "jsCode": validate},
    }


def chain_operations():
    return [
        {"type": "removeNode", "nodeName": "Executive Producer Agent"},
        {"type": "addNode", "node": {
            "id": "6b557f66-48eb-4546-ab4e-2de0020a26fc",
            "name": "Executive Producer Agent",
            "type": "@n8n/n8n-nodes-langchain.chainLlm", "typeVersion": 1.6,
            "position": [672,112], "parameters": parameters()["Executive Producer Agent"]
        }},
        {"type": "addConnection", "source": "Prepare input", "target": "Executive Producer Agent"},
        {"type": "addConnection", "source": "Executive Producer Agent",
         "target": "Validate canonical proposal - no dispatch"},
        {"type": "addConnection", "source": "Ollama Chat Model",
         "target": "Executive Producer Agent", "connectionType": "ai_languageModel"},
        {"type": "addConnection", "source": "Structured Output Parser",
         "target": "Executive Producer Agent", "connectionType": "ai_outputParser"},
        {"type": "setNodeSettings", "nodeName": "Executive Producer Agent",
         "settings": {"retryOnFail": False, "onError": "stopWorkflow"}},
    ]


def patch():
    operations = [
        {"type": "updateNodeParameters", "nodeName": name, "parameters": params, "replace": True}
        for name, params in parameters().items() if name != "Executive Producer Agent"
    ]
    operations.extend([
        {"type": "removeConnection", "source": "Called by orchestrator",
         "target": "Prepare input", "connectionType": "main"},
        {"type": "setNodeDisabled", "nodeName": "Called by orchestrator", "disabled": True},
        {"type": "renameNode", "oldName": "Validate and return agent_result",
         "newName": "Validate canonical proposal - no dispatch"},
    ])
    operations.extend(chain_operations())
    return dict(workflowId=WORKFLOW_ID, operations=operations,
                versionName="P02.01 canonical development reconciliation",
                versionDescription="Frozen manual synthetic fixture; strict tracked role/dependency/gate "
                "validation; candidate-only blocked handoff; no tools, dispatch or approval capability.")


if __name__ == "__main__":
    print(json.dumps(patch(), ensure_ascii=True))
