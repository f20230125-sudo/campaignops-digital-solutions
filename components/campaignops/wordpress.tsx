'use client';
import {useEffect,useRef,useState} from 'react';
import type {PlaygroundClient} from '@wp-playground/client';
import {Download,RefreshCw,ArrowUpRight} from 'lucide-react';
import {type Asset,type ObservedEvent,download,num} from '@/lib/campaignops';

export default function WordPress({onInventory}:{onInventory:(assets:Asset[])=>void}){
  const iframe=useRef<HTMLIFrameElement>(null);const client=useRef<PlaygroundClient|null>(null);
  const [status,setStatus]=useState('Preparing WordPress. The first load downloads the PHP runtime and WordPress.');const [ready,setReady]=useState(false);const [error,setError]=useState('');const [events,setEvents]=useState<ObservedEvent[]>([]);const [busy,setBusy]=useState(false);
  const [assets,setAssets]=useState<Asset[]>([]);const [assetId,setAssetId]=useState('');
  useEffect(()=>{
    let cancelled=false;
    async function boot(){try{
      const {startPlaygroundWeb}=await import('@wp-playground/client');
      const result=await startPlaygroundWeb({iframe:iframe.current!,remoteUrl:'https://playground.wordpress.net/remote.html',blueprint:{preferredVersions:{php:'8.3',wp:'7.0'},features:{networking:true},login:true,landingPage:'/wp-admin/edit.php?post_type=campaign_asset',steps:[{step:'installPlugin',pluginData:{resource:'url',url:new URL('/downloads/campaignops-plugin.zip',location.origin).href},options:{activate:true}},{step:'setSiteOptions',options:{blogname:'CampaignOps test workspace',blogdescription:'Isolated demonstration'}}]}});
      if(cancelled)return;client.current=result;setReady(true);setStatus('WordPress ready. This isolated sandbox belongs to this page session. Export before closing.');
    }catch(e){if(!cancelled)setError(e instanceof Error?e.message:String(e));}}
    boot();return()=>{cancelled=true;};
  },[]);
  async function rest(path:'inventory'|'events'){
    if(!client.current)throw Error('WordPress is still loading.');
    // Fixed bridge into this visitor's administrator sandbox. Native REST permission
    // callbacks still execute; no cross-frame browser cookies or arbitrary PHP input.
    const response=await client.current.run({code:`<?php require '/wordpress/wp-load.php'; wp_set_current_user(1); $response=rest_do_request(new WP_REST_Request('GET','/campaignops/v1/${path}')); echo wp_json_encode(['status'=>$response->get_status(),'data'=>$response->get_data()]);`});
    const result=JSON.parse(response.text) as {status:number;data:unknown};
    if(result.status!==200)throw Error(`WordPress returned ${result.status}. Check the sandbox administrator permissions.`);
    return result.data;
  }
  async function refresh(){setBusy(true);setError('');try{const inventory=await rest('inventory') as Asset[];const ledger=await rest('events') as ObservedEvent[];onInventory(inventory);setAssets(inventory);setAssetId(previous=>previous||String(inventory.find(a=>a.asset_id==='hepatitis-landing')?.id??inventory[0]?.id));setEvents(ledger);setStatus(`Refreshed ${inventory.length} assets and ${ledger.length} test events from WordPress.`);}catch(e){setError(String(e));}finally{setBusy(false);}}
  async function backup(){setBusy(true);try{
    if(!client.current) return;const {zipWpContent}=await import('@wp-playground/client');const zip=await zipWpContent(client.current);const url=URL.createObjectURL(new Blob([new Uint8Array(zip)],{type:'application/zip'}));const a=document.createElement('a');a.href=url;a.download='campaignops-wordpress-backup.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){setError(String(e));}finally{setBusy(false);}}
  const sessions=new Set(events.filter(e=>e.kind==='page_view').map(e=>e.session_id));const registrations=new Set(events.filter(e=>e.kind==='registration'&&sessions.has(e.session_id)).map(e=>e.session_id));
  return <section className="panel wp-workbench"><div className="panel-heading"><div><h2>WordPress workbench</h2><p role="status">{status}</p></div><div className="button-row"><button className="secondary" onClick={refresh} disabled={!ready||busy}><RefreshCw size={14}/>Refresh inventory & tests</button><button className="secondary" onClick={backup} disabled={!ready||busy}><Download size={14}/>Export sandbox</button></div></div>
    {error?<p className="error" role="alert">{error} <a href="/downloads/campaignops-blueprint.zip" download>Download the portable sandbox</a>.</p>:null}
    <details className="wp-instructions"><summary>How to investigate the mobile journey</summary><ol><li>Open the hepatitis landing asset, then View. At a narrow browser width its registration button is hidden.</li><li>Edit the asset. Open Settings ? the post tab ? CampaignOps governance, then enable “Registration visible on mobile” and publish.</li><li>View the page again on mobile and complete the demo registration. No email or personal information is used.</li><li>Refresh inventory and tests here. Export the event ledger and run the observed-test importer locally.</li><li>Use WordPress Revisions to inspect or restore saved content and metadata changes.</li></ol></details>
    {assets.length?<div className="wp-asset-tools"><label>Open an asset <select aria-label="WordPress asset" value={assetId} onChange={e=>setAssetId(e.target.value)}>{assets.map(a=><option key={a.id} value={a.id}>{a.title}</option>)}</select></label><button className="secondary" onClick={()=>client.current?.goTo(`/wp-admin/post.php?post=${Number(assetId)}&action=edit`)}>Edit in WordPress</button><button className="secondary" onClick={()=>client.current?.goTo(`/?post_type=campaign_asset&p=${Number(assetId)}`)}>View test page</button></div>:null}
    <iframe ref={iframe} title="Isolated WordPress editor" className="wp-frame" allow="clipboard-read; clipboard-write"/>
    <div className="test-summary"><div><span className="tiny-label">OBSERVED TESTS / THIS SANDBOX ONLY</span><p><strong>{num(sessions.size)}</strong> landing sessions <span>→</span> <strong>{num(registrations.size)}</strong> completed demo registrations</p><small>Never merged into the historical performance dataset.</small></div><button className="secondary" disabled={!events.length} onClick={()=>download('wordpress-test-events.json',JSON.stringify(events,null,2))}>Export test ledger <Download size={15}/></button></div>
    <p className="fine-print">Prefer a durable local workspace? Download the <a href="/downloads/campaignops-blueprint.zip" download>Blueprint bundle <ArrowUpRight size={12}/></a> and follow the local WordPress runbook.</p>
  </section>;
}
