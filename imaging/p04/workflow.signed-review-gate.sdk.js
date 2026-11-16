import {workflow,trigger,node,newCredential} from '@n8n/workflow-sdk';
const start=trigger({type:'n8n-nodes-base.manualTrigger',version:1,config:{name:'P04 remediation manual audit'}});
const freeze=node({type:'n8n-nodes-base.code',version:2,config:{name:'Inspect frozen P04 manifest review status',parameters:{mode:'runOnceForAllItems',jsCode:"const manifest={project_id:'FWAI-EP-0001',manifest_sha256:'cf2bbd17b2170755fef18de1be5ea4c08694ee894c8167c70ed322aa9906fe87',approval_state:'pending_review',image_count:10,rights_reviewed:false,quality_reviewed:false,spend_authorized:false};if($input.all().length!==1||Object.keys($input.first().json||{}).length)throw Error('Only frozen P04 development manifest permitted');return [{json:manifest}];"}}});
const deny=node({type:'n8n-nodes-base.code',version:2,config:{name:'Require signed manifest rights and QA approval',parameters:{mode:'runOnceForAllItems',jsCode:"const x=$input.first().json;if(x.approval_state!=='approved'||x.rights_reviewed!==true||x.quality_reviewed!==true||x.spend_authorized!==true)throw Error('P04 owner-signed immutable approval has not been granted; no image batch POST');return [{json:x}];"}}});
const locked=node({type:'n8n-nodes-base.httpRequest',version:4.2,config:{
name:'DISABLED Credentialed P04 image batch writer',
disabled:true,
credentials:{httpHeaderAuth:newCredential('FWAI-P04-Development-HTTP-Header-Credential')},
parameters:{method:'POST',url:'http://host.docker.internal:18741/v1/start',
authentication:'genericCredentialType',genericAuthType:'httpHeaderAuth',
sendBody:true,specifyBody:'json',jsonBody:'={{ JSON.stringify({project_id:$json.project_id,run_id:"P04_REVIEW_REQUIRED",manifest_sha256:$json.manifest_sha256}) }}',
options:{timeout:20000}}
}});
export default workflow('fwai-p04-signed-review-credential-gate','FWAI-DEV — P04 Signed Review and Managed Credential Gate').add(start).to(freeze).to(deny).add(locked);
