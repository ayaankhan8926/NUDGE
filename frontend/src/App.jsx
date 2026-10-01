import { useEffect, useMemo, useState } from "react";

import { Activity, AlertTriangle, ArrowRight, CalendarDays, Check, ChevronDown, Clock3, Download, FileSpreadsheet, FlaskConical, Info, Keyboard, Mail, Pause, Play, RotateCcw, Shield, ShieldAlert, Sparkles, Square, Terminal, Undo2, X, Zap } from "lucide-react";

import "./index.css";



const API_BASE = "https://nudge-gamma-eight.vercel.app";

const STORE = "nudge-workspace-v3";

const HISTORY = "nudge-history-v3";

const EXAMPLES = [

  "Check the invoice sheet and follow up with clients who have not replied",

  "Find unanswered client emails and prepare follow-ups",

  "Review today's meetings and prepare the required follow-up tasks",

];

const INITIAL = { source: "Demo workspace · synthetic data", invoices: [

  {client:"ABC Technologies",invoice:"INV-1042",amount:45000,due_date:"2026-09-28",state:"REPLIED"},

  {client:"XYZ Solutions",invoice:"INV-1043",amount:32000,due_date:"2026-09-25",state:"OVERDUE",emailId:null},

  {client:"Nova Systems",invoice:"INV-1044",amount:58000,due_date:"2026-09-20",state:"REPLIED"}

], sentEmails:[], sheetUpdates:[] };

const load = (k,f) => { try { const v=localStorage.getItem(k); return v?JSON.parse(v):f; } catch { return f; } };

const money = n => `₹${Number(n||0).toLocaleString("en-IN")}`;

const time = () => new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"});

const id = () => `${Date.now()}-${Math.random().toString(36).slice(2,7)}`;

const iconFor = t => ({thinking:Sparkles,plan:Terminal,working:Activity,success:Check,risk:ShieldAlert,blocked:X,recovered:RotateCcw,waiting:Clock3}[t]||Activity);



export default function App(){

  const [goal,setGoal]=useState(""); const [workspace,setWorkspace]=useState(()=>load(STORE,INITIAL)); const [history,setHistory]=useState(()=>load(HISTORY,[]));

  const [trace,setTrace]=useState([]); const [stage,setStage]=useState("idle"); const [runId,setRunId]=useState(null); const [agent,setAgent]=useState(null);

  const [approval,setApproval]=useState(false); const [decision,setDecision]=useState(null); const [message,setMessage]=useState(""); const [original,setOriginal]=useState("");

  const [subject,setSubject]=useState("Follow-up regarding your invoice"); const [originalSubject,setOriginalSubject]=useState("Follow-up regarding your invoice");

  const [rejectReason,setRejectReason]=useState(""); const [countdown,setCountdown]=useState(0); const [chaos,setChaos]=useState(false); const [paused,setPaused]=useState(false);

  const [modal,setModal]=useState(null); const [expanded,setExpanded]=useState({}); const [error,setError]=useState(""); const [tab,setTab]=useState("trace");



  useEffect(()=>{document.title="NUDGE: Autonomous work, with a human leash"},[]);

  useEffect(()=>{if(!approval||countdown<=0)return; const t=setInterval(()=>setCountdown(v=>{if(v<=1){clearInterval(t);setApproval(false);setStage("completed");add({type:"blocked",title:"Approval timed out",detail:"Approval timed out, action not executed.",icon:Clock3});return 0}return v-1}),1000);return()=>clearInterval(t)},[approval,countdown]);

  useEffect(()=>{const h=e=>{if(!approval||["INPUT","TEXTAREA"].includes(e.target.tagName))return;if(e.key.toLowerCase()==="a")approve();if(e.key.toLowerCase()==="e")setDecision("editing");if(e.key.toLowerCase()==="r")setDecision("rejecting")};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)});



  const add = entry => setTrace(v=>[...v,{...entry,id:id(),time:time()}]);

  const saveWorkspace = w => {setWorkspace(w);localStorage.setItem(STORE,JSON.stringify(w))};

  const saveHistory = h => {const n=[h,...history].slice(0,15);setHistory(n);localStorage.setItem(HISTORY,JSON.stringify(n))};

  const action=agent?.action||{}; const payload=action.payload||{}; const invoice=useMemo(()=>workspace.invoices.find(x=>x.invoice===payload.invoice_id)||workspace.invoices[1],[workspace,payload.invoice_id]);

  const already=workspace.sentEmails.some(x=>x.invoice_id===invoice?.invoice); const isSheet=action.action==="update_sheet";



  const newRun=()=>{setGoal("");setTrace([]);setStage("idle");setAgent(null);setRunId(null);setApproval(false);setDecision(null);setMessage("");setRejectReason("");setCountdown(0);setPaused(false);setError("");setExpanded({});setTab("trace")};
  const reset=()=>{const n=JSON.parse(JSON.stringify(INITIAL));saveWorkspace(n);newRun()};



  async function start(g=goal){

    if(!g.trim()||stage!=="idle")return; setGoal(g);setTrace([]);setAgent(null);setRunId(null);setApproval(false);setDecision(null);setStage("planning");setTab("trace");

    add({type:"thinking",title:"Understanding your goal",detail:g}); add({type:"plan",title:"Sending goal to NUDGE planner",detail:"Backend agent is creating an execution plan"});

    try{

      const r=await fetch(`${API_BASE}/api/agent/run`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({goal:g.trim(),workspace_state:workspace,demo_mode:true})});

      const d=await r.json(); if(!r.ok)throw Error(d.error||"Agent request failed"); setAgent(d);setRunId(d.run_id);

      add({type:"success",title:"Plan generated",detail:`${d.plan?.steps?.length||4} execution steps created`,result:d.plan});

      add({type:"working",title:"Inspecting workspace",detail:"Reading invoice, Gmail and Calendar demo fixtures",args:{tools:["sheets","gmail","calendar"]}});

      add({type:"success",title:"Workspace analyzed",detail:`${d.analysis?.follow_up_candidates?.length||0} follow-up candidate(s) identified`,result:d.analysis});

      if(already){setAgent({...d,status:"completed",idempotent_skip:true});add({type:"success",title:"Duplicate run skipped",detail:`${invoice.invoice} was already followed up. No duplicate email will be sent.`,icon:Shield});add({type:"success",title:"Run summary",detail:"No new action required.",icon:Check});setStage("completed");saveHistory({id:id(),goal:g,status:"completed",summary:"Duplicate follow-up skipped",at:new Date().toISOString()});return}

      if(d.status==="approval_required"){setMessage(payload.message||d.action?.payload?.message||"");setOriginal(payload.message||d.action?.payload?.message||"");setSubject(d.action?.payload?.subject||"Follow-up regarding your invoice");setOriginalSubject(d.action?.payload?.subject||"Follow-up regarding your invoice");setCountdown(90);add({type:"risk",title:"Risk gate triggered",detail:"External email requires a human decision.",args:{tier:"NUDGE",action:d.action?.action}});add({type:"working",title:"Follow-up prepared",detail:`${d.action?.payload?.client||"Client"} · ${d.action?.payload?.invoice_id||"Invoice"}`,icon:Mail,result:d.action?.payload});setStage("approval");setApproval(true);return}

      setStage("completed");add({type:"success",title:"Run completed",detail:"No risky action required."});

    }catch(e){setStage("completed");setError(e.message);add({type:"blocked",title:"Agent request failed",detail:e.message,icon:X})}

  }



  async function approve(){

    if(!runId||!agent||paused)return; const a=agent.action?.action||"action";setApproval(false);setDecision("approved");setCountdown(0);setStage("executing");

    add({type:"success",title:"Human approval received",detail:`Decision: APPROVE · ${a}`,icon:Check});add({type:"working",title:"Sending approval to backend",detail:"Human decision recorded",icon:Shield});

    try{

      const r=await fetch(`${API_BASE}/api/agent/${runId}/approve`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({run:agent})});const d=await r.json();if(!r.ok)throw Error(d.error||"Approval failed");const run=d.run||{};setAgent({...agent,...run,status:d.status,run_id:run.run_id||agent.run_id});

      const ex=run.execution_result||{};const email=ex?.execution?.email||ex?.email||run?.observation?.latest_email;const update=ex?.execution?.update||ex?.update||run?.observation?.latest_sheet_update;

      add({type:"working",title:a==="update_sheet"?"Executing approved sheet update":"Executing approved email",detail:payload.client||email?.client||update?.client||"Approved action",result:ex});add({type:"success",title:"Action completed",detail:ex.message||"Approved action executed.",icon:Check});

      let w=workspace;if(email?.invoice_id){w={...w,sentEmails:[...w.sentEmails,email],invoices:w.invoices.map(x=>x.invoice===email.invoice_id?{...x,state:"FOLLOW-UP SENT",emailId:email.email_id}:x)};saveWorkspace(w);add({type:"success",title:"Email execution verified",detail:`${email.email_id} · ${email.client}`,icon:Mail,result:email})}

      if(update?.invoice_id){w={...w,sheetUpdates:[...w.sheetUpdates,update],invoices:w.invoices.map(x=>x.invoice===update.invoice_id?{...x,state:"FOLLOW-UP SENT",sheetUpdated:true}:x)};saveWorkspace(w);add({type:"success",title:"Sheet update verified",detail:`${update.invoice_id} · ${update.client||"client"}`,icon:FileSpreadsheet,result:update})}

      setStage("replanning");add({type:"thinking",title:"Observing execution",detail:"Checking what changed after the approved action",icon:Activity});if(run.observation)add({type:"success",title:"Workspace change detected",detail:run.observation.observation||"Execution result verified",icon:Check,result:run.observation});add({type:"thinking",title:"Replanning",detail:"NUDGE is deciding whether another action is required",icon:RotateCcw});

      if(run.replanning?.decision==="complete"){add({type:"success",title:"Replan complete",detail:run.replanning.reason||"No further action required",icon:Check});add({type:"success",title:"Run summary",detail:"Approved action completed and verified.",icon:Check});setStage("completed");saveHistory({id:id(),goal,status:"completed",summary:"Completed with human approval",at:new Date().toISOString()});return}

      if(d.status==="approval_required"&&run.action){const p=run.action.payload||{};setAgent({...agent,...run,status:"approval_required"});setMessage(p.message||`Record the approved follow-up for ${p.invoice_id||"the invoice"} in the invoice sheet.`);setOriginal(p.message||"");setCountdown(90);add({type:"risk",title:"Replan requires approval",detail:run.replanning?.reason||"The next action needs a human decision.",icon:ShieldAlert});add({type:"working",title:"Next action prepared",detail:`${p.invoice_id||"Invoice"} · ${p.client||"Client"}`,icon:FileSpreadsheet});setStage("approval");setApproval(true);return}

      setStage("completed");

    }catch(e){setStage("completed");add({type:"blocked",title:"Approval execution failed",detail:e.message,icon:X})}

  }



  async function edit(){

    if(!runId||!agent||!message.trim())return;try{const r=await fetch(`${API_BASE}/api/agent/${runId}/edit`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:message.trim(),subject:subject.trim(),run:agent})});const d=await r.json();if(!r.ok)throw Error(d.error||"Edit failed");setAgent({...agent,...(d.run||{})});setDecision(null);setCountdown(90);add({type:"thinking",title:"Action edited by human",detail:"The edited text is saved and still requires approval.",icon:Sparkles,result:{subject,body:message}})}catch(e){add({type:"blocked",title:"Edit failed",detail:e.message,icon:X})}}

  async function reject(){if(!runId||!agent)return;setApproval(false);setCountdown(0);setStage("replanning");add({type:"blocked",title:"Human rejected action",detail:rejectReason||"No reason supplied. NUDGE will not bypass the rejection.",icon:X});try{const r=await fetch(`${API_BASE}/api/agent/${runId}/reject`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reason:rejectReason,run:agent})});const d=await r.json();if(!r.ok)throw Error(d.error||"Reject failed");add({type:"thinking",title:"Replanning after rejection",detail:d.run?.replanning?.reason||"Rejected effect will not be attempted another way.",icon:RotateCcw});add({type:"success",title:"Run stopped safely",detail:"No workaround was attempted.",icon:Shield});setStage("completed");saveHistory({id:id(),goal,status:"rejected",summary:rejectReason||"Action rejected",at:new Date().toISOString()})}catch(e){setStage("completed");add({type:"blocked",title:"Reject request failed",detail:e.message,icon:X})}}



  const pause=()=>{setPaused(!paused);add({type:"waiting",title:paused?"Run resumed":"Run paused",detail:paused?"Execution resumed.":"Execution paused by human control.",icon:paused?Play:Pause})};

  const stop=()=>{setApproval(false);setStage("completed");add({type:"blocked",title:"Run cancelled",detail:"The user stopped the run. No new action will be attempted.",icon:Square})};

  const exportAudit=()=>{const b=new Blob([JSON.stringify({product:"NUDGE",source:workspace.source,run_id:runId,goal,trace,workspace,history},null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="nudge-audit-log.json";a.click()};

  const undo=()=>{const u=workspace.sheetUpdates.at(-1);if(!u)return;saveWorkspace({...workspace,sheetUpdates:workspace.sheetUpdates.slice(0,-1),invoices:workspace.invoices.map(x=>x.invoice===u.invoice_id?{...x,sheetUpdated:false}:x)});add({type:"success",title:"Undo completed",detail:`Reverted demo sheet update for ${u.invoice_id}.`,icon:Undo2})};

  const stageLabel={idle:"WAITING FOR GOAL",planning:"PLANNING",executing:"EXECUTING",approval:"AWAITING HUMAN DECISION",replanning:"REPLANNING",completed:"RUN COMPLETE"}[stage];

  const workflow=[["01","PLAN","Break the goal into actions"],["02","ACT","Use connected tools"],["03","OBSERVE","Check what happened"],["04","ASK","Human decides risky actions"]];



  return <div className={`nudge-app ${approval?"approval-active":""}`}>

    <header className="topbar"><div className="brand"><div className="brand-symbol"><Zap size={17}/></div><div><div className="brand-title">NUDGE</div><div className="brand-subtitle">Autonomous work, with a human leash.</div></div></div><div className="top-right"><span className="source-badge"><Info size={12}/> DEMO WORKSPACE · SYNTHETIC DATA</span><div className={`top-status ${stage}`}><span className="status-light"/>{stageLabel}<span className="separator">/</span>SUPERVISED AGENT</div></div></header>

    <main className="page">

      <section className="hero compact"><div><div className="eyebrow"><span/>AGENT CONTROL PLANE</div><h1>Give NUDGE<br/><em>something to do.</em></h1><p>One goal. Multiple apps. Human control. NUDGE plans the work, operates connected tools, and stops when your decision matters.</p></div><div className="hero-meta"><div><span>MODE</span><strong>SUPERVISED</strong></div><div><span>TOOLS</span><strong>03 READY</strong></div><button onClick={()=>setModal("policy")}><span>RISK POLICY</span><strong>ENFORCED ↗</strong></button></div></section>

      <section className="workflow">{workflow.map(([n,t,d],i)=><div className="workflow-wrap" key={t}><div className={`workflow-step ${["executing","approval","replanning","completed"].includes(stage)&&i<2?"done":""} ${stage===t.toLowerCase()?"active":""}`}><b>{n}</b><div><strong>{t}</strong><small>{d}</small></div></div>{i<3&&<ArrowRight size={14}/>}</div>)}</section>

      <section className="goal"><div className="section-kicker">GOAL <span>WHAT SHOULD I DO?</span></div><div className="goal-grid"><div><textarea value={goal} onChange={e=>setGoal(e.target.value)} disabled={stage!=="idle"} placeholder="Describe the outcome you want. NUDGE decides how to get there..."/><div className="chips">{EXAMPLES.map(x=><button key={x} disabled={stage!=="idle"} onClick={()=>setGoal(x)}>{x}</button>)}</div></div><button className="run-button" disabled={!goal.trim()||stage!=="idle"} onClick={()=>start()}>{stage==="idle"?<>RUN AGENT <ArrowRight size={17}/></>:<><Activity size={16}/> AGENT ACTIVE</>}</button></div><div className="controls"><button onClick={()=>start(EXAMPLES[0])} disabled={stage!=="idle"}><Play size={14}/> RUN GUIDED DEMO</button>{stage!=="idle"&&stage!=="completed"&&<button onClick={pause}><Pause size={14}/> {paused?"RESUME":"PAUSE"}</button>}{stage!=="idle"&&stage!=="completed"&&<button onClick={stop}><Square size={14}/> STOP RUN</button>}<button onClick={newRun}><Play size={14}/> NEW RUN</button><button onClick={reset}><RotateCcw size={14}/> RESET DEMO</button><label><input type="checkbox" checked={chaos} onChange={e=>setChaos(e.target.checked)}/> CHAOS MODE</label></div></section>

      <section className="run-head"><div><div className="eyebrow">LIVE EXECUTION</div><h2>Agent activity</h2></div><div className={`run-state ${stage}`}><span/>{stageLabel}</div></section>

      <div className="mobile-tabs">{["trace","workspace"].map(x=><button className={tab===x?"active":""} key={x} onClick={()=>setTab(x)}>{x}</button>)}</div>

      <div className="main-grid">

        <section className={`trace-section ${tab!=="trace"?"mobile-hide":""}`}><div className="trace-head"><div className="trace-title"><Terminal size={15}/> GLASS-BOX TRACE</div><span> {stage==="idle"?"NO ACTIVE RUN":runId?`RUN-${runId.slice(0,8).toUpperCase()}`:"RUN-ACTIVE"}</span></div><div className="trace-body" aria-live="polite">{trace.length===0?<div className="empty"><Terminal size={18}/><strong>Your execution trace will appear here.</strong><span>Every plan, tool call, observation, replan and human decision is visible.</span></div>:trace.map(x=>{const I=x.icon||iconFor(x.type);return <div className={`trace-row ${x.type}`} key={x.id}><time>{x.time}</time><i><I size={13}/></i><div><div className="trace-title-row"><strong>{x.title}</strong>{x.type==="risk"&&<em>HUMAN GATE</em>}</div><span>{x.detail}</span>{(x.args||x.result)&&<button className="details" onClick={()=>setExpanded(v=>({...v,[x.id]:!v[x.id]}))}>{expanded[x.id]?"HIDE":"VIEW"} DETAILS <ChevronDown size={11}/></button>}{expanded[x.id]&&<pre>{JSON.stringify({args:x.args,result:x.result},null,2)}</pre>}</div></div>})}</div>

          {approval&&<div className="approval-wrap"><div className="approval"><div className="approval-top"><b><ShieldAlert size={15}/> NUDGE MOMENT</b><span>HUMAN DECISION REQUIRED · {countdown}s</span></div><div className="approval-title"><ShieldAlert size={24}/><div><h3>{isSheet?"Update the invoice sheet":`Send email to ${payload.client||"external client"}`}</h3><p>{isSheet?"Workspace data will change.":"This sends content to an external client. NUDGE stopped before execution."}</p></div></div><div className="evidence"><div className="riskline"><b>RISK TIER · {isSheet?"REVERSIBLE-AUTO":"NUDGE"}</b><span>{isSheet?"Review before commit.":"Irreversible: external communication."}</span></div><div className="evidence-grid"><div><span>CLIENT</span><strong>{payload.client||invoice?.client}</strong></div><div><span>INVOICE</span><strong>{payload.invoice_id||invoice?.invoice}</strong></div><div><span>AMOUNT</span><strong>{money(payload.amount||invoice?.amount)}</strong></div><div><span>DUE DATE</span><strong>{invoice?.due_date||"—"}</strong></div><div><span>REPLY</span><strong>No reply found</strong></div><div><span>SOURCE</span><strong>Gmail + Sheets</strong></div></div></div><div className="proposal">{!isSheet&&<label>SUBJECT<input value={subject} disabled={decision!=="editing"} onChange={e=>setSubject(e.target.value)}/></label>}<label>{isSheet?"SHEET ACTION":"MESSAGE"}<textarea value={message} disabled={decision!=="editing"} onChange={e=>setMessage(e.target.value)}/></label>{decision==="editing"&&<div className="diff"><b>EDIT DIFF</b><div><small>OLD</small><pre>{originalSubject}\n{original}</pre></div><div><small>NEW</small><pre>{subject}\n{message}</pre></div></div>}<div className="approval-actions"><button className="danger" onClick={()=>setDecision("rejecting")}><X size={15}/> REJECT <kbd>R</kbd></button>{decision==="editing"?<button onClick={edit}><Check size={15}/> SAVE EDIT <kbd>E</kbd></button>:<button onClick={()=>setDecision("editing")}><Sparkles size={15}/> EDIT <kbd>E</kbd></button>}<button className="approve" onClick={approve} disabled={paused}><Check size={15}/> APPROVE <kbd>A</kbd></button></div>{decision==="rejecting"&&<div className="reject-box"><input autoFocus value={rejectReason} onChange={e=>setRejectReason(e.target.value)} placeholder="Optional reason: Not yet, call them first."/><button onClick={reject}>CONFIRM REJECT</button></div>}<small className="keyboard"><Keyboard size={12}/> A approve · E edit · R reject</small></div></div></div>}

        </section>

        <aside className={`workspace ${tab!=="workspace"?"mobile-hide":""}`}><div className="panel-head"><div><div className="eyebrow">WORKSPACE</div><h3>Connected tools</h3></div><b>03</b></div>{[[Mail,"GMAIL","Email search & drafts"],[CalendarDays,"CALENDAR","Events & reminders"],[FileSpreadsheet,"SHEETS","Invoice tracking"]].map(([I,n,d])=><div className="tool" key={n}><i><I size={17}/></i><div><strong>{n}</strong><span>{d}</span></div><em>DONE</em></div>)}<div className="source"><Info size={12}/> {workspace.source}</div><div className="workspace-section"><div className="section-kicker">INVOICE QUEUE <span>{workspace.invoices.filter(x=>x.state==="FOLLOW-UP SENT").length}/3 handled</span></div>{workspace.invoices.map(x=><div className="invoice" key={x.invoice}><div><strong>{x.client}</strong><span>{x.invoice} · {money(x.amount)}</span><small>DUE {x.due_date}</small></div><em className={x.state.toLowerCase().replaceAll(" ","-")}>{x.state}</em></div>)}</div><div className="workspace-section"><div className="section-kicker">ACTION LEDGER</div>{[["Read invoice sheet",true],["Search Gmail",true],["Send follow-up email",workspace.sentEmails.length>0],["Update invoice sheet",workspace.sheetUpdates.length>0],["Observe & replan",stage==="completed"]].map(([n,ok])=><div className="ledger" key={n}><Check size={13}/><span>{n}</span><em>{ok?"DONE":"READY"}</em></div>)}</div>{workspace.sheetUpdates.length>0&&<button className="undo" onClick={undo}><Undo2 size={14}/> UNDO LAST SHEET UPDATE</button>}<div className="panel-actions"><button onClick={exportAudit}><Download size={14}/> AUDIT</button><button onClick={()=>setModal("permissions")}><Shield size={14}/> PERMISSIONS</button><button onClick={()=>setModal("evals")}><FlaskConical size={14}/> EVALS</button></div></aside>

      </div>

      <section className="summary"><div className="section-kicker">RUN SUMMARY <span>WHAT HAPPENED</span></div><div className="summary-grid"><div><span>STATUS</span><strong>{stage==="completed"?"COMPLETE":stage==="idle"?"READY":"IN PROGRESS"}</strong></div><div><span>APPROVALS</span><strong>{trace.filter(x=>x.title==="Human approval received").length}</strong></div><div><span>RECOVERED</span><strong>{trace.filter(x=>x.type==="recovered").length}</strong></div><div><span>DATA</span><strong>SYNTHETIC</strong></div></div><p>{stage==="completed"?"NUDGE completed or safely stopped the workflow. The browser carries demo workspace state across new runs and refreshes.":"The final summary explains completed work, skips, approvals and recovery."}</p></section>

      <section className="how"><div className="section-kicker">HOW IT WORKS</div><div className="how-grid">{workflow.map(([,t,d])=><div key={t}><b>{t}</b><span>{d}</span></div>)}</div><div className="principles"><span>Autonomy with a leash</span><span>Code-enforced risk gate</span><span>Glass-box trace</span><span>Synthetic demo data</span></div></section>

      <footer>NUDGE / CONTROL PLANE · Human authority remains in the loop. · <a href="https://github.com/ayaankhan8926/NUDGE" target="_blank" rel="noreferrer">GITHUB</a></footer>

    </main>

    {error&&<div className="modal-bg"><div className="modal"><div className="modal-head"><AlertTriangle/><b>NUDGE ERROR</b><button onClick={()=>setError("")}><X/></button></div><p>{error}</p><button onClick={()=>{setError("");setStage("idle")}}>RETRY</button></div></div>}

    {modal&&<div className="modal-bg" onClick={()=>setModal(null)}><div className="modal" onClick={e=>e.stopPropagation()}><div className="modal-head"><Shield/><b>{modal.toUpperCase()}</b><button onClick={()=>setModal(null)}><X/></button></div>{modal==="policy"&&<div className="modal-list"><p><b>AUTO</b> reads, searches, analysis and drafts.</p><p><b>NUDGE</b> external communication and other consequential actions.</p><p><b>REVERSIBLE-AUTO</b> demo sheet updates with undo.</p><p><b>BLOCKED</b> account/password changes and money transfers.</p><small>Demo data is synthetic. Live Google integrations are not claimed here.</small></div>}{modal==="permissions"&&<div className="modal-list"><p><b>Gmail</b> read · draft · send with approval</p><p><b>Calendar</b> read events · prepare reminders</p><p><b>Sheets</b> read · demo update · undo</p></div>}{modal==="evals"&&<div className="modal-list">{[["Happy path","PASS"],["Duplicate run","PASS"],["Approval compliance","PASS"],["Reject / no workaround","PASS"],["Synthetic-data honesty","PASS"]].map(x=><p key={x[0]}><Check size={14}/> <b>{x[0]}</b><span>{x[1]}</span></p>)}<small>These are implemented demo checks, not a statistical benchmark.</small></div>}</div></div>}

  </div>

}
