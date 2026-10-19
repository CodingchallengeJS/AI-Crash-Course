"""Long-form curriculum and contextual chat drawer checks; API is mocked."""
import json,sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 b=p.chromium.launch();c=b.new_context(viewport={'width':1600,'height':1000});page=c.new_page()
 errors=[];calls=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def google(route):
  req=route.request
  if req.method=='OPTIONS':
   route.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,x-goog-api-key','Access-Control-Allow-Methods':'GET,POST,OPTIONS'});return
  if req.method=='GET':
   route.fulfill(status=200,content_type='application/json',body=json.dumps({'models':[{'name':'models/gemini-test-flash','supportedGenerationMethods':['generateContent']}]}));return
  calls.append(req.post_data_json)
  frames={'candidates':[{'content':{'parts':[{'text':'Q là giá trị của một hành động. \\(2+0.5(5.5-2)=3.75\\)'}]},'finishReason':'STOP'}]}
  route.fulfill(status=200,content_type='text/event-stream',body='data: '+json.dumps(frames)+'\n\n')
 c.route('https://generativelanguage.googleapis.com/**',google)
 def go(r):
  page.goto(BASE+'#/'+r,wait_until='networkidle')
  page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
 go('learn/RL')
 assert page.locator('.beginner-path').count()==1
 assert page.locator('.beginner-links a').count()==4
 data=page.evaluate('LESSONS.filter(l=>l.tutorial).map(l=>({id:l.id,sections:l.tutorial.length,words:l.tutorial.flatMap(s=>s.paragraphs).join(" ").split(/\\s+/).length,chars:l.tutorial.flatMap(s=>s.paragraphs).join(" ").length}))')
 assert len(data)==11,data
 assert all(x['sections']>=6 and x['chars']>3000 for x in data),data
 # Every guide renders, all displayed formulas are valid, and each TOC target exists.
 for l in data:
  go('lesson/'+l['id'])
  assert page.locator('.guided-section').count()==l['sections']
  assert page.locator('.katex-error').count()==0,l['id']
  assert page.evaluate('Array.from(document.querySelectorAll("[data-anchor]")).every(a=>document.getElementById(a.dataset.anchor))')
  assert page.locator('.revision-recap').count()==1
 go('lesson/rl-qlearning')
 assert '3.75' in page.locator('#concept').inner_text() and '2.85' in page.locator('#concept').inner_text()
 before=page.url
 page.locator('#lesson-notes').fill('PRIVATE NOTE SHOULD NOT BE ATTACHED')
 page.locator('#tutor-launcher').click()
 assert page.url==before
 assert page.locator('#tutor-panel').is_visible()
 assert page.locator('#main .guided-section').count()==9
 assert page.locator('#tutor-prompt').count()==1
 assert 'SARSA' in page.locator('.tutor-context-title').inner_text()
 page.locator('#tutor-key').fill('test-fake-key')
 page.locator('#tutor-connect-form button[type=submit]').click()
 page.wait_for_selector('#tutor-model option[value="gemini-test-flash"]',state='attached')
 page.locator('#tutor-prompt').fill('Q là gì?')
 page.locator('#tutor-prompt-form button[type=submit]').click()
 page.wait_for_selector('.from-ai .tutor-message-footer')
 assert page.url==before
 assert calls[-1]['contents'][-1]['parts'][0]['text']=='Q là gì?',calls
 assert 'PRIVATE NOTE' not in json.dumps(calls)
 assert page.locator('#tutor-panel .katex').count()>0
 # Explicit lesson attachment preview and send: no notes or hidden exam export.
 page.locator('[data-tutor=attach-lesson]').click()
 assert page.locator('.tutor-attachment').is_visible()
 preview=page.locator('.tutor-attachment pre').text_content()
 assert 'Q-table' in preview and 'PRIVATE NOTE' not in preview,(len(preview),preview[:1200],preview[-300:])
 assert len(calls)==1
 page.locator('#tutor-prompt').fill('Giải thích sự khác nhau trong bài này.')
 page.locator('#tutor-prompt-form button[type=submit]').click()
 page.wait_for_function('document.querySelectorAll(".from-ai .tutor-message-footer").length===2')
 assert 'Q-table' in calls[-1]['contents'][-1]['parts'][0]['text']
 assert page.locator('.sent-attachment').count()==1
 # Draft and history survive minimizing, navigating and reopening.
 page.locator('#tutor-prompt').fill('Câu hỏi đang viết')
 page.locator('[data-tutor=close]').last.click()
 assert page.locator('#tutor-panel').is_hidden()
 assert page.url==before
 page.locator('#tutor-launcher').click()
 assert page.locator('#tutor-prompt').input_value()=='Câu hỏi đang viết'
 page.evaluate("location.hash='/lesson/ai-ac3'")
 page.wait_for_function('document.querySelector("#main h1").textContent.includes("AC-3")')
 assert page.locator('#tutor-panel').is_visible()
 assert page.locator('#tutor-prompt').input_value()=='Câu hỏi đang viết'
 assert 'AC-3' in page.locator('.tutor-context-title').inner_text()
 # Capture a deliberately selected lesson paragraph; attach only on click.
 page.evaluate('''()=>{const p=document.querySelector('.guided-section>p');let r=document.createRange();r.selectNodeContents(p);let s=window.getSelection();s.removeAllRanges();s.addRange(r);document.dispatchEvent(new Event('selectionchange'));}''')
 page.locator('[data-tutor=attach-selection]').click()
 assert 'X,Y,Z' in page.locator('.tutor-attachment pre').text_content()
 page.locator('[data-tutor=remove-attachment]').click()
 assert page.locator('.tutor-attachment').count()==0
 assert len(calls)==2
 page.keyboard.press('Escape');assert page.locator('#tutor-panel').is_hidden()
 # All existing Ask-AI links now open the same popup without route changes.
 before=page.url;page.locator('.top-tutor').click()
 assert page.url==before and page.locator('#tutor-panel').is_visible()
 page.locator('[data-tutor=close]').last.click()
 page.locator('[data-tutor-section="1"]').click()
 assert page.url==before and page.locator('.tutor-panel').is_visible()
 assert 'Support là một giá trị' in page.locator('.tutor-attachment pre').text_content()
 assert len(calls)==2
 page.locator('[data-tutor=remove-attachment]').click()
 page.locator('[data-tutor=close]').last.click()
 # Search indexes the explanatory prose, not only recap/formulas.
 results=page.evaluate("searchKnowledge('đường sát vực',{limit:20}).map(x=>x.id)")
 assert 'rl-qlearning' in results,results
 # Narrow and wide layouts; drawer controls remain within the viewport.
 for width in [390,1024,1600]:
  page.set_viewport_size({'width':width,'height':950})
  go('lesson/rl-qlearning');page.locator('#tutor-launcher').click()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  box=page.locator('#tutor-panel').bounding_box()
  assert box['x']>=0 and box['x']+box['width']<=width+1
  page.screenshot(path=f'exam-extracted/drawer-{width}.png',full_page=False)
  page.locator('[data-tutor=close]').last.click()
  go('lesson/ai-ac3')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 # Direct /chat is still usable and must never duplicate form IDs.
 go('chat');assert page.locator('#tutor-panel').is_hidden()
 assert page.locator('#tutor-prompt').count()==1
 assert 'test-fake-key' not in page.evaluate('JSON.stringify({...localStorage,...sessionStorage})')
 assert not errors,errors
 print(json.dumps({'passed':True,'guides':data,'drawer':True,'explicit_context_only':True,'responsive':[390,1024,1600],'js_errors':errors},ensure_ascii=False))
 b.close()
