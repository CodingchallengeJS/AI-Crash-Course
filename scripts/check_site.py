"""Browser checks for real study, practice and persistence flows."""
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 context=browser.new_context(viewport={'width':1440,'height':1000})
 page=context.new_page(); errors=[];bad=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:bad.append(r.url) if r.status>=400 and r.url.startswith(BASE) else None)
 def go(route=''):
  page.goto(BASE+'#/'+route,wait_until='networkidle')
  assert not errors,errors
 go()
 data=page.evaluate('({lessons:LESSONS.length,models:MODELS.length,formulas:formulaList().length,questions:QUESTIONS.length})')
 assert data=={'lessons':67,'models':30,'formulas':176,'questions':129},data
 assert page.locator('.mobile-menu').is_hidden()
 # Filtering is a set intersection across sources/topics, union within each group.
 go('practice')
 page.locator('[data-filter-all="topics"]').uncheck()
 assert page.locator('.empty').is_visible()
 page.locator('[data-filter="topics"][value="ML"]').check()
 page.locator('[data-filter="topics"][value="CV"]').check()
 page.locator('[data-filter="sources"][value="VOAI"]').uncheck()
 ids=page.evaluate('filteredQuestions().map(q=>q.id)')
 expected=page.evaluate("QUESTIONS.filter(q=>q.source==='VAIC'&&(q.topics.includes('ML')||q.topics.includes('CV'))).map(q=>q.id)")
 assert ids==expected and len(ids)==len(set(ids))
 # Correct, incorrect, flagged and skipped questions in one session.
 page.evaluate("beginQuiz(['voai-18','voai-37','voai-6','vaic-29','voai-80'])")
 page.wait_for_selector('[data-action="answer"]')
 page.locator('[data-action="answer"][data-value="B"]').click()
 page.locator('[data-action="check-answer"]').click()
 assert 'Chính xác' in page.locator('.answer-explanation').inner_text()
 page.locator('[data-action="next-question"]').click()
 page.locator('[data-action="answer"][data-value="A"]').click()
 page.locator('[data-action="check-answer"]').click()
 assert '0.9183' in page.locator('.answer-explanation').inner_text()
 page.reload(wait_until='networkidle')
 assert page.evaluate('state.session.index')==1
 assert page.evaluate("state.answers['voai-37'].correct") is False
 page.locator('[data-action="next-question"]').click()
 page.locator('[data-action="answer"][data-value="C"]').click()
 page.locator('[data-action="check-answer"]').click()
 assert page.evaluate("state.answers['voai-6'].correct") is None
 page.locator('[data-action="zoom-question"]').click()
 assert page.locator('#image-dialog').is_visible()
 page.locator('[data-action="close-zoom"]').click()
 page.locator('[data-action="finish-quiz"]').click()
 assert '1/3' in page.locator('.result-summary h2').inner_text()
 assert '2 chưa trả lời' in page.locator('.result-summary').inner_text()
 page.locator('[data-action="retry-wrong"]').click()
 assert page.evaluate('state.session.ids')==['voai-37','voai-80']
 # Timed mode does not reveal answers before submission; deadline auto-submits.
 page.evaluate("beginQuiz(['voai-18','voai-37'],'exam')")
 page.locator('[data-action="answer"][data-value="B"]').click()
 assert page.locator('.answer-explanation').count()==0
 page.evaluate('state.session.deadline=Date.now()-100;updateTimer()')
 page.wait_for_selector('.result-summary')
 assert page.evaluate('state.session.finished') is True
 # Completion and notes persist; formula bookmarking works.
 go('lesson/ml-tree')
 page.locator('#lesson-notes').fill('Tính impurity phải có trọng số số mẫu.')
 page.locator('[data-action="complete"]').click()
 page.reload(wait_until='networkidle')
 assert page.locator('#lesson-notes').input_value()=='Tính impurity phải có trọng số số mẫu.'
 assert page.locator('[data-action="complete"]').get_attribute('aria-pressed')=='true'
 page.locator('[data-action="formula-star"]').first.click()
 go('formulas');assert page.locator('.katex').count()==176
 assert page.locator('.katex-error').count()==0
 # Calculators, including invalid inputs and weighted child impurity.
 assert '0.48' in page.locator('#calc-result').inner_text()
 page.locator('#calc-counts').fill('-1,4')
 assert 'không âm' in page.locator('#calc-result').inner_text()
 page.locator('[data-action="calculator"][data-value="gain"]').click()
 assert '0.41997' in page.locator('#calc-result').inner_text()
 page.locator('[data-action="calculator"][data-value="linkage"]').click()
 assert 'Ward' in page.locator('#calc-result').inner_text() and '36' in page.locator('#calc-result').inner_text()
 page.locator('[data-action="calculator"][data-value="conv"]').click()
 assert '448' in page.locator('#calc-result').inner_text()
 # Two-model comparison; keyboard-search and diacritic-free matching.
 go('models')
 page.locator('[data-compare="bert"]').check()
 page.locator('[data-compare="gpt"]').check()
 page.locator('[data-compare="unet"]').click()
 assert not page.locator('[data-compare="unet"]').is_checked()
 assert page.evaluate('state.compare.length')==2
 page.locator('[data-action="compare"]').click()
 page.wait_for_selector('.compare-table')
 page.keyboard.press('/')
 page.locator('#global-search').fill('chu y')
 assert page.locator('#search-results a').count()>0
 page.keyboard.press('Escape')
 # Every lesson/model route renders; no missing formula or asset paths.
 for ident in page.evaluate('LESSONS.map(l=>l.id)'):
  go('lesson/'+ident)
  assert page.locator('h1').count()==1
  assert page.locator('.katex-error').count()==0,ident
 for ident in page.evaluate('MODELS.map(m=>m.id)'):
  go('model/'+ident)
  assert page.locator('.architecture-diagram').count()==1
  page.locator('.node').nth(1).click()
  assert 'Khối2' in page.locator('#node-description').inner_text()
 for src in page.evaluate('QUESTIONS.flatMap(q=>[...q.images,...q.context])'):
  assert context.request.get(BASE+src).status==200,src
 # Desktop and mobile horizontal overflow, representative routes.
 for width in [1440,390]:
  page.set_viewport_size({'width':width,'height':900})
  for r in ['', 'learn/ML','lesson/dl-attention','models','model/unet','formulas','practice','plan']:
   go(r)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,r)
  go('');page.screenshot(path=f'exam-extracted/final-{width}.png',full_page=True)
 assert not errors,errors
 assert not bad,bad
 print(json.dumps({'passed':True,'data':data,'routes':'67 lessons + 30 models','flows':['filters','scoring','flagged exclusions','resume','timeout','notes','progress','calculators','comparison','search','image assets','mobile overflow'],'errors':errors},ensure_ascii=False))
 browser.close()
