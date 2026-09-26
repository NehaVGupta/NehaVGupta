import { useCallback, useRef, useState } from 'react'
import { api } from '../services/api'
import { useQuery } from './useQuery'
import { useUpload } from './useUpload'

const newSession = () => 's-' + Math.random().toString(36).slice(2, 12)

/** Workspace state: images, conversation, selected analysis, layer settings. */
export function useAnalysis() {
  const session = useRef(newSession())
  const operation = useRef(0)
  const [dataset, setDataset] = useState(null)
  const [imageA, setImageA] = useState(null)
  const [imageB, setImageB] = useState(null)
  const [messages, setMessages] = useState([])
  const [selected, setSelected] = useState(null)
  const [highlightId, setHighlightId] = useState(null)
  const [view, setView] = useState('A')
  const [mode, setMode] = useState('map')
  const [layers, setLayers] = useState({ detections: true, masks: true, change: true, opacity: 0.85 })
  const [notice, setNotice] = useState(null)
  const [datasetLoading, setDatasetLoading] = useState(false)
  const up = useUpload()
  const q = useQuery()

  const reset = useCallback(() => { ++operation.current; session.current = newSession(); setMessages([]); setSelected(null); setHighlightId(null); setMode('map'); setView('A') }, [])

  const loadDataset = useCallback(async (name) => {
    const currentOperation = ++operation.current
    setNotice(null)
    setDatasetLoading(true)
    try {
      const r = await api.demoLoad(name)
      if (currentOperation !== operation.current) return null
      reset()
      setDataset(r.dataset); setImageA(r.images[0]); setImageB(r.images[1] || null)
      return r
    } catch (e) {
      if (currentOperation === operation.current) setNotice(e.message)
      return null
    } finally {
      if (currentOperation === operation.current) setDatasetLoading(false)
    }
  }, [reset])

  const setImage = useCallback(async (role, file) => {
    const currentOperation = ++operation.current
    const rec = await up.upload(file)
    if (!rec) return
    if (currentOperation !== operation.current) return
    setDataset(null)
    if (role === 'a') { reset(); setImageA(rec) } else setImageB(rec)
  }, [up, reset])

  const clearImage = useCallback((role) => {
    ++operation.current
    if (role === 'a') { setImageA(null); setImageB(null); setDataset(null); reset() } else setImageB(null)
  }, [reset])

  const select = useCallback((rec) => {
    setSelected(rec); setHighlightId(null)
    const v = rec?.visualization?.view
    setView(v === 'A' || !v ? 'A' : 'B')
  }, [])

  const send = useCallback(async (text, a = imageA, b = imageB) => {
    if (!text.trim()) return null
    if (!a) { setNotice('Choose an image before asking a question.'); return null }
    const currentOperation = operation.current
    setNotice(null)
    setMessages((m) => [...m, { role: 'user', text }])
    const rec = await q.ask({ query: text, image_id: a.id, image_b_id: b?.id, session_id: session.current })
    if (currentOperation !== operation.current) return null
    if (!rec) {
      setMessages((m) => [...m, { role: 'assistant', error: true, text: 'I could not complete that analysis. Please try again.' }])
      return null
    }
    setMessages((m) => [...m, { role: 'assistant', text: rec.answer, record: rec }])
    select(rec)
    return rec
  }, [imageA, imageB, q, select])

  const openAnalysis = useCallback(async (id) => {
    try {
      const rec = await api.analysis(id)
      const a = await api.imageMeta(rec.image_ids.a)
      const b = rec.image_ids.b ? await api.imageMeta(rec.image_ids.b) : null
      reset(); setImageA(a); setImageB(b)
      setMessages([{ role: 'user', text: rec.query }, { role: 'assistant', text: rec.answer, record: rec }])
      select(rec)
    } catch (e) { setNotice(e.message) }
  }, [reset, select])

  return {
    dataset, imageA, imageB, messages, selected, highlightId, view, mode, layers, notice, setNotice,
    loading: q.loading, datasetLoading, uploading: up.uploading, uploadError: up.error, queryError: q.error,
    loadDataset, setImage, clearImage, send, select, openAnalysis, setHighlightId, setView, setMode,
    setLayers: (p) => setLayers((l) => ({ ...l, ...p })),
  }
}
