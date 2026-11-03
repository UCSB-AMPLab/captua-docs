import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { writeFileSync } from 'node:fs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const preview=process.argv.includes('--preview');
const start=performance.now();
for(const [name,args] of [['hugo',['--cleanDestinationDir',...(preview?['--config','hugo.json,hugo.preview.json']:[])]],['pagefind',['--site','public']]]){
 const cmd=resolve(root,'node_modules','.bin',name);
 const run=spawnSync(cmd,args,{cwd:root,stdio:'inherit'});
 if(run.status!==0)process.exit(run.status||1);
}
writeFileSync(resolve(root,'.build-result.json'),JSON.stringify({preview,seconds:(performance.now()-start)/1000},null,2)+'\n');
