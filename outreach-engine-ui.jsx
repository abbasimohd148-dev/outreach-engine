import { useState, useEffect } from "react";

// ─── Mock Data for Demo ───────────────────────────────────────────────
const MOCK_CAMPAIGNS = [
  { id: "1", name: "SaaS CTOs Q1", status: "ready", total_prospects: 47, enriched_count: 47, generated_count: 47, created_at: "2026-03-10" },
  { id: "2", name: "E-comm Founders", status: "enriching", total_prospects: 120, enriched_count: 63, generated_count: 41, created_at: "2026-03-11" },
  { id: "3", name: "Agency Owners", status: "pending", total_prospects: 0, enriched_count: 0, generated_count: 0, created_at: "2026-03-12" },
];

const MOCK_PROSPECTS = [
  {
    id: "p1", first_name: "Sarah", last_name: "Chen", title: "CTO", company: "Dataflow AI",
    email: "sarah@dataflow.ai", enrichment_status: "done", generation_status: "done",
    personalized_first_line: "Saw Dataflow AI just closed your Series B — congrats on the $12M round. Scaling infrastructure fast usually means the ops tooling hasn't caught up yet.",
    subject_line: "Dataflow's Series B → one ops problem we can solve",
    email_body: "Hi Sarah,\n\nScaling from 20 to 80 engineers post-funding is exciting and chaotic. Most CTOs at this stage tell us their biggest time sink is still manual outreach coordination.\n\nWe built a tool that automates the research + personalization side of BD entirely. Saved Acme Corp 12 hours/week in their first month.\n\nWorth a 15-minute chat this week?",
    enrichment_signals: { funding: "Dataflow AI raises $12M Series B", tech_stack: ["HubSpot", "Segment"] }
  },
  {
    id: "p2", first_name: "Marcus", last_name: "Webb", title: "Head of Sales", company: "Prism Analytics",
    email: "m.webb@prismanalytics.com", enrichment_status: "done", generation_status: "done",
    personalized_first_line: "Noticed Prism Analytics is hiring 3 SDRs right now — looks like you're scaling the outbound motion seriously.",
    subject_line: "Scaling Prism's SDR team → make each rep 3x more efficient",
    email_body: "Hi Marcus,\n\nBuilding an SDR team from scratch means every hour of rep time matters enormously. The biggest bottleneck we see is prospect research eating 40% of their day.\n\nOur tool handles enrichment + personalization automatically so reps spend time on calls, not tabs.\n\nCould save your new hires 2+ hours daily from day one. Open to a quick demo?",
    enrichment_signals: { recent_news: "Prism Analytics hiring SDRs", linkedin_headline: "Building the outbound engine at Prism" }
  },
  {
    id: "p3", first_name: "Priya", last_name: "Nair", title: "Founder & CEO", company: "Luma Commerce",
    email: "priya@lumacommerce.co", enrichment_status: "running", generation_status: "pending",
    personalized_first_line: null, subject_line: null, email_body: null,
    enrichment_signals: {}
  },
];

// ─── Icons ────────────────────────────────────────────────────────────
const Icon = ({ name, size = 18 }) => {
  const icons = {
    plus: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>,
    upload: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>,
    download: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
    check: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>,
    edit: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>,
    zap: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
    back: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>,
    signal: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
    x: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>,
    refresh: <svg width={size} height={size} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>,
  };
  return icons[name] || null;
};

// ─── Status Badge ─────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const styles = {
    ready: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
    enriching: "bg-amber-500/15 text-amber-400 border border-amber-500/20",
    pending: "bg-zinc-700/50 text-zinc-400 border border-zinc-600/20",
    generating: "bg-blue-500/15 text-blue-400 border border-blue-500/20",
    done: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
    running: "bg-amber-500/15 text-amber-400 border border-amber-500/20 animate-pulse",
    failed: "bg-red-500/15 text-red-400 border border-red-500/20",
  };
  const labels = {
    ready: "Ready", enriching: "Enriching…", pending: "Pending",
    generating: "Generating…", done: "Done", running: "Processing…", failed: "Failed"
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </span>
  );
};

// ─── Progress Bar ─────────────────────────────────────────────────────
const ProgressBar = ({ value, max, color = "emerald" }) => {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  const colors = { emerald: "bg-emerald-500", amber: "bg-amber-400", blue: "bg-blue-500" };
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${colors[color]}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-zinc-500 w-8 text-right">{pct}%</span>
    </div>
  );
};

// ─── Modal ────────────────────────────────────────────────────────────
const Modal = ({ title, children, onClose }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
    <div className="relative bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors">
          <Icon name="x" size={20} />
        </button>
      </div>
      {children}
    </div>
  </div>
);

// ─── SCREEN: Dashboard ────────────────────────────────────────────────
const Dashboard = ({ onSelectCampaign, onNewCampaign }) => {
  const totalGenerated = MOCK_CAMPAIGNS.reduce((a, c) => a + c.generated_count, 0);
  const creditsUsed = 167;
  const creditsTotal = 200;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Campaigns</h1>
          <p className="text-zinc-500 text-sm mt-1">AI-powered outreach personalization</p>
        </div>
        <button
          onClick={onNewCampaign}
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-black font-semibold text-sm px-4 py-2 rounded-xl transition-colors"
        >
          <Icon name="plus" size={16} />
          New Campaign
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Generated", value: totalGenerated, sub: "emails this month" },
          { label: "Credits Used", value: `${creditsUsed}/${creditsTotal}`, sub: "resets Apr 1" },
          { label: "Active Campaigns", value: MOCK_CAMPAIGNS.length, sub: "across all plans" },
        ].map((s) => (
          <div key={s.label} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <p className="text-zinc-500 text-xs mb-1">{s.label}</p>
            <p className="text-2xl font-bold text-white">{s.value}</p>
            <p className="text-zinc-600 text-xs mt-1">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Credits Bar */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-zinc-300">Monthly Credits</span>
          <span className="text-xs text-zinc-500">Starter Plan · 200 prospects/mo</span>
        </div>
        <ProgressBar value={creditsUsed} max={creditsTotal} color="emerald" />
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-zinc-600">{creditsTotal - creditsUsed} remaining</span>
          <button className="text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
            Upgrade Plan →
          </button>
        </div>
      </div>

      {/* Campaign List */}
      <div className="space-y-3">
        {MOCK_CAMPAIGNS.map((c) => (
          <div
            key={c.id}
            onClick={() => c.status !== "pending" && onSelectCampaign(c)}
            className={`bg-zinc-900 border border-zinc-800 hover:border-zinc-600 rounded-2xl p-5 transition-all cursor-pointer group`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-white group-hover:text-emerald-400 transition-colors">{c.name}</h3>
                <p className="text-zinc-600 text-xs mt-0.5">{c.created_at}</p>
              </div>
              <StatusBadge status={c.status} />
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm mb-3">
              <div><p className="text-zinc-500 text-xs">Prospects</p><p className="text-white font-medium">{c.total_prospects}</p></div>
              <div><p className="text-zinc-500 text-xs">Enriched</p><p className="text-white font-medium">{c.enriched_count}</p></div>
              <div><p className="text-zinc-500 text-xs">Generated</p><p className="text-white font-medium">{c.generated_count}</p></div>
            </div>
            {c.total_prospects > 0 && (
              <ProgressBar value={c.generated_count} max={c.total_prospects} color={c.status === "enriching" ? "amber" : "emerald"} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── SCREEN: Prospect Review ──────────────────────────────────────────
const ProspectReview = ({ campaign, onBack }) => {
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editValues, setEditValues] = useState({});

  const openProspect = (p) => {
    setSelected(p);
    setEditValues({
      subject: p.edited_subject_line || p.subject_line || "",
      first_line: p.edited_first_line || p.personalized_first_line || "",
      body: p.edited_email_body || p.email_body || "",
    });
    setEditing(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="text-zinc-500 hover:text-white transition-colors">
          <Icon name="back" size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-white">{campaign.name}</h1>
          <p className="text-zinc-500 text-sm">{campaign.generated_count} emails ready · {campaign.total_prospects} total</p>
        </div>
        <button className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white text-sm px-4 py-2 rounded-xl transition-colors border border-zinc-700">
          <Icon name="download" size={16} />
          Export CSV
        </button>
      </div>

      {/* Prospect Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
        <div className="grid grid-cols-12 gap-4 px-5 py-3 border-b border-zinc-800 text-xs text-zinc-500 font-medium uppercase tracking-wider">
          <div className="col-span-3">Prospect</div>
          <div className="col-span-5">First Line Preview</div>
          <div className="col-span-2">Signals</div>
          <div className="col-span-2">Status</div>
        </div>
        {MOCK_PROSPECTS.map((p) => (
          <div
            key={p.id}
            onClick={() => p.generation_status === "done" && openProspect(p)}
            className={`grid grid-cols-12 gap-4 px-5 py-4 border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors ${p.generation_status === "done" ? "cursor-pointer" : "opacity-60"}`}
          >
            <div className="col-span-3">
              <p className="text-white font-medium text-sm">{p.first_name} {p.last_name}</p>
              <p className="text-zinc-500 text-xs">{p.title} · {p.company}</p>
            </div>
            <div className="col-span-5">
              <p className="text-zinc-400 text-sm line-clamp-2 leading-relaxed">
                {p.personalized_first_line || "Processing…"}
              </p>
            </div>
            <div className="col-span-2">
              <div className="flex flex-wrap gap-1">
                {p.enrichment_signals?.funding && (
                  <span className="text-xs bg-violet-500/15 text-violet-400 border border-violet-500/20 px-1.5 py-0.5 rounded-full">💰 Funding</span>
                )}
                {p.enrichment_signals?.recent_news && (
                  <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded-full">📰 News</span>
                )}
                {p.enrichment_signals?.tech_stack && (
                  <span className="text-xs bg-amber-500/15 text-amber-400 border border-amber-500/20 px-1.5 py-0.5 rounded-full">🛠 Tech</span>
                )}
              </div>
            </div>
            <div className="col-span-2 flex items-center">
              <StatusBadge status={p.generation_status} />
            </div>
          </div>
        ))}
      </div>

      {/* Email Preview Modal */}
      {selected && (
        <Modal title={`${selected.first_name} ${selected.last_name} · ${selected.company}`} onClose={() => setSelected(null)}>
          <div className="space-y-4">
            {/* Signal badges */}
            <div className="flex flex-wrap gap-1.5">
              {selected.enrichment_signals?.funding && (
                <span className="text-xs bg-violet-500/15 text-violet-400 border border-violet-500/20 px-2 py-1 rounded-full">💰 {selected.enrichment_signals.funding}</span>
              )}
              {selected.enrichment_signals?.recent_news && (
                <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 px-2 py-1 rounded-full">📰 {selected.enrichment_signals.recent_news}</span>
              )}
              {selected.enrichment_signals?.tech_stack?.map(t => (
                <span key={t} className="text-xs bg-amber-500/15 text-amber-400 border border-amber-500/20 px-2 py-1 rounded-full">🛠 {t}</span>
              ))}
            </div>

            {editing ? (
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-zinc-500 mb-1 block">Subject</label>
                  <input
                    value={editValues.subject}
                    onChange={e => setEditValues(v => ({ ...v, subject: e.target.value }))}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-500 mb-1 block">First Line</label>
                  <textarea
                    value={editValues.first_line}
                    onChange={e => setEditValues(v => ({ ...v, first_line: e.target.value }))}
                    rows={2}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500 resize-none"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-500 mb-1 block">Email Body</label>
                  <textarea
                    value={editValues.body}
                    onChange={e => setEditValues(v => ({ ...v, body: e.target.value }))}
                    rows={6}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500 resize-none"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-zinc-800/60 rounded-xl p-4 space-y-3">
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">Subject</p>
                    <p className="text-white font-medium text-sm">{editValues.subject}</p>
                  </div>
                  <div className="border-t border-zinc-700 pt-3">
                    <p className="text-xs text-zinc-500 mb-1">First Line</p>
                    <p className="text-zinc-300 text-sm leading-relaxed">{editValues.first_line}</p>
                  </div>
                  <div className="border-t border-zinc-700 pt-3">
                    <p className="text-zinc-300 text-sm leading-relaxed whitespace-pre-line">{editValues.body}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={() => setEditing(!editing)}
                className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors"
              >
                <Icon name="edit" size={14} />
                {editing ? "Preview" : "Edit"}
              </button>
              <button className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors">
                <Icon name="refresh" size={14} />
                Regenerate
              </button>
              <div className="flex-1" />
              {editing && (
                <button className="flex items-center gap-1.5 text-sm bg-emerald-500 hover:bg-emerald-400 text-black font-semibold px-4 py-2 rounded-lg transition-colors">
                  <Icon name="check" size={14} />
                  Save Changes
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

// ─── SCREEN: New Campaign Wizard ──────────────────────────────────────
const NewCampaign = ({ onBack, onCreate }) => {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ name: "", tone: "professional", offer: "" });
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);

  const tones = [
    { id: "professional", label: "Professional", desc: "Polished & respectful" },
    { id: "casual", label: "Casual", desc: "Warm & conversational" },
    { id: "direct", label: "Direct", desc: "No fluff, fast value" },
    { id: "friendly", label: "Friendly", desc: "Approachable & warm" },
  ];

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="text-zinc-500 hover:text-white transition-colors">
          <Icon name="back" size={20} />
        </button>
        <h1 className="text-xl font-bold text-white">New Campaign</h1>
      </div>

      {/* Step indicators */}
      <div className="flex items-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${step >= s ? "bg-emerald-500 text-black" : "bg-zinc-800 text-zinc-500"}`}>
              {step > s ? <Icon name="check" size={14} /> : s}
            </div>
            {s < 3 && <div className={`flex-1 h-px w-12 transition-all ${step > s ? "bg-emerald-500" : "bg-zinc-800"}`} />}
          </div>
        ))}
        <span className="text-zinc-500 text-xs ml-2">{["Campaign Setup", "Your Offer", "Upload CSV"][step - 1]}</span>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-5">
        {step === 1 && (
          <>
            <div>
              <label className="text-sm font-medium text-zinc-300 mb-2 block">Campaign Name</label>
              <input
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="e.g. SaaS CTOs Q2 2026"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-zinc-300 mb-3 block">Email Tone</label>
              <div className="grid grid-cols-2 gap-2">
                {tones.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setForm(f => ({ ...f, tone: t.id }))}
                    className={`p-3 rounded-xl border text-left transition-all ${form.tone === t.id ? "border-emerald-500 bg-emerald-500/10" : "border-zinc-700 hover:border-zinc-500"}`}
                  >
                    <p className={`text-sm font-medium ${form.tone === t.id ? "text-emerald-400" : "text-white"}`}>{t.label}</p>
                    <p className="text-zinc-500 text-xs mt-0.5">{t.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <div>
            <label className="text-sm font-medium text-zinc-300 mb-2 block">What are you selling?</label>
            <p className="text-zinc-500 text-xs mb-3">Describe your product/service in 2-3 sentences. The AI will use this to craft relevant outreach.</p>
            <textarea
              value={form.offer}
              onChange={e => setForm(f => ({ ...f, offer: e.target.value }))}
              placeholder="e.g. We help SaaS companies automate their outbound prospecting. Our tool enriches prospects from LinkedIn and news signals, then writes personalized emails automatically — saving SDRs 2+ hours per day."
              rows={5}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 transition-colors resize-none"
            />
            <p className="text-zinc-600 text-xs mt-2">{form.offer.length}/500 characters</p>
          </div>
        )}

        {step === 3 && (
          <div>
            <label className="text-sm font-medium text-zinc-300 mb-2 block">Upload Prospect CSV</label>
            <p className="text-zinc-500 text-xs mb-3">Required columns: <code className="text-emerald-400">first_name, last_name, email, company, title</code> · Optional: <code className="text-emerald-400">linkedin_url, website</code></p>
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={e => { e.preventDefault(); setDragging(false); setFile(e.dataTransfer.files[0]); }}
              onClick={() => document.getElementById("csv-input").click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${dragging ? "border-emerald-500 bg-emerald-500/5" : file ? "border-emerald-500/50 bg-emerald-500/5" : "border-zinc-700 hover:border-zinc-500"}`}
            >
              <input id="csv-input" type="file" accept=".csv" className="hidden" onChange={e => setFile(e.target.files[0])} />
              {file ? (
                <div>
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center mx-auto mb-2">
                    <Icon name="check" size={20} />
                  </div>
                  <p className="text-white font-medium text-sm">{file.name}</p>
                  <p className="text-zinc-500 text-xs mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div>
                  <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center mx-auto mb-2 text-zinc-400">
                    <Icon name="upload" size={20} />
                  </div>
                  <p className="text-zinc-400 text-sm">Drop your CSV here or click to browse</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        {step > 1 && (
          <button onClick={() => setStep(s => s - 1)} className="flex-1 py-3 rounded-xl border border-zinc-700 text-white text-sm font-medium hover:bg-zinc-800 transition-colors">
            Back
          </button>
        )}
        <button
          onClick={() => step < 3 ? setStep(s => s + 1) : onCreate()}
          disabled={step === 1 && !form.name}
          className="flex-1 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed text-black text-sm font-bold transition-colors flex items-center justify-center gap-2"
        >
          {step === 3 ? (
            <><Icon name="zap" size={16} /> Start Enrichment</>
          ) : "Continue →"}
        </button>
      </div>
    </div>
  );
};

// ─── APP SHELL ────────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState("dashboard");
  const [selectedCampaign, setSelectedCampaign] = useState(null);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Sidebar */}
      <div className="fixed left-0 top-0 bottom-0 w-56 bg-zinc-950 border-r border-zinc-800/60 p-5 flex flex-col z-10">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-8">
          <div className="w-8 h-8 rounded-xl bg-emerald-500 flex items-center justify-center">
            <Icon name="zap" size={16} />
          </div>
          <span className="font-bold text-white tracking-tight">OutreachAI</span>
        </div>

        {/* Nav */}
        <nav className="space-y-1 flex-1">
          {[
            { id: "dashboard", label: "Campaigns", icon: "signal" },
            { id: "new", label: "New Campaign", icon: "plus" },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setScreen(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${screen === item.id ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-white hover:bg-zinc-900"}`}
            >
              <Icon name={item.icon} size={16} />
              {item.label}
            </button>
          ))}
        </nav>

        {/* User */}
        <div className="border-t border-zinc-800 pt-4">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-xs font-bold text-black">JD</div>
            <div>
              <p className="text-white text-xs font-medium">John Doe</p>
              <p className="text-zinc-600 text-xs">Starter · 33 left</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="ml-56 p-8 max-w-5xl">
        {screen === "dashboard" && (
          <Dashboard
            onSelectCampaign={(c) => { setSelectedCampaign(c); setScreen("review"); }}
            onNewCampaign={() => setScreen("new")}
          />
        )}
        {screen === "review" && selectedCampaign && (
          <ProspectReview campaign={selectedCampaign} onBack={() => setScreen("dashboard")} />
        )}
        {screen === "new" && (
          <NewCampaign
            onBack={() => setScreen("dashboard")}
            onCreate={() => setScreen("dashboard")}
          />
        )}
      </main>
    </div>
  );
}
