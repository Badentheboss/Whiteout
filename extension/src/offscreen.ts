import * as ort from 'onnxruntime-web/wasm';
ort.env.wasm.numThreads=1;
ort.env.wasm.wasmPaths=chrome.runtime.getURL('ort/');
let session:Promise<ort.InferenceSession>|undefined;
let vocabulary:Record<string,number>|undefined;
function wordpiece(text:string):bigint[] {
 const cleaned=text.toLowerCase().replace(/canary-[a-z0-9-]+/gi,'token').normalize('NFD').replace(/\p{M}/gu,'')
  .replace(/[\p{Cf}\u0000\uFFFD]/gu,'').replace(/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u{20000}-\u{2FA1F}]/gu,' $& ');
 const basic=cleaned.match(/[\p{L}\p{N}]+|[^\s\p{L}\p{N}]/gu)||[];
 const output=[101n];
 for(const token of basic) {
  let start=0;const pieces:number[]=[];
  while(start<token.length){
   let end=token.length,found:number|undefined;
   while(end>start){const sub=(start?'##':'')+token.slice(start,end);if(vocabulary![sub]!==undefined){found=vocabulary![sub];break;}end--;}
   if(found===undefined){pieces.splice(0,pieces.length,100);break;}pieces.push(found);start=end;
  }
  output.push(...pieces.map(BigInt));if(output.length>=127)break;
 }
 return [...output.slice(0,127),102n];
}
chrome.runtime.onMessage.addListener((message,_sender,reply)=>{
 if(message.type!=='offscreen-score')return;
 (async()=>{
   if(!vocabulary)vocabulary=await (await fetch(chrome.runtime.getURL('models/vocab.json'))).json();
   session??=ort.InferenceSession.create(chrome.runtime.getURL('models/minilm-int8.onnx'),{executionProviders:['wasm']});
   const runtime=await session;const scores:number[]=[];
   for(let offset=0;offset<message.texts.length;offset+=16){
    const batch=message.texts.slice(offset,offset+16);const ids=new BigInt64Array(batch.length*128),mask=new BigInt64Array(batch.length*128);
    batch.forEach((text:string,i:number)=>{const tokens=wordpiece(text);ids.set(tokens,i*128);mask.fill(1n,i*128,i*128+tokens.length);});
    const result=await runtime.run({input_ids:new ort.Tensor('int64',ids,[batch.length,128]),attention_mask:new ort.Tensor('int64',mask,[batch.length,128])});
    scores.push(...Array.from(result.scores.data as Float32Array));
   }
   reply({scores});
 })().catch(e=>reply({error:String(e)}));return true;
});
