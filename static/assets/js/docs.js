/* Shared navigation and reading tools for the Captua guides (adapted from the Telar guides). */
(() => {
 'use strict';
 const header=document.querySelector('.guide-header');
 const updateHeader=()=>document.documentElement.style.setProperty('--header-height',header.getBoundingClientRect().height+'px');
 new ResizeObserver(updateHeader).observe(header);updateHeader();
 const hero=document.querySelector('.home-hero');
 if(hero){document.documentElement.classList.add('home-js');const sync=()=>header.classList.toggle('is-scrolled',hero.getBoundingClientRect().bottom<=header.getBoundingClientRect().height);addEventListener('scroll',sync,{passive:true});addEventListener('resize',sync);sync()}
 const lang=document.documentElement.lang;
 try{localStorage.setItem('captua-lang',lang)}catch{}
 const picker=document.querySelector('[data-section-picker]');
 picker?.addEventListener('change',()=>{if(picker.value)location.assign(picker.value)});
 const menu=document.querySelector('.docs-menu'),wide=matchMedia('(min-width:961px)');
 if(menu){const sync=()=>{menu.open=wide.matches};sync();wide.addEventListener('change',sync);menu.addEventListener('keydown',e=>{if(e.key==='Escape'&&!wide.matches&&menu.open){menu.open=false;menu.querySelector('summary').focus()}});menu.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{if(!wide.matches)menu.open=false}))}
 const article=document.querySelector('.docs-content'),announcement=document.getElementById('docs-announcement');
 const announce=text=>{announcement.textContent=text};
 const copy=async(text,button,success)=>{try{await navigator.clipboard.writeText(text);const original=button.textContent;button.textContent=success;announce(success);setTimeout(()=>button.textContent=original,1600)}catch{announce(article?.dataset.copyFailed||'Copy unavailable')}};
 if(article){
  const headings=[...article.querySelectorAll('h2[id]')];
  if(headings.length>3&&article.dataset.toc!=='false'){
   const toc=document.createElement('details');toc.className='on-this-page';toc.dataset.pagefindIgnore='';
   const summary=document.createElement('summary');summary.textContent=article.dataset.onPage;toc.append(summary);
   const list=document.createElement('ul');headings.forEach(h=>{const li=document.createElement('li'),a=document.createElement('a');a.href='#'+encodeURIComponent(h.id);a.textContent=h.textContent;li.append(a);list.append(li)});toc.append(list);headings[0].before(toc);
  }
  article.querySelectorAll('h2[id],h3[id],h4[id]').forEach(h=>{
   const a=document.createElement('a');a.className='heading-link';a.href='#'+encodeURIComponent(h.id);a.textContent='#';a.setAttribute('aria-label',article.dataset.copyLink);a.dataset.pagefindIgnore='';
   a.addEventListener('click',e=>{e.preventDefault();const url=new URL(location.href);url.hash=h.id;navigator.clipboard.writeText(url.href).then(()=>announce(article.dataset.linkCopied)).catch(()=>{location.hash=h.id})});h.append(a);
  });
  article.querySelectorAll('pre>code').forEach(code=>{
   const pre=code.parentElement;if(pre.closest('.code-sample'))return;
   const wrap=document.createElement('div');wrap.className='code-sample';pre.before(wrap);wrap.append(pre);
   const button=document.createElement('button');button.type='button';button.className='code-copy';button.textContent=article.dataset.copyCode;button.dataset.pagefindIgnore='';
   button.addEventListener('click',()=>copy(code.textContent,button,article.dataset.copied));wrap.append(button);
  });
  article.querySelectorAll('table').forEach(table=>{
   if(table.closest('.docs-table'))return;const wrap=document.createElement('div');wrap.className='docs-table';wrap.setAttribute('role','region');wrap.setAttribute('aria-label',table.querySelector('caption')?.textContent||article.dataset.tableLabel);table.before(wrap);wrap.append(table);
   const sync=()=>{if(wrap.scrollWidth>wrap.clientWidth+1)wrap.tabIndex=0;else wrap.removeAttribute('tabindex')};new ResizeObserver(sync).observe(wrap);sync();
  });
   }
 const dialog=document.getElementById('docs-search-dialog'),search=document.getElementById('docs-search');let searchStarted=false;
 const searchForm=document.querySelector('.docs-search-form'),headerQuery=searchForm.querySelector('input');
 function openSearch(query){
  if(!searchStarted){
   searchStarted=true;
   if(typeof PagefindUI==='function')new PagefindUI({element:'#docs-search',showSubResults:true,showImages:false,pageSize:5});
   else document.querySelector('.search-unavailable').hidden=false;
  }
  dialog.showModal();requestAnimationFrame(()=>{const input=search.querySelector('input');if(input&&typeof query==='string'){input.value=query;input.dispatchEvent(new Event('input',{bubbles:true}))}(input||dialog.querySelector('[data-close-search]')).focus()});
 }
 searchForm.addEventListener('submit',e=>{e.preventDefault();openSearch(headerQuery.value)});
 search.addEventListener('input',e=>{if(e.target.matches('input'))headerQuery.value=e.target.value});
 document.querySelectorAll('[data-open-search]').forEach(b=>b.addEventListener('click',()=>openSearch(headerQuery.value)));
 document.querySelector('[data-close-search]').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
 document.addEventListener('keydown',e=>{if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&!e.target.closest('input,textarea,select,[contenteditable="true"],[role="textbox"]')){e.preventDefault();if(!dialog.open)openSearch()}});
})();
