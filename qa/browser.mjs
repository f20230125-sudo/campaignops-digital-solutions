import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const base=process.argv[2]??'http://localhost:3000';const full=process.argv.includes('--wordpress');mkdirSync('qa-output',{recursive:true});
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const context=await browser.newContext({viewport:{width:1440,height:1100}});const page=await context.newPage();const checks=[];const errors=[];const browserNotices=[];page.on('pageerror',e=>{if(e.message==='Transition was aborted because of invalid state. ViewTransition opt-in disabled')browserNotices.push(e.message);else errors.push(e.message);});
const check=(label,fn)=>{assert.ok(fn,label);checks.push(label);};
try{
 for(let i=0;i<30;i++){try{const response=await page.goto(base,{waitUntil:'networkidle'});if(response.ok())break;}catch{await page.waitForTimeout(1000);}}
 await page.getByRole('heading',{name:'A clearer view of every campaign.'}).waitFor();
 await page.waitForFunction(()=>document.querySelector('.app-shell')?.dataset.hydrated==='true');
 const data=await (await page.request.get(base+'/data/dashboard.json')).json();const metric=data.metrics.find(m=>m.campaign===m.market&&m.market===m.period&&m.period==='all');
 const cards=page.locator('.metric-card');for(const [i,k] of ['email_click_rate','engagement_rate','registration_rate','attendance_rate'].entries())check('Dashboard matches SQL metric '+k,(await cards.nth(i).innerText()).includes((metric[k]*100).toFixed(1)+'%'));
 await page.getByLabel('Campaign',{exact:true}).selectOption('hepatitis');await page.getByLabel('Market',{exact:true}).selectOption('AE');
 check('URL preserves campaign and market',page.url().includes('campaign=hepatitis')&&page.url().includes('market=AE'));
 await page.getByLabel('Reporting period').selectOption('2026-07');check('Scope recalculates denominator',(await cards.nth(2).innerText()).includes('/ '+data.metrics.find(m=>m.campaign==='hepatitis'&&m.market==='AE'&&m.period==='2026-07').sessions));
 await page.reload({waitUntil:'networkidle'});check('Filters survive refresh',await page.getByLabel('Campaign',{exact:true}).inputValue()==='hepatitis');
 await page.getByRole('button',{name:'Inspect source records'}).click();await page.locator('.source-table tbody tr').first().waitFor();check('Source drilldown has file and line',(await page.locator('.source-table').innerText()).includes('.csv:'));await page.getByRole('button',{name:'Close source records'}).click();
 await page.locator('nav').getByRole('button',{name:'Data health'}).click();await page.getByRole('button',{name:'Inspect quarantined rows'}).click();await page.getByRole('heading',{name:'Quarantine evidence'}).waitFor();check('Raw unmapped tag visible',(await page.locator('main').innerText()).includes('Hepatitis_2026'));
 await page.getByRole('button',{name:'Reports & briefs'}).click();
 for(const file of ['campaign-report.pdf','campaign-metrics.xlsx','campaign-metrics.csv','report-manifest.json','campaignops-blueprint.zip']){const res=await page.request.get(base+'/downloads/'+file);check('Download '+file,res.ok()&&(await res.body()).length>100);}
 await page.getByRole('button',{name:'Load saved brief'}).click();await page.locator('.ai-panel .empty').filter({hasText:'No saved AI brief matches'}).waitFor();check('Unsupported AI scope shown honestly',true);
 await page.getByLabel('Campaign',{exact:true}).selectOption('all');await page.getByLabel('Market',{exact:true}).selectOption('all');await page.getByLabel('Reporting period').selectOption('all');
 await page.getByRole('button',{name:'Load saved brief'}).click();await page.locator('.ai-panel .status').filter({hasText:'Validated metric references'}).waitFor();check('Saved AI draft matches scope and data fingerprint',true);
 await page.getByRole('button',{name:'Overview',exact:true}).click();await page.getByLabel('Campaign',{exact:true}).selectOption('all');await page.getByLabel('Market',{exact:true}).selectOption('all');await page.getByLabel('Reporting period').selectOption('all');
 const axe=await new AxeBuilder({page}).analyze();writeFileSync('qa-output/axe-desktop.json',JSON.stringify(axe.violations,null,2));check('Desktop automated accessibility checks',axe.violations.length===0);
 await page.screenshot({path:'qa-output/desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});check('No page horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.getByRole('button',{name:'Toggle navigation'}).click();await page.getByRole('button',{name:'Content operations',exact:true}).click();
 const mobileAxe=await new AxeBuilder({page}).analyze();writeFileSync('qa-output/axe-mobile.json',JSON.stringify(mobileAxe.violations,null,2));check('Mobile automated accessibility checks',mobileAxe.violations.length===0);await page.screenshot({path:'qa-output/mobile.png',fullPage:true});
 if(full){
  await page.getByRole('button',{name:'Launch WordPress'}).click();await page.getByRole('button',{name:'Refresh inventory & tests'}).waitFor({state:'visible'});
  await page.getByRole('button',{name:'Refresh inventory & tests'}).waitFor();
  for(let n=0;n<120;n++){if(await page.getByRole('button',{name:'Refresh inventory & tests'}).isEnabled())break;const e=page.locator('.wp-workbench .error');if(await e.count())throw Error(await e.innerText());await page.waitForTimeout(1000);}
  check('Real WordPress booted',await page.getByRole('button',{name:'Refresh inventory & tests'}).isEnabled());
  await page.getByRole('button',{name:'Refresh inventory & tests'}).click();await page.getByLabel('WordPress asset').waitFor();await page.getByLabel('WordPress asset').selectOption({label:'World Hepatitis Day · Landing'});await page.getByRole('button',{name:'View test page'}).click();
  let wp;for(let n=0;n<90;n++){wp=page.frames().find(f=>f.url().includes('scope:')&&!f.url().includes('wp-admin'));if(wp&&await wp.locator('#cops-cta').count())break;await page.waitForTimeout(1000);}
  if(!wp||!await wp.locator('#cops-cta').count()){writeFileSync('qa-output/frames.json',JSON.stringify(page.frames().map(f=>f.url())));throw Error('WordPress test page frame was not found.');}
  check('Seeded mobile CTA defect reproduced',!await wp.locator('#cops-cta').isVisible());
  await page.setViewportSize({width:1440,height:1100});
  await page.getByRole('button',{name:'Edit in WordPress'}).click();
  for(let n=0;n<60;n++){wp=page.frames().find(f=>f.url().includes('post.php'));if(wp&&await wp.getByRole('button',{name:/^(Save|Update)$/}).count())break;await page.waitForTimeout(1000);}
  const welcome=wp.getByRole('dialog');
  if(await welcome.count()){
    const close=welcome.getByRole('button',{name:/close/i});
    if(await close.count())await close.first().click();
  }
  const settings=wp.getByRole('button',{name:'Settings',exact:true});
  if(await settings.count()){
    const expanded=(await settings.first().getAttribute('aria-expanded'))??(await settings.first().getAttribute('aria-pressed'));
    if(expanded!=='true')await settings.first().click();
  }
  const postTab=wp.getByRole('tab',{name:/^(Post|Campaign assets?)$/});
  if(await postTab.count()&&await postTab.first().isVisible())await postTab.first().click();
  const governance=wp.getByRole('button',{name:'CampaignOps governance',exact:true});
  await governance.waitFor({state:'visible'});
  if(await governance.getAttribute('aria-expanded')==='false')await governance.click();
  await wp.getByLabel('Registration visible on mobile').check();
  const save=wp.getByRole('button',{name:/^(Save|Update)$/});await save.first().click();await page.waitForTimeout(2500);
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button',{name:'View test page'}).click();
  for(let n=0;n<60;n++){wp=page.frames().find(f=>f.url().includes('scope:')&&!f.url().includes('wp-admin'));if(wp&&await wp.locator('#cops-cta').isVisible().catch(()=>false))break;await page.waitForTimeout(1000);}
  await wp.getByRole('button',{name:'Open demo registration'}).click();await wp.getByRole('button',{name:'Complete demo registration'}).click();await wp.getByText('Demo registration recorded in WordPress.').waitFor();
  await page.getByRole('button',{name:'Refresh inventory & tests'}).click();await page.waitForTimeout(1000);check('Actual mobile registration recorded',(await page.locator('.test-summary').innerText()).includes('1 completed demo registrations'));
  const downloaded=page.waitForEvent('download');await page.getByRole('button',{name:'Export test ledger'}).click();const file=await downloaded;await file.saveAs('qa-output/wordpress-test-events.json');await page.screenshot({path:'qa-output/wordpress-mobile.png',fullPage:true});
 }
 check('No application JavaScript errors',errors.length===0);
 writeFileSync('qa-output/browser-result.json',JSON.stringify({base,checks,errors,browserNotices,wordpress:full},null,2));console.log(JSON.stringify({passed:checks.length,checks},null,2));
}catch(e){await page.screenshot({path:'qa-output/failure.png',fullPage:true}).catch(()=>{});writeFileSync('qa-output/browser-failure.json',JSON.stringify({error:String(e),checks,errors,workbench:await page.locator('.wp-workbench').innerText().catch(()=>''),frames:page.frames().map(f=>f.url())},null,2));throw e;}finally{await browser.close();}
