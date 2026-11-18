'use strict';
const $=id=>document.getElementById(id),video=$('video'),status=$('status'),result=$('result');
const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;const ctx=canvas.getContext('2d',{willReadFrequently:true});
let db=[],paused=false,busy=false,stream=null,detector=null,lastFrame=0,lastCode='',frameHandle=0,stableSku='',stableCount=0,lastCandidateTime=0,lastOCR=0,ocrDisabled=false,ocrPending=false,ocrStable="",ocrStableCount=0;
const KEY='offline_sku_db_v1';try{db=JSON.parse(localStorage.getItem(KEY)||'[]')}catch{}
function persist(){try{localStorage.setItem(KEY,JSON.stringify(db));return true}catch(e){status.textContent='保存失败：本地空间不足，请先导出备份';return false}}
function normalize(v){return String(v||'').toUpperCase().replace(/[^A-Z0-9]/g,'')}
function validItem(x){return x&&typeof x.sku==='string'&&x.sku.trim()&&typeof x.name==='string'&&x.name.trim()&&Number.isFinite(Number(x.price))&&Number(x.price)>=0&&(!x.feature||Array.isArray(x.feature)&&x.feature.length===192)&&(!x.features||Array.isArray(x.features)&&x.features.every(f=>Array.isArray(f)&&f.length===192))}
function clearCandidates(){ $('candidates').replaceChildren() }
function feature(){ctx.drawImage(video,0,0,64,64);const p=ctx.getImageData(0,0,64,64).data;let f=[];for(let y=0;y<8;y++)for(let x=0;x<8;x++){let r=0,g=0,b=0;for(let j=0;j<8;j++)for(let i=0;i<8;i++){let k=((y*8+j)*64+x*8+i)*4;r+=p[k];g+=p[k+1];b+=p[k+2]}f.push(Math.round(r/64/16),Math.round(g/64/16),Math.round(b/64/16))}return f}
function distance(a,b){let d=0;for(let i=0;i<a.length;i++){const q=a[i]-b[i];d+=q*q}return d/a.length}
function show(item,method){if(paused)return;paused=true;clearCandidates();$('name').textContent=item.name;$('price').textContent='₱'+Number(item.price).toFixed(2);$('sku').textContent=item.sku+' · '+method;result.showModal();status.textContent='识别暂停'}
function lookup(code){const v=normalize(code);if(!v)return;const found=db.filter(x=>normalize(x.barcode)===v||normalize(x.sku)===v);if(found.length===1)show(found[0],'编号/条码匹配');else status.textContent=found.length?'编号重复，请修正数据库':'本地商品库未找到该编号'}
function candidates(){
 if(!db.length){clearCandidates();return}
 const f=feature();
 const r=db.map(x=>{const fs=x.features?.length?x.features:(x.feature?[x.feature]:[]);if(!fs.length)return null;return{x,d:Math.min(...fs.map(v=>distance(f,v)))}}).filter(Boolean).sort((a,b)=>a.d-b.d).slice(0,5);
 const host=$('candidates');host.replaceChildren();
 if(!r.length)return;
 const h=document.createElement('p');h.textContent='包装外观候选（仅供人工选择，不能自动确认）';host.append(h);
 for(const {x,d} of r){const b=document.createElement('button');b.textContent=x.name+' · ₱'+Number(x.price).toFixed(2)+' · '+x.sku+'（外观差异 '+d.toFixed(1)+'）';b.onclick=()=>show(x,'人工确认视觉候选');host.append(b)}
}
async function scan(t){frameHandle=requestAnimationFrame(scan);if(paused||busy||!video.videoWidth||t-lastFrame<350)return;lastFrame=t;busy=true;try{if(detector){const codes=await detector.detect(video);if(paused)return;for(const c of codes){const value=c.rawValue||'';if(value&&value!==lastCode){lastCode=value;const item=db.find(x=>x.barcode===value||x.sku===value);if(item){show(item,'条码');return}}}}if(!paused&&!ocrDisabled&&window.ScannerOCR&&!ocrPending&&t-lastOCR>1700){
 lastOCR=t;ocrPending=true;
 ScannerOCR.recognize(video).then(found=>{
   if(paused)return;
   const matches=new Map();
   for(const code of found){
     const exact=db.filter(x=>normalize(x.sku)===code||normalize(x.productCode)===code||normalize(x.model)===code);
     if(exact.length===1)matches.set(normalize(exact[0].sku),exact[0]);
   }
   if(matches.size!==1){ocrStable='';ocrStableCount=0;return}
   const [key,item]=matches.entries().next().value;
   if(ocrStable===key)ocrStableCount++;else{ocrStable=key;ocrStableCount=1}
   if(ocrStableCount>=2){ocrStable='';ocrStableCount=0;show(item,'OCR 货号')}
 }).catch(err=>{ocrDisabled=true;status.textContent='OCR 不可用：'+(window.ScannerOCR?.describe?.(err)||String(err))}).finally(()=>{ocrPending=false});
}
if(!paused&&t-lastCandidateTime>=700){lastCandidateTime=t;candidates()}}catch(e){status.textContent='扫描异常：'+e.message}finally{busy=false}}
async function startCamera(){try{if(!navigator.mediaDevices?.getUserMedia){throw new Error('当前 WebView 不支持摄像头接口，需原生 WebChromeClient 授权及安全来源配置')}if(stream){status.textContent='摄像头已启动';return}stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}},audio:false});video.srcObject=stream;await video.play();if('BarcodeDetector'in window){try{detector=new BarcodeDetector({formats:['ean_13','ean_8','code_128','code_39','upc_a','upc_e','itf']})}catch{detector=null}}status.textContent=detector?'扫描中：条码、OCR 和包装候选':'扫描中：OCR 和包装候选';requestAnimationFrame(scan)}catch(e){const reason=e?.name==='NotAllowedError'?'摄像头授权被拒绝，请在系统设置中允许摄像头权限，并确认原生 WebView 已处理 onPermissionRequest':e?.name==='NotFoundError'?'未找到可用摄像头':e?.name==='NotReadableError'?'摄像头被其他应用占用':(e?.message||String(e));status.textContent='摄像头启动失败：'+reason;$('start').hidden=false;stream=null}}
$('lookup').onclick=()=>lookup($('code').value);
$('enroll').onclick=()=>{if(!video.videoWidth){alert('请先启动摄像头');return}const sku=prompt('商品 SKU / 字母数字货号');if(!sku)return;const name=prompt('商品名称');if(!name)return;const price=prompt('价格（菲律宾比索）');if(price===null||!Number.isFinite(Number(price)))return;const barcode=prompt('条码（没有可留空）')||'';const key=normalize(sku);if(!key){alert('商品编号不能为空');return}const existing=db.find(x=>normalize(x.sku)===key);const feat=feature();const item={sku:sku.trim(),name:name.trim(),price:Number(price),barcode:barcode.trim(),features:[...(existing?.features||existing?.feature?[...(existing?.features||[existing.feature])]:[]),feat].slice(-5)};if(!validItem(item)){alert('商品资料无效');return}db=db.filter(x=>normalize(x.sku)!==key);db.push(item);if(persist())status.textContent='已录入 '+item.name+'（共 '+db.length+' SKU，最多保留5个角度）';refreshCount()};
$('close').onclick=()=>{result.close();paused=false;lastCode='';ocrStable='';ocrStableCount=0;status.textContent='正在扫描商品';if(!stream)startCamera()};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify(db)],{type:'application/json'}),u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='sku-database.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),2000)};
$('import').onchange=async e=>{try{const a=JSON.parse(await e.target.files[0].text());if(!Array.isArray(a)||a.length>10000||!a.every(validItem))throw Error('商品数组格式错误');const seen=new Set();for(const x of a){const k=normalize(x.sku);if(seen.has(k))throw Error('存在重复 SKU：'+x.sku);seen.add(k)}db=a;if(persist())status.textContent='已导入 '+db.length+' SKU';refreshCount()}catch(err){alert('导入失败：'+err.message)}};

window.addEventListener('pagehide',()=>{if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}cancelAnimationFrame(frameHandle)});

$('start').onclick=startCamera;
function refreshCount(){const el=$('skuCount');if(el)el.textContent=db.length+' 种商品'}
refreshCount();
window.addEventListener('DOMContentLoaded',()=>{status.textContent='界面已加载，准备启动摄像头';setTimeout(startCamera,300);});
