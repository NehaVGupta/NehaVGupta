const STAGES = [
  ['User', 'Judge, planner, farmer, researcher…'], ['SatQuery AI UI', 'React + Leaflet workspace'], ['FastAPI', 'Validated, typed HTTP API'],
  ['Query understanding', 'Rule-based intent + modality router (LLM-ready interface)'],
  ['Agentic model router', 'Selects and sequences specialist models per intent'],
]
const SPECIALISTS = ['Object detection', 'Segmentation', 'Change detection', 'Image understanding', 'Optical/SAR fusion (planned)']
const TAIL = [['Evidence aggregation', 'Fuses and cross-checks model outputs'], ['Validation / confidence', '80/60 thresholds, quality & synthetic-data discounting'], ['Grounded response', 'Template composed only from structured evidence'], ['Visual evidence + map', 'Boxes, masks, change regions on an interactive map']]

const REAL = ['React/Tailwind frontend', 'FastAPI backend with typed schemas', 'Real file upload, validation, quality checks', 'GeoTIFF metadata via Rasterio (CRS, bounds, transform, bands)', 'Deterministic NL intent router', 'Classical-CV detection/segmentation/change engines running on real pixels', 'Confidence thresholds, evidence validation, "insufficient evidence" handling', 'Conversational follow-ups with session context', 'GeoJSON export, downloadable HTML report', 'Storage / cache / model abstractions ready for real backends']
const DEMO = ['Detection, segmentation and change results come from OpenCV colour-space heuristics, not a trained neural network', 'Demo dataset imagery is synthetically drawn, not real satellite imagery', 'Confidence scores are heuristic mask/shape-consistency scores, not calibrated probabilities', '"GSD" and coordinates for demo images are illustrative, not real georeferencing']
const PLUG = [['Object detection', 'YOLO / Faster R-CNN', 'app/engines/adapters.py → YOLOObjectDetectionModel'], ['Segmentation', 'U-Net / SegFormer', 'SegFormerSegmentationModel'], ['Change detection', 'Siamese U-Net / transformer CD', 'SiameseUNetChangeDetectionModel'], ['Scene understanding', 'GeoChat-style RS-VLM', 'HFVisionLanguageModel'], ['Multi-sensor', 'Optical/SAR fusion', 'OpticalSARFusionModel']]

const Box = ({ t, s }) => (<div className="panel px-4 py-3 text-center"><div className="font-medium">{t}</div>{s && <div className="text-xs text-mist-500">{s}</div>}</div>)
const Arrow = () => <div className="mx-auto h-6 w-px bg-ink-600" />

export default function Architecture() {
  return (
    <div className="mx-auto max-w-[1100px] space-y-12 px-4 py-12">
      <div><h1 className="font-display text-3xl">Architecture</h1><p className="mt-3 max-w-2xl text-mist-300">The agentic pipeline behind every answer, and an honest account of what is a working prototype today versus a planned production model.</p></div>

      <div className="panel p-6">
        {STAGES.map(([t, s], i) => (<div key={t}><Box t={t} s={s} />{i < STAGES.length - 1 && <Arrow />}</div>))}
        <Arrow />
        <div className="grid grid-cols-2 gap-2 md:grid-cols-5">{SPECIALISTS.map((s) => <Box key={s} t={s} />)}</div>
        <Arrow />
        {TAIL.map(([t, s], i) => (<div key={t}><Box t={t} s={s} />{i < TAIL.length - 1 && <Arrow />}</div>))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div><h2 className="font-display text-xl text-signal">What is real in this prototype</h2><ul className="mt-3 space-y-2 text-sm text-mist-300">{REAL.map((r) => <li key={r} className="flex gap-2"><span className="text-signal">✓</span>{r}</li>)}</ul></div>
        <div><h2 className="font-display text-xl text-amber-flag">What is demo / prototype inference</h2><ul className="mt-3 space-y-2 text-sm text-mist-300">{DEMO.map((r) => <li key={r} className="flex gap-2"><span className="text-amber-flag">△</span>{r}</li>)}</ul></div>
      </div>

      <div>
        <h2 className="font-display text-xl">Plugging in real models</h2>
        <p className="mt-2 max-w-2xl text-sm text-mist-400">Models share interfaces in <code className="font-mono text-signal">app/engines/base.py</code>, keeping the orchestrator and evidence pipeline model-agnostic. The listed real-model adapters are stubs; using one still requires implementing inference, loading weights, and enabling it in the registry.</p>
        <div className="mt-4 overflow-hidden rounded-lg border border-ink-600">
          <table className="w-full text-left text-sm"><thead className="bg-ink-700 text-xs text-mist-300"><tr><th className="px-3 py-2">Capability</th><th>Real model family</th><th>Adapter class</th></tr></thead>
            <tbody>{PLUG.map(([c, m, a]) => (<tr key={c} className="border-t border-ink-600"><td className="px-3 py-2">{c}</td><td>{m}</td><td className="font-mono text-xs text-mist-400">{a}</td></tr>))}</tbody></table>
        </div>
      </div>
    </div>
  )
}
