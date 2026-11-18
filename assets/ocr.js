'use strict';
/* Offline OCR: retryable initialization with explicit Android WebView diagnostics. */
window.ScannerOCR=(()=>{
 let worker=null,initializing=null,active=false,lastRun=0,mode='';
 const roi=document.createElement('canvas');roi.width=720;roi.height=420;
 const context=roi.getContext('2d',{willReadFrequently:true});
 const root=new URL('ocr/',document.baseURI);
 const resolve=p=>new URL(p,root).href;
 const normalize=s=>String(s||'').toUpperCase().replace(/[^A-Z0-9]/g,'');
 const describe=e=>{
   if(typeof e==='string')return e||'未知错误（空字符串）';
   if(e==null)return '未知错误（Worker 未返回错误详情）';
   const msg=[e.name,e.message,e.stack].filter(Boolean).join('：');
   return msg||(()=>{try{return JSON.stringify(e)}catch{return String(e)}})()||'未知错误';
 };
 function codes(text){const out=new Set();for(const line of String(text||'').toUpperCase().split(/\r?\n/))for(const m of line.matchAll(/[A-Z0-9][A-Z0-9\-\s./]{2,24}/g)){const v=normalize(m[0]);if(v.length>=4&&v.length<=24&&/[A-Z]/.test(v)&&/[0-9]/.test(v))out.add(v)}return [...out]}
 const timeout=(p,ms,label)=>Promise.race([p,new Promise((_,reject)=>setTimeout(()=>reject(new Error(label+' 超时（'+Math.round(ms/1000)+'秒）')),ms))]);
 async function init(){
   if(worker)return worker;
   if(initializing)return initializing;
   initializing=(async()=>{
     if(!window.Tesseract?.createWorker)throw new Error('未加载 tesseract.min.js');
     if(!window.Worker)throw new Error('当前 Android WebView 不支持 Web Worker');
     const workerURL=resolve('worker.min.js');
     // All OCR files share the same HTTPS origin via Android asset interception.
     try{
       if(location.protocol!=='https:' || location.hostname!=='appassets.androidplatform.net') throw new Error('本地 HTTPS 资源映射未启用：'+location.href);
       mode='同源 HTTPS Worker';
       const opts={workerPath:workerURL,workerBlobURL:false,corePath:resolve('core/'),langPath:resolve('lang/'),cacheMethod:'none',gzip:true};
       const w=await timeout(Tesseract.createWorker('eng',1,opts),30000,'OCR Worker / WASM / 语言包初始化');
       await timeout(w.setParameters({tessedit_char_whitelist:'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-./ ',preserve_interword_spaces:'1'}),8000,'OCR 参数设置');
       worker=w;return w;
     }catch(e){throw new Error(describe(e)+'；加载方式：'+mode+'；页面：'+location.href)}

   })().catch(e=>{initializing=null;throw e});
   return initializing;
 }
 async function recognize(video){
   if(active||!video?.videoWidth||Date.now()-lastRun<1100)return [];
   active=true;lastRun=Date.now();
   try{
     const w=await init(),sw=video.videoWidth*.9,sh=video.videoHeight*.72;
     context.fillStyle='#fff';context.fillRect(0,0,roi.width,roi.height);
     context.drawImage(video,(video.videoWidth-sw)/2,(video.videoHeight-sh)/2,sw,sh,0,0,roi.width,roi.height);
     const result=await timeout(w.recognize(roi),12000,'OCR 识别');
     return codes(result?.data?.text);
   }finally{active=false}
 }
 async function dispose(){if(worker){await worker.terminate();worker=null}initializing=null}
 return {recognize,init,dispose,codes,describe};
})();
