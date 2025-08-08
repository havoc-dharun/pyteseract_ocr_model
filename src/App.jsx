import React, { useEffect, useRef, useState } from 'react'

function Field({label, value, onChange, name}) {
  return (
    <div style={{marginBottom: 8}}>
      <label style={{display:'block', fontWeight:'600', marginBottom:4}}>{label}</label>
      <input name={name} value={value} onChange={e=>onChange(e.target.value)} style={{width:'100%', padding:8, border:'1px solid #ccc', borderRadius:6}} />
    </div>
  )
}

export default function App(){
  const [file, setFile] = useState(null)
  const [useGemini, setUseGemini] = useState(true)
  const [loading, setLoading] = useState(false)
  const [ocrText, setOcrText] = useState('')
  const [fields, setFields] = useState({Name:'', Phone:'', Email:'', Company:'', Address:'', Website:''})
  const [status, setStatus] = useState('')

  // API base for Netlify/hosted environments
  const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/+$/, '')

  // Camera state
  const [useCamera, setUseCamera] = useState(false)
  const videoRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [capturedBlob, setCapturedBlob] = useState(null)

  useEffect(()=>{
    // Cleanup on unmount
    return () => {
      stopCamera()
    }
  }, [])

  useEffect(()=>{
    if (!useCamera) {
      stopCamera()
      setCapturedBlob(null)
    }
  }, [useCamera])

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        await videoRef.current.play()
      }
      setStream(mediaStream)
      setStatus('')
    } catch (e) {
      setStatus('Camera error: ' + e.message)
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(t => t.stop())
    }
    if (videoRef.current) {
      videoRef.current.pause()
      videoRef.current.srcObject = null
    }
    setStream(null)
  }

  const captureFrame = async () => {
    const video = videoRef.current
    if (!video) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    await new Promise(resolve => canvas.toBlob(async (blob)=>{
      if (!blob) return resolve()
      setCapturedBlob(blob)
      setFile(new File([blob], 'camera.jpg', { type: 'image/jpeg' }))
      resolve()
    }, 'image/jpeg', 0.92))
  }

  const retake = () => {
    setCapturedBlob(null)
    setFile(null)
    if (!stream) {
      startCamera()
    }
  }

  const onExtract = async () => {
    const inputBlob = capturedBlob || (file ? file : null)
    if(!inputBlob){ setStatus('Choose an image or capture from camera'); return }
    setLoading(true); setStatus('')
    try{
      const form = new FormData()
      // If we have a captured blob, send it; otherwise send selected file
      if (capturedBlob) {
        form.append('file', new File([capturedBlob], 'capture.jpg', { type: 'image/jpeg' }))
      } else if (file) {
        form.append('file', file)
      }
      form.append('use_gemini', String(useGemini))
      const res = await fetch(`${API_BASE}/api/extract`, { method:'POST', body: form })
      if(!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setOcrText(data.ocr_text || '')
      const f = data.fields || {}
      setFields({
        Name: f.Name || '',
        Phone: f.Phone || '',
        Email: f.Email || '',
        Company: f.Company || '',
        Address: f.Address || '',
        Website: f.Website || ''
      })
    }catch(e){
      setStatus('Extract failed: ' + e.message)
    }finally{ setLoading(false) }
  }

  const onSave = async (toSheet) => {
    setLoading(true); setStatus('')
    try{
      const form = new FormData()
      Object.entries(fields).forEach(([k,v])=> form.append(k.toLowerCase(), v))
      form.append('to_csv', 'true')
      form.append('to_sheet', String(!!toSheet))
      const res = await fetch(`${API_BASE}/api/save`, { method:'POST', body: form })
      if(!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setStatus('Saved: ' + JSON.stringify(data))
    }catch(e){
      setStatus('Save failed: ' + e.message)
    }finally{ setLoading(false) }
  }

  return (
    <div style={{maxWidth: 900, margin:'32px auto', padding: 16}}>
      <h2 style={{fontSize:24, fontWeight:700, marginBottom:12}}>Business Card OCR</h2>
      <p style={{marginBottom:16}}>Upload a visiting card image or scan with your camera, extract fields with OCR and Gemini, then review and save.</p>

      <div style={{display:'flex', gap:12, alignItems:'center', marginBottom:12, flexWrap:'wrap'}}>
        <label style={{display:'flex', alignItems:'center', gap:6}}>
          <input type="checkbox" checked={useCamera} onChange={e=> setUseCamera(e.target.checked)} /> Use Camera
        </label>
        {!useCamera && (
          <input type="file" accept="image/*" onChange={e=> { setFile(e.target.files?.[0] || null); setCapturedBlob(null) }} />
        )}
        <label style={{display:'flex', alignItems:'center', gap:6}}>
          <input type="checkbox" checked={useGemini} onChange={e=> setUseGemini(e.target.checked)} /> Use Gemini
        </label>
        <button onClick={onExtract} disabled={loading} style={{padding:'8px 12px'}}>Extract</button>
      </div>

      {useCamera && (
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, alignItems:'start', marginBottom:16}}>
          <div>
            <div style={{position:'relative', background:'#000', borderRadius:8, overflow:'hidden'}}>
              {!capturedBlob ? (
                <video ref={videoRef} style={{width:'100%', height:'auto'}} playsInline muted />
              ) : (
                <img alt="capture" src={URL.createObjectURL(capturedBlob)} style={{width:'100%', height:'auto', display:'block'}} />
              )}
            </div>
            <div style={{display:'flex', gap:8, marginTop:8}}>
              {!stream && !capturedBlob && <button onClick={startCamera} style={{padding:'8px 12px'}}>Start Camera</button>}
              {stream && !capturedBlob && <button onClick={captureFrame} style={{padding:'8px 12px'}}>Capture</button>}
              {(stream || capturedBlob) && <button onClick={()=> { stopCamera(); retake() }} style={{padding:'8px 12px'}}>Stop/Retake</button>}
            </div>
          </div>
          <div>
            <small>Tip: Use the rear camera on mobile for better OCR accuracy.</small>
          </div>
        </div>
      )}

      {ocrText && (
        <details style={{marginBottom:16}}>
          <summary>OCR Text</summary>
          <pre style={{whiteSpace:'pre-wrap'}}>{ocrText}</pre>
        </details>
      )}

      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
        <Field label="Name" value={fields.Name} onChange={v=> setFields(s=>({...s, Name:v}))} name="name" />
        <Field label="Phone" value={fields.Phone} onChange={v=> setFields(s=>({...s, Phone:v}))} name="phone" />
        <Field label="Email" value={fields.Email} onChange={v=> setFields(s=>({...s, Email:v}))} name="email" />
        <Field label="Company" value={fields.Company} onChange={v=> setFields(s=>({...s, Company:v}))} name="company" />
        <Field label="Address" value={fields.Address} onChange={v=> setFields(s=>({...s, Address:v}))} name="address" />
        <Field label="Website" value={fields.Website} onChange={v=> setFields(s=>({...s, Website:v}))} name="website" />
      </div>

      <div style={{display:'flex', gap:12, marginTop:16}}>
        <button onClick={()=> onSave(false)} disabled={loading} style={{padding:'8px 12px'}}>Save to CSV</button>
        <button onClick={()=> onSave(true)} disabled={loading} style={{padding:'8px 12px'}}>Save to CSV + Google Sheet</button>
      </div>

      {status && <p style={{marginTop:12}}>{status}</p>}
    </div>
  )
}