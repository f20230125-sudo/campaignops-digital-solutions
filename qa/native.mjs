import {runCLI} from '@wp-playground/cli';
import {mkdirSync,existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const out=resolve('runtime/native-output');mkdirSync(out,{recursive:true});
await runCLI({command:'run-blueprint',blueprint:resolve('runtime/native-qa.zip'),workers:6,verbosity:'debug',mount:[{hostPath:out,vfsPath:'/verification'}]});
const result=resolve(out,'wordpress-native.json');
if(!existsSync(result))throw Error('WordPress did not produce a verification receipt.');
console.log(readFileSync(result,'utf8'));
