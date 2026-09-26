export default function About() {
  const refs = [
    ['Remote Sensing and Image Interpretation', 'Lillesand, Kiefer & Chipman', 'Fundamentals of satellite sensors, optical/SAR imagery and image interpretation underpin the segmentation and detection heuristics.'],
    ['GeoChat: Grounded Large Vision-Language Model for Remote Sensing', 'Research paper', 'Identified as relevant to natural-language image queries, visual question answering and region grounding — the direction the VLM adapter is designed for.'],
    ['Remote Sensing SpatioTemporal Vision-Language Models', 'Research survey', 'Informs the temporal-comparison / change-captioning direction of the change-detection module.'],
    ['BigEarthNet', 'Dataset', 'Paired Sentinel-1/2 imagery with text annotations — a target training/evaluation source for future real models.'],
    ['IIT Bombay decodes satellite images using natural language', 'The Hindu', 'Demonstrates practical relevance of natural-language satellite-image interaction for disaster response, agriculture and planning.'],
  ]
  return (
    <div className="mx-auto max-w-[900px] space-y-10 px-4 py-12">
      <div><h1 className="font-display text-3xl">About SatQuery AI</h1><p className="mt-3 text-mist-300">SatQuery AI is Team Cipher’s prototype for SIH26167 (Space Technology, Software). It is a working, evidence-grounded prototype — not a claim that trained deep-learning models are running behind it. The project README documents the active pipeline and what is real versus planned.</p></div>
      <div>
        <h2 className="font-display text-xl">Research alignment</h2>
        <ul className="mt-4 space-y-3">
          {refs.map(([t, s, d]) => (<li key={t} className="panel p-4"><p className="font-medium">{t}</p><p className="text-xs text-mist-500">{s}</p><p className="mt-1 text-sm text-mist-400">{d}</p></li>))}
        </ul>
      </div>
      <div><h2 className="font-display text-xl">Team</h2><p className="mt-2 text-mist-300">Team Cipher — Smart India Hackathon 2026, Problem Statement SIH26167.</p></div>
    </div>
  )
}
