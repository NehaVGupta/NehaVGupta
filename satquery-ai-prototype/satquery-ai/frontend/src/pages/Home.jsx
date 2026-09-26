import { Link } from 'react-router-dom'

const CAPABILITIES = [
  ['01', 'Detect objects', 'Identify buildings and other visible structures.'],
  ['02', 'Map land cover', 'Explore water, vegetation, roads, and built-up areas.'],
  ['03', 'Compare scenes', 'Review differences between before-and-after imagery.'],
]

export default function Home() {
  return (
    <div className="mx-auto max-w-[1320px] px-4 py-8 md:px-8 md:py-12">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3 border-b border-ink-600 pb-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-signal">Geospatial analysis workspace</p>
          <p className="mt-1 text-sm text-mist-400">Satellite imagery, made queryable.</p>
        </div>
        <span className="inline-flex items-center gap-2 rounded border border-ink-600 px-3 py-1.5 text-xs text-mist-300">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-flag" />
          Prototype environment
        </span>
      </div>

      <section className="grid items-center gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:gap-12">
        <div className="py-4 lg:py-10">
          <p className="mb-4 font-mono text-xs uppercase tracking-[0.16em] text-mist-500">SatQuery AI / Workspace</p>
          <h1 className="max-w-xl font-display text-4xl font-medium leading-tight md:text-5xl">Ask better questions of satellite imagery.</h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-mist-300">Run focused image analysis, inspect the visual evidence, and ask questions in plain language. Results stay connected to the imagery they came from.</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/analysis" className="btn-primary">Open analysis</Link>
            <Link to="/analysis?demo=1" className="btn-ghost">Explore sample scene</Link>
          </div>
          <p className="mt-5 text-xs text-mist-500">Upload an image or start with the included urban sample.</p>
        </div>

        <figure className="overflow-hidden rounded-md border border-ink-600 bg-ink-900">
          <div className="relative aspect-[16/10]">
            <img src="/samples/urban.png" alt="Urban satellite imagery sample" className="h-full w-full object-cover" />
            <span className="absolute left-3 top-3 rounded-sm border border-white/20 bg-ink-950/85 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wider text-mist-100">Sample scene</span>
          </div>
          <figcaption className="flex flex-wrap items-center justify-between gap-2 border-t border-ink-600 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-mist-100">Urban overview</p>
              <p className="mt-0.5 text-xs text-mist-500">Included sample imagery</p>
            </div>
            <Link to="/analysis?demo=1" className="text-sm text-signal hover:underline">Open sample <span aria-hidden="true">-&gt;</span></Link>
          </figcaption>
        </figure>
      </section>

      <section className="mt-12 border-t border-ink-600 pt-7 md:mt-16" aria-labelledby="capabilities-title">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-mist-500">Available in this prototype</p>
            <h2 id="capabilities-title" className="mt-2 font-display text-2xl font-medium">Analysis tools</h2>
          </div>
          <Link to="/architecture" className="text-sm text-mist-300 hover:text-mist-100">View system architecture</Link>
        </div>
        <div className="grid gap-0 sm:grid-cols-3">
          {CAPABILITIES.map(([number, title, description]) => (
            <div key={number} className="border-t border-ink-600 py-4 sm:mr-6 sm:last:mr-0">
              <p className="font-mono text-xs text-signal">{number}</p>
              <h3 className="mt-2 text-sm font-medium text-mist-100">{title}</h3>
              <p className="mt-1 max-w-xs text-sm leading-6 text-mist-400">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
