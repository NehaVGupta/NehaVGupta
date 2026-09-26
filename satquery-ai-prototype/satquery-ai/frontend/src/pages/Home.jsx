import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

const STEPS = [
  ['Upload imagery', 'Drop a satellite/remote-sensing image, or a before/after pair, in PNG, JPG or GeoTIFF.'],
  ['Ask in plain language', '“How many buildings are visible?”, “Show me the water bodies”, “What changed?”'],
  ['Agentic routing', 'The query router detects intent and modality, then selects the right specialist model(s).'],
  ['Grounded answer', 'A response is composed only from measured evidence — masks, boxes, counts, confidence.'],
]
const ANALYSES = [
  ['Object detection', 'Buildings, vehicles, ships, agricultural structures — bounding boxes with confidence.'],
  ['Land-cover segmentation', 'Water, vegetation, built-up area, roads, bare soil — pixel-accurate masks and area.'],
  ['Change detection', 'Co-registered before/after comparison with significance thresholds and change typing.'],
  ['Scene understanding', 'A composed summary of land-cover mix and detected objects, grounded in the above.'],
]
const USES = [
  ['Disaster response', 'Rapid before/after assessment of flood and damage extent.'],
  ['Urban planning', 'Track built-up growth, new construction, and infrastructure change over time.'],
  ['Agriculture', 'Monitor field vegetation, bare soil and water availability across a season.'],
  ['Forests & water', 'Watch vegetation loss and shoreline / water-extent change.'],
]

function useReveal() {
  const ref = useRef()
  const [shown, setShown] = useState(false)
  useEffect(() => {
    const o = new IntersectionObserver(([e]) => e.isIntersecting && setShown(true), { threshold: 0.15 })
    if (ref.current) o.observe(ref.current)
    return () => o.disconnect()
  }, [])
  return [ref, shown]
}

function Section({ eyebrow, title, children, id }) {
  const [ref, shown] = useReveal()
  return (
    <section id={id} ref={ref} className={`mx-auto max-w-[1200px] px-4 py-20 transition-all duration-700 ${shown ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'}`}>
      <p className="mb-2 font-mono text-xs uppercase tracking-[0.2em] text-signal">{eyebrow}</p>
      <h2 className="mb-8 max-w-2xl font-display text-3xl font-medium leading-tight md:text-4xl">{title}</h2>
      {children}
    </section>
  )
}

function Scanline() {
  return (
    <svg viewBox="0 0 800 500" className="h-full w-full" aria-hidden="true">
      <defs><radialGradient id="g" cx="50%" cy="40%" r="70%"><stop offset="0%" stopColor="#16324f" /><stop offset="60%" stopColor="#0b1626" /><stop offset="100%" stopColor="#080d16" /></radialGradient></defs>
      <rect width="800" height="500" fill="url(#g)" />
      {Array.from({ length: 9 }).map((_, i) => <line key={i} x1="0" y1={i * 60} x2="800" y2={i * 60} stroke="#3dc9b0" strokeOpacity="0.06" />)}
      {Array.from({ length: 13 }).map((_, i) => <line key={i} x1={i * 62} y1="0" x2={i * 62} y2="500" stroke="#3dc9b0" strokeOpacity="0.06" />)}
      <g className="draw" fill="none" stroke="#3dc9b0" strokeWidth="1.4">
        <rect x="120" y="90" width="70" height="52" rx="2" /><rect x="230" y="140" width="90" height="60" rx="2" /><rect x="380" y="80" width="60" height="46" rx="2" />
        <rect x="500" y="160" width="100" height="66" rx="2" /><rect x="640" y="100" width="56" height="72" rx="2" />
      </g>
      <g className="draw" style={{ animationDelay: '.3s' }} fill="none" stroke="#f2b544" strokeWidth="1.6" strokeDasharray="5 4">
        <polygon points="230,140 320,140 320,200 230,200" />
      </g>
      <circle cx="285" cy="320" r="70" fill="#38bdf8" fillOpacity="0.18" stroke="#38bdf8" strokeOpacity="0.5" className="draw" style={{ animationDelay: '.5s' }} />
      <text x="120" y="410" fill="#8494ad" fontFamily="IBM Plex Mono" fontSize="11">12 buildings · 91% confidence</text>
    </svg>
  )
}

export default function Home() {
  return (
    <div>
      <section className="relative overflow-hidden border-b border-ink-600 graticule">
        <div className="mx-auto grid max-w-[1200px] items-center gap-10 px-4 py-20 md:grid-cols-2 md:py-28">
          <div>
            <p className="mb-4 font-mono text-xs uppercase tracking-[0.2em] text-signal">Smart India Hackathon 2026 · SIH26167 · Team Cipher</p>
            <h1 className="font-display text-5xl font-medium leading-[1.05] md:text-6xl">Ask questions.<br />Understand Earth.</h1>
            <p className="mt-6 max-w-md text-mist-300">An evidence-grounded AI assistant for analysing satellite imagery using natural language. Every answer is backed by masks, boxes, coordinates and a confidence score — or it says so.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/analysis?demo=1" className="btn-primary">Start Analysis</Link>
              <Link to="/analysis?demo=1&guide=1" className="btn-ghost">View Demo</Link>
            </div>
          </div>
          <div className="aspect-[8/5] overflow-hidden rounded-lg border border-ink-600"><Scanline /></div>
        </div>
      </section>

      <Section eyebrow="What is SatQuery AI?" title="A natural-language interface over specialist remote-sensing models — not a generic chatbot.">
        <p className="max-w-2xl text-mist-300">SatQuery AI does not let a language model freely describe a satellite image. It parses intent, runs the right computer-vision analysis, and only then composes an answer from the structured result. If the evidence is weak, it says <span className="font-mono text-amber-flag">“Insufficient visual evidence for a reliable conclusion.”</span> — by design, not as an error.</p>
      </Section>

      <Section eyebrow="How it works" title="Query, route, analyse, ground.">
        <ol className="grid gap-4 md:grid-cols-4">
          {STEPS.map(([t, d], i) => (
            <li key={t} className="panel p-4"><span className="font-mono text-xs text-signal">{String(i + 1).padStart(2, '0')}</span><h3 className="mt-2 font-medium">{t}</h3><p className="mt-1 text-sm text-mist-400">{d}</p></li>
          ))}
        </ol>
      </Section>

      <Section eyebrow="Supported analysis" title="Four specialist analyses behind one conversation.">
        <div className="grid gap-4 md:grid-cols-2">
          {ANALYSES.map(([t, d]) => (<div key={t} className="panel p-5"><h3 className="font-display text-lg">{t}</h3><p className="mt-1 text-sm text-mist-400">{d}</p></div>))}
        </div>
      </Section>

      <Section eyebrow="Use cases" title="Built for the people who read imagery for a living.">
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          {USES.map(([t, d]) => (<div key={t} className="rounded-lg border border-ink-600 p-4"><h3 className="font-medium">{t}</h3><p className="mt-1 text-xs text-mist-400">{d}</p></div>))}
        </div>
      </Section>

      <Section eyebrow="Evidence-grounded AI" title="No evidence, no strong claim.">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-red-400/30 bg-red-400/5 p-5"><p className="mb-2 font-mono text-xs text-red-300">NOT THIS</p><p className="font-display text-lg">“The area is definitely flooded.”</p></div>
          <div className="rounded-lg border border-signal/30 bg-signal/5 p-5"><p className="mb-2 font-mono text-xs text-signal">THIS</p><p className="font-display text-lg">“Regions consistent with water presence were identified. Model confidence: 84%. Expert verification is recommended.”</p></div>
        </div>
      </Section>

      <Section eyebrow="Architecture" title="Query → intent → agentic model selection → evidence → validation → response.">
        <p className="max-w-2xl text-mist-300">See the full pipeline, and how prototype heuristics map to planned production models, on the <Link to="/architecture" className="text-signal underline">architecture page</Link>.</p>
      </Section>

      <Section eyebrow="Technology" title="A geospatial-intelligence stack, not a toy demo.">
        <div className="flex flex-wrap gap-2 text-xs">
          {['React', 'Tailwind CSS', 'Leaflet', 'FastAPI', 'OpenCV', 'Rasterio / GDAL', 'PyTorch (planned)', 'Hugging Face (planned)', 'PostgreSQL + PostGIS (ready)', 'MinIO / S3 (ready)', 'Redis', 'Docker'].map((t) => (<span key={t} className="chip">{t}</span>))}
        </div>
      </Section>

      <Section eyebrow="Impact" title="From fragmented tools to grounded, explainable answers.">
        <div className="flex items-center gap-1 overflow-x-auto pb-2 text-xs">
          {['Fragmented analysis', 'Upload imagery', 'Ask question', 'Explore results', 'Grounded answer'].map((s, i, a) => (
            <div key={s} className="flex items-center gap-1"><span className="whitespace-nowrap rounded-full border border-ink-600 px-3 py-1.5 text-mist-300">{s}</span>{i < a.length - 1 && <span className="text-mist-600">→</span>}</div>
          ))}
        </div>
      </Section>

      <section className="border-t border-ink-600 py-16 text-center">
        <h2 className="font-display text-3xl">See it decide, in one click.</h2>
        <Link to="/analysis?demo=1" className="btn-primary mt-6 inline-flex">Start Analysis</Link>
      </section>
    </div>
  )
}
