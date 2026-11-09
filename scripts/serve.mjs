import http from 'node:http';
import { createReadStream,statSync } from 'node:fs';
import { resolve,extname,sep } from 'node:path';
const root=resolve('public');const port=Number(process.env.PORT||4006);const host=process.env.HOST||'127.0.0.1';
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.pdf':'application/pdf','.wasm':'application/wasm','.xml':'application/xml','.txt':'text/plain'};
http.createServer((req,res)=>{
 let path;try{path=decodeURIComponent(new URL(req.url,'http://localhost').pathname)}catch{res.writeHead(400).end();return}
 let file=resolve(root,'.'+path);if(file!==root&&!file.startsWith(root+sep)){res.writeHead(403).end();return}
 try{if(statSync(file).isDirectory()){if(!path.endsWith('/')){res.writeHead(301,{Location:path+'/'}).end();return}file=resolve(file,'index.html')}const stat=statSync(file);if(!stat.isFile())throw Error();res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream','Cache-Control':'no-store'});createReadStream(file).pipe(res)}catch{res.writeHead(404).end('Not found')}
}).listen(port,host,()=>console.log(`Captua preview: http://${host}:${port}/`));
