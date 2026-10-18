import {runCLI} from '@wp-playground/cli';
import {mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
const state=resolve('runtime/wordpress/wp-content');mkdirSync(state,{recursive:true});
const blueprint=resolve('public/downloads/campaignops-blueprint.zip');
if(!existsSync(blueprint))throw Error('Run npm run wp:package first.');
console.log('Durable WordPress content and SQLite state:',state);
await runCLI({command:'server',port:9400,wp:'7.0',php:'8.3',login:true,workers:6,blueprint,'mount-before-install':[{hostPath:state,vfsPath:'/wordpress/wp-content'}]});
