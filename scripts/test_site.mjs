import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';
const server=spawn('python3',['-m','http.server','4173','--bind','127.0.0.1','--directory','website/public'],{stdio:'ignore'});
let browser;
try{
  for(let i=0;i<40;i++){try{const r=await fetch('http://127.0.0.1:4173/');if(r.ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
  await mkdir('website/screenshots',{recursive:true});
  browser=await chromium.launch();
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(String(error)));
  await page.goto('http://127.0.0.1:4173/');
  assert.equal(await page.locator('h1').count(),1);
  await page.getByRole('tab',{name:'Notice clock'}).click();
  assert.match(await page.locator('#demo-out').innerText(),/cure sequence/);
  await page.getByRole('tab',{name:'Profit share'}).focus();
  await page.keyboard.press('ArrowLeft');
  assert.equal(await page.getByRole('tab',{name:'Notice clock'}).getAttribute('aria-selected'),'true');
  await page.screenshot({path:'website/screenshots/home-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.goto('http://127.0.0.1:4173/');
  await page.getByRole('button',{name:'Toggle navigation'}).click();
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Forms'}).click();
  assert.match(page.url(),/\/forms\/$/);
  assert.equal(await page.locator('.form-list article').count(),4);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'mobile horizontal overflow');
  await page.goto('http://127.0.0.1:4173/');
  await page.screenshot({path:'website/screenshots/home-mobile.png',fullPage:true});
  await page.goto('http://127.0.0.1:4173/get-started/');
  await page.getByRole('button',{name:'Copy starter prompt'}).click();
  await page.waitForFunction(()=>document.getElementById('copy-status').textContent.length>0);
  for(const route of ['/library/','/workflow/','/safety/','/verification/','/about/','/forms/']){
    const response=await page.goto('http://127.0.0.1:4173'+route);
    assert.equal(response.status(),200);assert.equal(await page.locator('h1').count(),1);
  }
  const zip=await page.request.get('http://127.0.0.1:4173/downloads/contract-check-direct-upload.zip');
  assert.equal(zip.status(),200);assert.equal((await zip.body()).subarray(0,2).toString(),'PK');
  assert.deepEqual(errors,[]);
  console.log('PASS: desktop/mobile navigation, keyboard tabs, copy feedback, four forms, page routes, ZIP download, and no browser errors.');
}finally{await browser?.close();server.kill();}
