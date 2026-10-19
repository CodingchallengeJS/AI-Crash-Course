"""End-to-end search and BYOK chatbot tests; Google responses are mocked.

No real key is used and no lesson/exam material leaves the local test browser.
"""
import json,sys
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
BASE='http://127.0.0.1:8000/'
FAKE_KEY='unit-test-key-not-a-real-google-key'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 ctx=browser.new_context(viewport={'width':1440,'height':1000})
 page=ctx.new_page();page.set_default_timeout(10000);errors=[];calls=[];mode={'value':'ok'};held=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def fulfill(route,status,data,content_type='application/json'):
  route.fulfill(status=status,content_type=content_type,headers={'Access-Control-Allow-Origin':'*'},body=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False))
 def google(route):
  request=route.request
  if request.method=='OPTIONS':
   route.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,x-goog-api-key','Access-Control-Allow-Methods':'GET,POST,OPTIONS'});return
  assert FAKE_KEY not in request.url
  assert request.headers.get('x-goog-api-key')==FAKE_KEY
  if request.method=='GET':
   calls.append({'type':'models','url':request.url})
   if mode['value']=='badkey':fulfill(route,403,{'error':{'message':'Key invalid: '+FAKE_KEY}});return
   if not parse_qs(urlparse(request.url).query).get('pageToken'):
    fulfill(route,200,{'models':[{'name':'models/gemini-test-flash','displayName':'Test Flash','supportedGenerationMethods':['generateContent']},{'name':'models/text-embedding-test','supportedGenerationMethods':['embedContent']}],'nextPageToken':'page-two'})
   else:fulfill(route,200,{'models':[{'name':'models/gemini-test-pro','displayName':'Test Pro','supportedGenerationMethods':['generateContent']},{'name':'models/gemini-test-flash','displayName':'Test Flash','supportedGenerationMethods':['generateContent']}]})
   return
  body=request.post_data_json;calls.append({'type':'chat','url':request.url,'body':body})
  # Only the explicitly submitted text and prior user/model turns are sent.
  assert all(set(part)=={'text'} for c in body['contents'] for part in c['parts'])
  assert 'inlineData' not in json.dumps(body)
  assert 'Mã đề 006' not in json.dumps(body,ensure_ascii=False)
  if mode['value']=='quota':fulfill(route,429,{'error':{'message':'Quota exceeded '+FAKE_KEY}});return
  if mode['value']=='hold':held.append(route);return
  if mode['value']=='empty':fulfill(route,200,{'candidates':[{'finishReason':'STOP','content':{'parts':[]}}]});return
  frames=[{'candidates':[{'content':{'parts':[{'text':'private thought','thought':True},{'text':'**Cập nhật trọng số**\n\n'}]}}]},
          {'candidates':[{'content':{'parts':[{'text':r'\[w_{t+1}=w_t-\eta\nabla_wL\]'+'\n\n<img src=x onerror="window.__tutorXSS=1">'}]},'finishReason':'STOP'}]}]
  # CRLF framing and an unterminated last event exercise the SSE parser.
  stream='data: '+json.dumps(frames[0],ensure_ascii=False)+'\r\n\r\n'+'data: '+json.dumps(frames[1],ensure_ascii=False)
  fulfill(route,200,stream,'text/event-stream')
 ctx.route('https://generativelanguage.googleapis.com/**',google)
 def go(route=''):
  page.goto(BASE+'#/'+route,wait_until='networkidle')
  page.evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
  assert not errors,errors
 go()
 page.locator('#home-knowledge-search').fill('cập nhật trọng số w')
 page.locator('#home-search-form button').click();page.wait_for_selector('.knowledge-result')
 assert 'Gradient descent' in page.locator('#main .knowledge-result strong').first.inner_text()
 page.locator('#main .knowledge-result').first.click();page.wait_for_selector('#formula-dl-backprop-1.located')
 assert page.evaluate("document.activeElement.id")=='formula-dl-backprop-1'
 assert page.locator('.formula.located .katex').count()==1
 page.keyboard.press('/')
 page.locator('#global-search').fill('weight update')
 assert page.locator('#search-results a').count()>0
 page.keyboard.press('ArrowDown');page.keyboard.press('Enter');page.wait_for_selector('.formula.located')
 go('search?q=VOAI%2043&kind=question')
 assert page.locator('#main .knowledge-result').count()==1,(page.url,page.locator('#main .knowledge-result strong').all_text_contents(),page.locator('#main').inner_text()[:300])
 page.locator('#main .knowledge-result').click();page.wait_for_selector('#located-question')
 assert '43' in page.locator('#located-question h2').inner_text()
 page.locator('#located-question summary').click()
 assert page.locator('#located-question img').first.is_visible()
 assert not calls, 'Search must be entirely local'
 # Empty-key validation and pagination of the actual model picker UI.
 go('chat')
 page.locator('#tutor-prompt').fill('Giải thích cập nhật w.')
 page.locator('#tutor-prompt-form button[type=submit]').click()
 assert 'Thêm API key' in page.locator('#tutor-error').inner_text()
 assert not calls
 page.locator('#tutor-key').fill(FAKE_KEY)
 page.locator('#tutor-connect-form button[type=submit]').click()
 page.wait_for_selector('#tutor-model option[value="gemini-test-pro"]',state='attached')
 assert page.locator('#tutor-model option').count()==3
 assert len([c for c in calls if c['type']=='models'])==2
 assert page.locator('#tutor-key').input_value()==''
 assert FAKE_KEY not in page.evaluate("JSON.stringify({...localStorage,...sessionStorage})")
 assert page.locator('#tutor-prompt').input_value()=='Giải thích cập nhật w.'
 page.locator('#tutor-model').select_option('gemini-test-pro')
 page.locator('#tutor-prompt-form button[type=submit]').click()
 page.wait_for_selector('.from-ai .tutor-message-footer')
 chat=[c for c in calls if c['type']=='chat'][-1]
 assert 'gemini-test-pro:streamGenerateContent' in chat['url']
 assert chat['body']['contents']==[{'role':'user','parts':[{'text':'Giải thích cập nhật w.'}]}]
 assert page.locator('.from-ai .katex').count()==1
 assert 'private thought' not in page.locator('.from-ai').inner_text()
 assert page.locator('.from-ai img').count()==0
 assert page.evaluate('window.__tutorXSS||0')==0
 # Multi-turn history is preserved, without attaching site material.
 page.locator('#tutor-prompt').fill('Cho một ví dụ tính tay.')
 page.locator('#tutor-prompt').press('Enter')
 page.wait_for_function("document.querySelectorAll('.from-ai .tutor-message-footer').length===2")
 body=[c for c in calls if c['type']=='chat'][-1]['body']
 assert [c['role'] for c in body['contents']]==['user','model','user']
 assert body['contents'][-1]['parts'][0]['text']=='Cho một ví dụ tính tay.'
 # Quota errors are visible and redact keys; retry is explicit, not automatic.
 mode['value']='quota';page.locator('#tutor-prompt').fill('Giải thích thêm.');page.locator('#tutor-prompt').press('Enter')
 page.wait_for_selector('[data-tutor="retry"]')
 assert 'hạn mức' in page.locator('#tutor-error').inner_text()
 assert FAKE_KEY not in page.locator('#tutor-error').inner_text()
 failed=len([c for c in calls if c['type']=='chat']);page.wait_for_timeout(200)
 assert failed==len([c for c in calls if c['type']=='chat'])
 mode['value']='ok';page.locator('[data-tutor="retry"]').click()
 page.wait_for_function("document.querySelectorAll('.from-ai .tutor-message-footer').length===3")
 body=[c for c in calls if c['type']=='chat'][-1]['body']
 assert len(body['contents'])==5
 # Cancellation does not discard the question.
 mode['value']='hold';page.locator('#tutor-prompt').fill('Một câu hỏi chậm.');page.locator('#tutor-prompt').press('Enter')
 page.wait_for_selector('[data-tutor="stop"]');page.locator('[data-tutor="stop"]').click()
 page.wait_for_selector('[data-tutor="retry"]')
 assert 'Đã dừng' in page.locator('#tutor-error').inner_text()
 for r in held:
  try:r.abort()
  except Exception:pass
 mode['value']='ok'
 # Reload keeps conversation, but not the key. No silent request on reload.
 before=len(calls);page.reload(wait_until='networkidle')
 assert len(calls)==before
 assert page.locator('.from-user').count()>=3
 assert 'Chưa có API key' in page.locator('.tutor-config summary').inner_text()
 assert FAKE_KEY not in page.evaluate("JSON.stringify({...localStorage,...sessionStorage})")
 # Invalid model/key responses and manual model entry remain recoverable.
 mode['value']='badkey';page.locator('#tutor-key').fill(FAKE_KEY);page.locator('#tutor-connect-form button[type=submit]').click()
 page.wait_for_function("document.querySelector('#tutor-error').textContent.includes('từ chối')")
 assert FAKE_KEY not in page.locator('#tutor-error').inner_text()
 page.locator('#tutor-model-manual').fill('../invalid?model')
 page.locator('#tutor-prompt').fill('Test ID không hợp lệ.');before=len(calls);page.locator('#tutor-prompt').press('Enter')
 assert 'ID hợp lệ' in page.locator('#tutor-error').inner_text()
 assert len(calls)==before
 page.locator('[data-tutor="forget-key"]').click()
 page.locator('[data-tutor="new-chat"]').click()
 assert page.locator('.tutor-welcome').is_visible()
 # Responsive checks use a fresh navigation after resizing.
 for width in [1440,390]:
  page.set_viewport_size({'width':width,'height':900})
  for route in ['', 'search?q=cap%20nhat%20w','lesson/dl-backprop?formula=dl-backprop-1','practice?question=voai-43','chat']:
   go(route);page.wait_for_timeout(220)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route)
  page.screenshot(path=f'exam-extracted/tutor-final-{width}.png',full_page=True)
 assert not errors,errors
 print(json.dumps({'passed':True,'live_google_calls':0,'flows':['search ranking and formula location','English aliases','question location','no-key validation','paginated model picker','model switching','streaming and math','multi-turn','quota and explicit retry','cancel','key redaction and memory-only storage','reload','invalid model','new chat','mobile']},ensure_ascii=False))
 browser.close()
