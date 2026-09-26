import { useRef, useState } from 'react'
import { api } from '../services/api'

export default function UploadPanel({ label, image, onFile, onClear, uploading, hint }) {
  const input = useRef()
  const [over, setOver] = useState(false)
  const drop = (e) => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files?.[0]; if (f) onFile(f) }
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm"><span className="font-medium">{label}</span>{image && <button className="text-xs text-mist-500 hover:text-mist-100" onClick={onClear}>Remove</button>}</div>
      {image ? (
        <div className="overflow-hidden rounded-md border border-ink-600">
          <img src={api.imageUrl(image.id)} alt={image.name} className="h-24 w-full object-cover" />
          <div className="flex items-center justify-between px-2 py-1 text-xs text-mist-300"><span className="truncate">{image.name}</span>{image.synthetic && <span className="chip !py-0">synthetic</span>}</div>
        </div>
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)} onDrop={drop}
          onClick={() => input.current.click()} onKeyDown={(e) => e.key === 'Enter' && input.current.click()} role="button" tabIndex={0}
          className={`flex h-24 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed text-center text-xs transition-colors ${over ? 'border-signal bg-signal/5' : 'border-ink-600 hover:border-mist-500'}`}
        >
          {uploading ? 'Uploading…' : <><span className="text-mist-100">Drop or click to upload</span><span className="text-mist-500">{hint || 'PNG, JPG, GeoTIFF · max 50 MB'}</span></>}
          <input ref={input} type="file" accept=".png,.jpg,.jpeg,.tif,.tiff" hidden onChange={(e) => { if (e.target.files[0]) onFile(e.target.files[0]); e.target.value = '' }} />
        </div>
      )}
    </div>
  )
}
