"""Build an editable light Daybreak film. Read-only captures; no app or API writes."""
from pathlib import Path
import json
import re

P = Path(__file__).resolve().parent
C = P / 'compositions'
C.mkdir(exist_ok=True)
DURATION = 52.9
shots = [
    ('storm',0,4.88),('outage',4.88,8.78),('meter',8.78,10.82),
    ('solar',10.82,14.23),('capacity',14.23,19.30),('question',19.30,21.65),
    ('product',21.65,24.40),('workflow',24.40,31.0),('review',31.0,36.88),
    ('dispatch',36.88,39.18),('result',39.18,43.45),('end',43.45,DURATION),
]
common = '''
@font-face{font-family:Archivo;src:url("fonts/Archivo-wdth62_125-wght100_900-latin.woff2") format("woff2");font-weight:100 900;font-stretch:62% 125%;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:Archivo;src:url("fonts/Archivo-wdth62_125-wght100_900-latin-ext.woff2") format("woff2");font-weight:100 900;font-stretch:62% 125%;unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1E00-1EFF,U+2020-202F,U+2C60-2C7F,U+A720-A7FF}
:root{--paper:#fff;--ink:#000f1e;--orange:#fa4616;--blue:#163fe8;--cyan:#00a3e0;--muted:#53616d;--rule:#dce2e5}
*{box-sizing:border-box;margin:0}html,body{width:1920px;height:1080px;overflow:hidden;background:var(--paper);font-family:Archivo,sans-serif;color:var(--ink)}
.title{font-size:144px;line-height:1.04;font-weight:620;letter-spacing:-.055em;font-stretch:100%;color:var(--ink)}
.headline{font-size:94px;line-height:1.08;font-weight:620;letter-spacing:-.045em}
.body{font-size:42px;line-height:1.35;font-weight:420;letter-spacing:-.015em}
.small{font-size:29px;line-height:1.35;font-weight:450;color:var(--muted)}
.side{position:absolute;left:192px;top:340px;width:850px}.side .body{margin-top:38px;max-width:720px}
.object{position:absolute;width:850px;height:850px;object-fit:contain;left:960px;top:90px}
.screen{position:absolute;overflow:hidden;border-radius:18px;border:1px solid #dce2e5;background:#f1f3f3;box-shadow:0 24px 70px rgba(0,15,30,.10)}
.screen img{display:block;width:1920px;height:1080px;max-width:none;transform-origin:0 0}
.foot{position:absolute;left:192px;bottom:62px;font-size:28px;color:var(--muted)}
.line{display:block;overflow:hidden;padding-bottom:.11em;margin-bottom:-.11em}.line span{display:inline-block}
.cursor{position:absolute;width:134px;height:134px;z-index:20;transform-origin:20.833% 12.5%;pointer-events:none}
.cursor svg{width:100%;height:100%;overflow:visible}
'''
(P/'assets/theme.css').write_text(common)

def image(name, id='object', extra=''):
    return f'<img id="{id}" class="object" src="assets/objects/{name}/hero.png" alt="{name}" style="{extra}" />'

def cursor(id):
    # Arrow geometry adapted from the installed agent-cursor registry component.
    return f'<div id="{id}" class="cursor" data-layout-ignore><svg viewBox="0 0 24 24"><path d="M5 3 L5 21 L10.5 16 L14.2 23 L17.6 21.2 L13.9 14.4 L21 14 Z" fill="#fff" stroke="#000f1e" stroke-width="1.2" stroke-linejoin="round"/></svg></div>'

def scene(name, markup, script, css=''):
    script = re.sub(r'tl\.set\(([^;]+?),\{opacity:0\}\);',r'gsap.set(\1,{opacity:0});',script)
    script = script.replace("tl.set('#flow-cursor'", "gsap.set('#flow-cursor'")
    script = script.replace("tl.set('#review-cursor'", "gsap.set('#review-cursor'")
    (C/f'{name}.html').write_text(f'''<template><link rel="stylesheet" href="assets/theme.css"><style>#root{{position:absolute;inset:0;overflow:hidden;background:var(--paper)}}{css}</style>
<div id="root" data-composition-id="{name}" data-width="1920" data-height="1080">{markup}</div>
<script>(function(){{const tl=gsap.timeline({{paused:true}});{script}
window.__timelines=window.__timelines||{{}};window.__timelines["{name}"]=tl;}})();</script></template>''')

scene('storm', '''<div id="name" class="title" style="position:absolute;left:192px;top:360px;font-size:180px">Daybreak</div>
<div id="storm-copy" class="side"><h1 class="title">A storm hits.</h1><p class="body">Banat, Romania.</p></div>'''+image('cloud','cloud','left:970px;top:0;width:950px;height:950px'), '''
tl.set('#storm-copy',{opacity:0});
tl.fromTo('#cloud',{x:60,rotation:-8},{x:0,rotation:0,duration:1.2,ease:'power3.out'},0);
tl.to('#name',{scale:.44,x:-230,y:-268,transformOrigin:'0 0',duration:.65,ease:'power3.inOut'},1.55);
tl.to('#name',{opacity:0,duration:.15},2.12);
tl.fromTo('#storm-copy',{x:70,opacity:0},{x:0,opacity:1,duration:.55,ease:'power3.out'},2.12);
tl.to('#cloud',{x:-55,rotation:3,duration:1.5,ease:'power2.inOut'},2.35);
''')

scene('outage','''<h1 id="out-title" class="headline" style="position:absolute;left:192px;top:105px">Poles fall.</h1>
<div id="out-screen" class="screen" style="left:192px;top:250px;width:1536px;height:750px"><img src="assets/screens/plan.png" alt="Actual Daybreak dispatch console"></div>
<div id="out-caption" class="body" style="position:absolute;left:192px;top:106px;background:white;width:1500px">Homes go dark.</div>
''', '''
gsap.set('#out-screen img',{scale:.8});
tl.set('#out-caption',{opacity:0});
tl.fromTo('#out-screen',{y:70,opacity:0},{y:0,opacity:1,duration:.7,ease:'power3.out'},.05);
tl.to('#out-title',{opacity:0,duration:.12},1.27);
tl.fromTo('#out-caption',{x:40,opacity:0},{x:0,opacity:1,duration:.35,ease:'power3.out'},1.35);
tl.to('#out-screen img',{scale:1.18,x:-50,y:-125,duration:1.0,ease:'power3.inOut'},1.7);
''', '#out-caption{font-size:94px;font-weight:620;letter-spacing:-.045em;line-height:1.08}')

scene('meter','<div class="side"><h1 class="title">Tampered<br>meters.</h1></div>'+image('meter'), '''
tl.fromTo('#object',{rotation:-12,x:180},{rotation:0,x:0,duration:.65,ease:'power3.out'},0);
tl.to('#object',{scale:1.12,duration:.7,ease:'power2.inOut'},.9);
''')

scene('solar','<div class="side" style="top:290px"><h1 class="title">Voltage<br>rises.</h1><p id="solar-detail" class="body">Rooftop solar can overload<br>local lines.</p></div>'+image('solar'), '''
tl.fromTo('#object',{rotation:10,x:130},{rotation:0,x:0,duration:.7,ease:'power3.out'},0);
tl.fromTo('#solar-detail',{opacity:0,y:25},{opacity:1,y:0,duration:.5,ease:'power3.out'},.75);
tl.to('#object',{scale:1.08,duration:.8,ease:'power2.inOut'},1.6);
''')

scene('capacity','''<div id="crews" style="position:absolute;left:230px;top:220px"><div class="title" style="font-size:264px">11</div><div class="body" style="margin-top:20px">field crews</div></div>
<div style="position:absolute;left:890px;top:220px;width:2px;height:425px;background:var(--rule)"></div>
<div id="jobs" style="position:absolute;left:1010px;top:220px"><div class="title" style="font-size:264px">689</div><div class="body" style="margin-top:20px">incoming jobs</div></div>
<p id="cap-note" class="small" style="position:absolute;left:230px;top:750px">Current demo scenario. Includes synthetic data.</p>
'''+image('truck','cap-truck','width:550px;height:550px;left:1130px;top:570px'), '''
tl.fromTo('#jobs',{y:50,opacity:0},{y:0,opacity:1,duration:.6,ease:'power3.out'},1.55);
tl.fromTo('#cap-note',{opacity:0},{opacity:1,duration:.45},2.7);
tl.fromTo('#cap-truck',{x:900,rotation:4},{x:0,rotation:0,duration:1.1,ease:'power3.out'},2.75);
''')

scene('question','''<h1 id="question" class="title" style="position:absolute;left:192px;top:300px;width:1536px;text-align:center;font-size:143px">Where should<br>each crew go?</h1>
''', '''tl.fromTo('#question',{scale:1.12},{scale:1,duration:.65,ease:'power3.out'},0);''')

scene('product','''<h1 id="product-name" class="title" style="position:absolute;left:192px;top:340px;font-size:200px;width:1536px;text-align:center">Daybreak</h1>
<div id="product-screen" class="screen" style="left:192px;top:230px;width:1536px;height:780px"><img src="assets/screens/plan.png" alt="Actual Daybreak console"></div>''', '''
gsap.set('#product-screen img',{scale:.8});
tl.fromTo('#product-name',{scale:.9},{scale:1,duration:.65,ease:'power3.out'},0);
tl.to('#product-name',{y:-275,scale:.48,transformOrigin:'50% 50%',duration:.65,ease:'power3.inOut'},.7);
tl.fromTo('#product-screen',{scale:.68,y:470,opacity:0},{scale:1,y:0,opacity:1,duration:.8,ease:'power3.out'},.7);
''')

scene('workflow','''<div id="flow-screen" class="screen" style="left:192px;top:235px;width:1536px;height:760px"><img id="flow-before" src="assets/screens/plan.png" alt="Daybreak's real plan"><img id="flow-after" style="position:absolute;left:0;top:0" src="assets/screens/route.png" alt="A selected crew's actual work plan"></div>
<h1 id="find" class="headline" style="position:absolute;left:192px;top:105px">Find the problems.</h1>
<h1 id="urgent" class="headline" style="position:absolute;left:192px;top:105px">Urgent ones first.</h1>
<h1 id="routes" class="headline" style="position:absolute;left:192px;top:105px">Efficient routes. Every crew.</h1>
'''+cursor('flow-cursor'), '''
gsap.set('#flow-screen img',{scale:.8});
tl.set(['#urgent','#routes','#flow-after'],{opacity:0});
tl.set('#flow-cursor',{x:950,y:1200});
tl.to('#flow-screen img',{scale:1.65,x:-1760,y:-640,duration:.65,ease:'power3.inOut'},1.25);
tl.set('#find',{opacity:0},1.62);tl.set('#urgent',{opacity:1},1.62);
tl.to('#flow-screen img',{scale:1.8,x:0,y:-1160,duration:.65,ease:'power3.inOut'},3.15);
tl.set('#urgent',{opacity:0},3.47);tl.set('#routes',{opacity:1},3.47);
tl.to('#flow-cursor',{x:1032,y:723,duration:.7,ease:'power3.out'},3.55);
tl.to('#flow-cursor',{scale:.84,duration:.1,ease:'power2.in'},4.25);
tl.set('#flow-after',{opacity:1},4.25);
tl.to('#flow-cursor',{scale:1,duration:.22,ease:'power2.out'},4.35);
tl.to('#flow-cursor',{x:850,y:1200,duration:.5,ease:'power2.in'},4.85);
''')

scene('review','''<h1 id="review-question" class="headline" style="position:absolute;left:192px;top:105px">Is this meter tampered with?</h1>
<h1 id="review-answer" class="headline" style="position:absolute;left:192px;top:105px">The dispatcher decides.</h1>
<div id="review-screen" class="screen" style="left:192px;top:250px;width:1536px;height:690px"><img id="review-image" src="assets/screens/meter-detail.png" alt="Actual meter evidence and human review controls"></div>
<div id="approved" style="position:absolute;left:1040px;top:675px;width:660px;padding:30px 38px;background:#fff;border:1px solid #dce2e5;border-radius:10px;box-shadow:0 12px 30px rgba(0,15,30,.12)"><div class="body" style="font-size:46px;font-weight:600">Ai aprobat</div><p class="small" style="margin-top:14px">Planul se recalculează.</p></div>
<p class="small" style="position:absolute;left:192px;top:975px">Animated demo with synthetic meter data.</p>
'''+cursor('review-cursor'), '''
gsap.set('#review-image',{scale:.8});
tl.set(['#review-answer','#approved'],{opacity:0});tl.set('#review-cursor',{x:1200,y:1200});
tl.to('#review-image',{scale:1.85,x:-2035,y:-274,duration:.75,ease:'power3.inOut'},1.75);
tl.set('#review-question',{opacity:0},2.5);tl.set('#review-answer',{opacity:1},2.5);
tl.to('#review-cursor',{x:393,y:764,duration:.8,ease:'power3.out'},3.35);
tl.to('#review-cursor',{scale:.84,duration:.1,ease:'power2.in'},4.55);
tl.to('#review-cursor',{scale:1,duration:.22,ease:'power2.out'},4.65);
tl.fromTo('#approved',{y:35,opacity:0},{y:0,opacity:1,duration:.35,ease:'power3.out'},4.55);
tl.to('#review-cursor',{x:800,y:1200,duration:.45,ease:'power2.in'},5.05);
''')

scene('dispatch','''<h1 class="title" style="position:absolute;left:192px;top:170px">Ready for<br>daybreak.</h1>
<div id="sun" style="position:absolute;left:1310px;top:310px;width:170px;height:170px;border-radius:50%;background:var(--orange)"></div>
<div style="position:absolute;left:192px;top:770px;width:1536px;height:3px;background:var(--rule)"></div>
'''+image('truck','departure','left:860px;top:190px;width:900px;height:900px'), '''
tl.fromTo('#sun',{y:85,scale:.3},{y:0,scale:1,duration:.8,ease:'power3.out'},0);
tl.fromTo('#departure',{x:-280},{x:200,duration:2.25,ease:'power2.inOut'},0);
''')

report=json.loads((P.parents[1]/'reports/planner/agent_eval.json').read_text())
strategies=report['main']['strategies']
agent=strategies['agent']['km_per_day']; baseline=strategies['primul_venit']['km_per_day']
scene('result',f'''<div id="result-main" style="position:absolute;left:192px;top:180px"><h1 class="title" style="font-size:260px"><span style="font-size:130px;vertical-align:28px;margin-right:15px">≈</span>30%</h1><p class="headline" style="margin-top:22px;font-size:86px">less driving.</p></div>
<div id="comparison" style="position:absolute;left:1140px;top:295px;width:570px"><p class="small">First come, first served</p><div style="margin-top:18px;width:570px;height:40px;background:#cbd3d8"></div><p class="body" style="margin-top:12px">{baseline:.1f} km / day</p><p class="small" style="margin-top:65px">Daybreak</p><div id="result-bar" style="margin-top:18px;width:{570*agent/baseline:.1f}px;height:40px;background:var(--blue);transform-origin:0 50%"></div><p class="body" style="margin-top:12px">{agent:.1f} km / day</p></div>
<p id="fewer" class="body" style="position:absolute;left:192px;top:700px;font-size:58px">Fewer wasted trips.</p>
<p class="small" style="position:absolute;left:192px;top:900px">30-day synthetic simulation. Compared with first come, first served.</p>''', '''
tl.fromTo('#comparison',{x:70,opacity:0},{x:0,opacity:1,duration:.6,ease:'power3.out'},.65);
tl.fromTo('#result-bar',{scaleX:0},{scaleX:1,duration:.9,ease:'power3.out'},.9);
tl.fromTo('#fewer',{y:35,opacity:0},{y:0,opacity:1,duration:.5,ease:'power3.out'},2.0);
''')

scene('end','''<div id="end-name" class="title" style="position:absolute;left:192px;top:310px;width:1536px;text-align:center;font-size:192px;color:#fff">Daybreak</div>
<p id="end-line1" class="body" style="position:absolute;left:192px;top:570px;width:1536px;text-align:center;color:#fff;font-size:56px">Tomorrow’s crews,</p>
<p id="end-line2" class="body" style="position:absolute;left:192px;top:640px;width:1536px;text-align:center;color:#fff;font-size:56px">planned tonight.</p>
<p id="end-audience" class="body" style="position:absolute;left:192px;top:810px;width:1536px;text-align:center;font-size:32px;color:#b4c1cd">For Rețele Electrice dispatchers.</p>
<p id="end-team" class="small" style="position:absolute;left:192px;top:915px;width:1536px;text-align:center;color:#b4c1cd">CyberPunks / SmartHack 2026</p>''', '''
tl.fromTo('#end-name',{scale:1.15},{scale:1,duration:.65,ease:'power3.out'},0);
tl.fromTo('#end-line1',{y:30,opacity:0},{y:0,opacity:1,duration:.5,ease:'power3.out'},1.55);
tl.fromTo('#end-line2',{y:30,opacity:0},{y:0,opacity:1,duration:.5,ease:'power3.out'},2.4);
tl.fromTo('#end-audience',{opacity:0},{opacity:1,duration:.5},4.0);
tl.fromTo('#end-team',{opacity:0},{opacity:1,duration:.5},6.42);
''', '#root{background:#000f1e}')

hosts=[]
for name,start,end in shots:
    hosts.append(f'<div id="w-{name}" class="wrapper"><div id="host-{name}" class="clip" data-start="{start}" data-duration="{end-start:.4f}" data-composition-id="{name}" data-composition-src="compositions/{name}.html" data-width="1920" data-height="1080" data-track-index="1" data-track-kind="graphics"></div></div>')
ledger={'fps':30,'current':'LEFT','seams':[]}
for (before,_,_), (after,start,_) in zip(shots,shots[1:]):
    ledger['seams'].append({'id':before+' to '+after,'cut':start,'technique':'cut-the-curve LEFT','exit':{'selector':'#w-'+before,'axis':'x','dir':-1},'entry':{'selector':'#w-'+after,'axis':'x','dir':-1}})
(P/'ledger.json').write_text(json.dumps(ledger,indent=2))
(P/'index.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>Daybreak · light film</title><script src="assets/vendor/gsap.min.js"></script><link rel="stylesheet" href="assets/theme.css"><style>.wrapper{position:absolute;inset:0}.clip{position:absolute;inset:0}#root{position:absolute;inset:0;background:#fff}</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="52.9" data-width="1920" data-height="1080" data-fps="30">'''+''.join(hosts)+'''<audio id="mix" class="clip" src="assets/local/mix.m4a" data-start="0" data-duration="52.9" data-volume="1" data-track-index="8"></audio></div><script>window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});window.__timelines.main=tl;
// <seams:auto>
// </seams:auto>
</script></body></html>''')
(P/'SPEC.md').write_text('''# Daybreak light redesign

1920×1080, 30 fps, 52.9 s. Rework the supplied v3, preserving its narration clock and local music.

White #FFFFFF, ink #000F1E, PPC-derived orange #FA4616, cyan #00A3E0 and blue #163FE8. Archivo at natural width, 620 display, 420 body. Display 94–264 px, body 42 px, evidence notes 28–32 px. Insets 192 px horizontally. Navy only on the final card.

Reference: the supplied 21.04 s Trust film, for action isolation, quiet backgrounds and clear interaction feedback. No copied branding or claims.

Use real console captures from localhost:3711, the root checkout's running app, captured read only. The current scenario has 689 incoming work items and 11 crews. The commercial music remains local and ignored by Git. Original presentation worktree and supplied MP4 stay untouched.

Keep the supplied voice identity. Replace lines 4 and 9 to match the current scenario and avoid claiming mathematically shortest routes. Numbers come from reports/planner/agent_eval.json. The headline approximately 30 percent is deliberately rounded down from the measured 31.9 percent. Label the 30-day synthetic simulation and comparison strategy on screen.

Banned: tiny planet as a continuous background, confetti markers, stretched heavy type, invented dashboard, gradients, decorative badges, idle drift, unlabeled synthetic evidence. Approval animation uses the real pending screen and the verified success copy from ReviewActions; it does not mutate the shared API.

Current: LEFT, stamped velocity-matched seams. Performance routes: staged text reveals, deliberate camera moves through real screens, one cursor-led selection, one animated review, trucks departing, a sourced bar comparison. The short question holds deliberately before the product reveal.
''')
print('Built',len(shots),'scenes')
