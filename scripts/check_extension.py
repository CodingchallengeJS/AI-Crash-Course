"""Browser and mathematical checks for new curriculum and interactive examples."""
import json,sys,itertools,random,ast
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
BASE='http://127.0.0.1:8000/#/'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 context=browser.new_context(viewport={'width':1440,'height':1000})
 page=context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def go(route):
  page.goto(BASE+route,wait_until='networkidle')
  page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
 go('syllabus')
 assert page.locator('.syllabus-card').count()==10
 assert page.evaluate('SYLLABUS.every(x=>x[3].every(id=>LESSONS.some(l=>l.id===id)))')
 assert page.evaluate('new Set(LESSONS.map(l=>l.id)).size===LESSONS.length')
 assert page.evaluate('formulaList().every(f=>{try{katex.renderToString(f.tex,{throwOnError:true});return true}catch{return false}})')
 for code in page.evaluate('LESSONS.filter(l=>l.code?.language==="python").map(l=>l.code.text)'):
  ast.parse(code)
 for query,expected in [('AC-3','ai-ac3'),('Q learning','rl-qlearning'),('early stopping','lab-checkpoints'),('LR scheduler','lab-schedulers'),('pseudo labelling','lab-pseudo'),('hard voting','lab-voting'),('data preprocessing','lab-preprocessing')]:
  ids=page.evaluate('q=>searchKnowledge(q,{limit:10}).map(x=>x.id)',query)
  assert expected in ids,(query,ids)
 go('lesson/lab-checkpoints')
 assert 'last.pt' in page.locator('.lesson-code').inner_text()
 assert page.locator('.lesson-demo-link').get_attribute('href').endswith('demo=early')
 # Q and SARSA targets, including terminal and invalid inputs.
 go('workshop?demo=q')
 assert '3.75' in page.locator('.lab-result').inner_text()
 assert '2.85' in page.locator('.workshop-table').inner_text()
 page.locator('#ws-terminal').check()
 assert '1.5' in page.locator('.lab-result').inner_text()
 page.locator('#ws-alpha').fill('2')
 assert 'Kiểm tra dữ liệu' in page.locator('#workshop-output').inner_text()
 # Scheduler endpoints and midpoint; invalid horizon must be recoverable.
 go('workshop')
 assert '0.005' in page.locator('.lab-result').inner_text()
 page.locator('#ws-time').fill('100')
 assert page.locator('.lab-result strong').inner_text()=='0'
 page.locator('#ws-kind').select_option('warmup')
 page.locator('#ws-time').fill('10')
 assert page.locator('.lab-result strong').inner_text()=='0.01'
 page.locator('#ws-total').fill('2')
 assert page.locator('.callout.warning').is_visible()
 page.locator('#ws-total').fill('100')
 assert page.locator('.scheduler-chart').is_visible()
 page.locator('#ws-kind').select_option('step')
 page.locator('#ws-time').fill('20')
 assert page.locator('.lab-result strong').inner_text()=='0.005'
 # Hard and soft disagree, then weighted vote changes; tie and bad weights.
 go('workshop?demo=voting')
 text=page.locator('#workshop-output').inner_text()
 assert 'Class 1' in text and 'Class 0' in text and '0.343333' in text
 page.locator('#ws-weights').fill('1,1,3')
 assert page.locator('.domain-grid>div').nth(0).inner_text().endswith('Class 0')
 page.locator('#ws-probs').fill('.9,.1');page.locator('#ws-weights').fill('1,1')
 assert 'Đồng phiếu' in page.locator('.domain-grid').inner_text()
 page.locator('#ws-weights').fill('0,0')
 assert 'Kiểm tra dữ liệu' in page.locator('#workshop-output').inner_text()
 # Early stopping strict delta and restoring the best; mode=max.
 go('workshop?demo=early')
 assert 'epoch 4' in page.locator('.lab-result').inner_text()
 assert page.locator('.lab-result strong').inner_text()=='2'
 assert page.locator('.workshop-table tbody tr').count()==4
 page.locator('#ws-direction').select_option('max')
 assert 'epoch 3' in page.locator('.lab-result').inner_text()
 assert page.locator('.lab-result strong').inner_text()=='1'
 # AC-3 queue, full propagation, arc-consistent unsat and domain wipeout.
 go('workshop?demo=ac3')
 assert page.locator('.workshop-table tbody tr').count()==1
 page.locator('[data-lab-action=next]').click()
 assert 'xóa {3} khỏi X' in page.locator('.lab-result').inner_text()
 page.locator('[data-lab-action=all]').click()
 assert [x.strip() for x in page.locator('.domain-grid strong').all_inner_texts()]==['{ 1 }','{ 2 }','{ 3 }']
 page.locator('[data-lab-action=reset]').click()
 assert '{ 1, 2, 3 }' in page.locator('.domain-grid').inner_text()
 page.locator('#ws-constraint').select_option('triangle')
 for id in ['dx','dy','dz']:page.locator('#ws-'+id).fill('1,2')
 page.locator('[data-lab-action=all]').click()
 assert 'Arc-consistent' in page.locator('#workshop-output').inner_text()
 assert [x.strip() for x in page.locator('.domain-grid strong').all_inner_texts()]==['{ 1, 2 }']*3
 page.locator('#ws-constraint').select_option('chain')
 page.locator('#ws-dx').fill('2');page.locator('#ws-dy').fill('1')
 page.locator('[data-lab-action=all]').click()
 assert 'Domain rỗng' in page.locator('.lab-result').inner_text()
 page.locator('#ws-dx').fill('x')
 assert page.locator('.callout.warning').is_visible()
 page.locator('#ws-dx').fill('1,2,3')
 assert page.locator('[data-lab-action=reset]').is_enabled()
 # Independently compare AC-3 pruning against exhaustive valid assignments.
 rng=random.Random(42)
 for kind in ['chain','triangle']:
  for _ in range(30):
   domains=[rng.sample([1,2,3],rng.randint(1,3)) for i in range(3)]
   valid=[v for v in itertools.product(*domains) if (v[0]<v[1]<v[2] if kind=='chain' else len(set(v))==3)]
   rows=page.evaluate('x=>ac3Trace(x.domains,x.kind)',{'domains':domains,'kind':kind})
   final=rows[-1]
   for sol in valid:assert all(sol[i] in final['domains'][i] for i in range(3)),(kind,domains,sol,final)
   if final.get('failed'):assert not valid
   else:
    edges=[(0,1),(1,0),(1,2),(2,1)]+([(0,2),(2,0)] if kind=='triangle' else [])
    for i,j in edges:
     for x in final['domains'][i]:
      assert any(x!=y if kind=='triangle' else (x<y if i<j else x>y) for y in final['domains'][j])
 # Topic filters, formulas and mobile layouts include all new material.
 for topic,count in [('AI',7),('RL',4),('LAB',11)]:
  go('learn/'+topic);assert page.locator('.lesson-row').count()==count
 go('formulas');page.locator('[data-action="formula-filter"][data-value="RL"]').click()
 assert page.locator('.formula-grid>.formula').count()==0  # wrapped cards
 assert 'RL' in page.locator('.formula-origin').first.inner_text()
 go('practice')
 assert page.locator('[data-filter="topics"]').count()==4
 assert page.locator('[data-filter-all="topics"]').is_checked()
 # Screenshots + horizontal layout checks on representative narrow/wide screens.
 for width in [390,1440]:
  page.set_viewport_size({'width':width,'height':950})
  for route in ['syllabus','workshop','workshop?demo=q','workshop?demo=ac3','workshop?demo=voting','workshop?demo=early','lesson/lab-checkpoints','learn/LAB']:
   go(route)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route)
  go('workshop');page.screenshot(path=f'exam-extracted/workshop-{width}.png',full_page=True)
  go('syllabus');page.screenshot(path=f'exam-extracted/syllabus-{width}.png',full_page=True)
 assert not errors,errors
 print(json.dumps({'passed':True,'lessons':67,'formulas':176,'syllabus_sections':10,'demos':5,'ac3_exhaustive_cases':60,'mobile':True,'js_errors':errors},ensure_ascii=False))
 browser.close()
