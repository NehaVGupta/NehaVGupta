import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import { useAnalysis } from '../hooks/useAnalysis'
import DatasetSelector from '../components/DatasetSelector'
import UploadPanel from '../components/UploadPanel'
import MetadataPanel from '../components/MetadataPanel'
import MapViewer from '../components/MapViewer'
import DetectionOverlay from '../components/DetectionOverlay'
import SegmentationOverlay from '../components/SegmentationOverlay'
import ChangeOverlay from '../components/ChangeOverlay'
import ChangeMap from '../components/ChangeMap'
import ChatPanel from '../components/ChatPanel'
import EvidencePanel from '../components/EvidencePanel'
import ErrorState from '../components/ErrorState'
import DemoGuide, { DEMO_STEPS } from '../components/DemoGuide'

const TABS = [['map', 'Map / detections'], ['segment', 'Segmentation'], ['change', 'Change'], ['dashboard', 'Evidence']]
const SEG_CLASSES = ['water', 'vegetation', 'built_up', 'roads', 'bare_soil']
const DEFAULT_SUGGEST = ['How many buildings are visible?', 'Show me the water bodies.', 'What percentage of the image is vegetation?', 'Explain this image.']

export default function AnalysisPage() {
  const [params, setParams] = useSearchParams()
  const A = useAnalysis()
  const [datasets, setDatasets] = useState([])
  const [showGuide, setShowGuide] = useState(false)
  const [guideStep, setGuideStep] = useState(null)
  const [segClass, setSegClass] = useState('vegetation')
  const [segLoading, setSegLoading] = useState(false)
  const [segResult, setSegResult] = useState(null)

  useEffect(() => { api.demoDatasets().then(setDatasets).catch(() => setDatasets([])) }, [])

  useEffect(() => {
    const open = params.get('open')
    if (open) { A.openAnalysis(open); setParams({}, { replace: true }); return }
    if (params.get('demo') === '1') {
      A.loadDataset('urban').then(() => { if (params.get('guide') === '1') setShowGuide(true) })
      setParams({}, { replace: true })
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const record = A.selected
  const suggestions = record?.suggestions?.length ? record.suggestions : A.dataset?.suggested_questions || DEFAULT_SUGGEST

  const runDemoStep = async (i) => {
    setGuideStep(i)
    const step = DEMO_STEPS[i]
    let a = A.imageA, b = A.imageB
    if (A.dataset?.id !== step.dataset) {
      const r = await A.loadDataset(step.dataset)
      a = r?.images[0]; b = r?.images[1] || null
    }
    await A.send(step.q, a, b)
    setActiveTab(step.q.match(/chang/i) ? 'change' : step.q.match(/water|vegetation|bare|road|percent/i) ? 'segment' : 'map')
  }

  const [activeTab, setActiveTab] = useState('map')
  useEffect(() => {
    if (!record) return
    if (record.visualization.change_regions?.length || record.evidence.analysis_type.includes('change')) setActiveTab('change')
    else if (record.visualization.masks?.length) setActiveTab('segment')
    else setActiveTab('map')
  }, [record?.id])

  const runSegment = async (cls) => {
    setSegClass(cls); setSegLoading(true)
    try {
      const rec = await api.analyze('segment', { image_id: A.imageA.id, target: cls })
      setSegResult(rec); A.select(rec)
    } catch (e) { A.setNotice(e.message) } finally { setSegLoading(false) }
  }

  const runDetect = async () => {
    try { const rec = await api.analyze('detect', { image_id: A.imageA.id }); A.select(rec) } catch (e) { A.setNotice(e.message) }
  }
  const runChange = async () => {
    if (!A.imageB) return A.setNotice('Upload or load a second image (Image B) first.')
    try { const rec = await api.analyze('change', { image_id: A.imageA.id, image_b_id: A.imageB.id }); A.select(rec) } catch (e) { A.setNotice(e.message) }
  }

  const viz = record?.visualization
  const highlightIds = record?.evidence?.focus_ids || A.highlightId ? [...(record?.evidence?.focus_ids || []), A.highlightId].filter(Boolean) : []

  return (
    <div className="flex h-[calc(100vh-56px)] flex-col lg:flex-row">
      <aside className="w-full shrink-0 space-y-5 overflow-y-auto border-b border-ink-600 p-4 lg:w-72 lg:border-b-0 lg:border-r">
        <UploadPanel label="Image A (required)" image={A.imageA} onFile={(f) => A.setImage('a', f)} onClear={() => A.clearImage('a')} uploading={A.uploading} />
        <UploadPanel label="Image B (for change detection)" image={A.imageB} onFile={(f) => A.setImage('b', f)} onClear={() => A.clearImage('b')} uploading={A.uploading} hint="Optional — same scene, later date" />
        <DatasetSelector datasets={datasets} active={A.dataset?.id} onLoad={A.loadDataset} busy={A.loading} />
        <MetadataPanel image={A.imageA} />
        {A.imageB && <MetadataPanel image={A.imageB} title="Image B metadata" />}
        <div className="space-y-2">
          <div className="text-sm font-medium">Layer opacity</div>
          <input type="range" min="0.2" max="1" step="0.05" value={A.layers.opacity} onChange={(e) => A.setLayers({ opacity: +e.target.value })} className="w-full accent-signal" />
        </div>
        <button className="text-xs text-signal hover:underline" onClick={() => setShowGuide((s) => !s)}>{showGuide ? 'Hide' : 'Show'} judge demo script</button>
        {showGuide && <DemoGuide current={guideStep} onRun={runDemoStep} onClose={() => setShowGuide(false)} busy={A.loading} />}
      </aside>

      <section className="flex min-h-[60vh] flex-1 flex-col border-b border-ink-600 lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between gap-2 border-b border-ink-600 px-3 py-2">
          <div className="flex gap-1">
            {TABS.map(([id, label]) => (<button key={id} onClick={() => setActiveTab(id)} className={`rounded-md px-3 py-1.5 text-xs ${activeTab === id ? 'bg-ink-700 text-mist-100' : 'text-mist-400 hover:text-mist-100'}`}>{label}</button>))}
          </div>
          <div className="flex gap-2">
            <button className="btn-ghost !py-1 text-xs" onClick={runDetect} disabled={!A.imageA}>Detect objects</button>
            <button className="btn-ghost !py-1 text-xs" onClick={runChange} disabled={!A.imageA || !A.imageB}>Analyze changes</button>
          </div>
        </div>
        <ErrorState message={A.notice || A.uploadError} onDismiss={() => A.setNotice(null)} />
        <div className="flex-1 overflow-hidden">
          {activeTab === 'change' ? (
            <ChangeMap before={A.imageA} after={A.imageB} record={record} />
          ) : activeTab === 'dashboard' ? (
            <div className="h-full overflow-y-auto"><EvidencePanel record={record} highlightId={A.highlightId} onHighlight={A.setHighlightId} /></div>
          ) : (
            <MapViewer image={A.imageA} imageB={A.imageB} view={A.view}>
              {activeTab === 'map' && viz?.boxes?.length > 0 && <DetectionOverlay boxes={viz.boxes} itemsById={Object.fromEntries((record.evidence.items || []).map((i) => [i.id, i]))} highlightIds={highlightIds} focusId={A.highlightId} onSelect={A.setHighlightId} />}
              {activeTab === 'map' && viz?.change_regions?.length > 0 && <ChangeOverlay maskPng={viz.change_mask_png} regions={viz.change_regions} opacity={A.layers.opacity} highlightIds={highlightIds} focusId={A.highlightId} onSelect={A.setHighlightId} />}
              {activeTab === 'segment' && (
                <>
                  {viz?.masks?.length > 0 && <SegmentationOverlay masks={viz.masks} polygons={viz.polygons} opacity={A.layers.opacity} highlightIds={highlightIds} focusId={A.highlightId} onSelect={A.setHighlightId} />}
                  {segResult?.visualization?.masks?.length > 0 && record?.id !== segResult.id && <SegmentationOverlay masks={segResult.visualization.masks} polygons={segResult.visualization.polygons} opacity={A.layers.opacity} />}
                </>
              )}
            </MapViewer>
          )}
        </div>
        {activeTab === 'segment' && (
          <div className="flex flex-wrap items-center gap-1.5 border-t border-ink-600 px-3 py-2">
            <span className="text-xs text-mist-500">Class:</span>
            {SEG_CLASSES.map((c) => (<button key={c} disabled={segLoading || !A.imageA} onClick={() => runSegment(c)} className={`chip disabled:opacity-40 ${segClass === c ? 'border-signal text-signal' : 'hover:text-mist-100'}`}>{c.replace('_', ' ')}</button>))}
          </div>
        )}
      </section>

      <section className="hidden w-full shrink-0 lg:block lg:w-[380px]">
        <ChatPanel messages={A.messages} onSend={A.send} loading={A.loading} suggestions={suggestions} selectedId={record?.id} onOpen={(r) => { A.select(r); setActiveTab('dashboard') }} disabled={!A.imageA} />
      </section>
      <section className="border-t border-ink-600 lg:hidden">
        <div className="h-96"><ChatPanel messages={A.messages} onSend={A.send} loading={A.loading} suggestions={suggestions} selectedId={record?.id} onOpen={(r) => { A.select(r); setActiveTab('dashboard') }} disabled={!A.imageA} /></div>
      </section>
    </div>
  )
}
