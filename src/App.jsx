import React, { useState } from 'react'

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

  const onExtract = async () => {
    if(!file){ setStatus('Choose an image'); return }
    setLoading(true); setStatus('')
    try{
      const form = new FormData()
      form.append('file', file)
      form.append('use_gemini', String(useGemini))
      const res = await fetch('/api/extract', { method:'POST', body: form })
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
      const res = await fetch('/api/save', { method:'POST', body: form })
      if(!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setStatus('Saved: ' + JSON.stringify(data))
    }catch(e){
      setStatus('Save failed: ' + e.message)
    }finally{ setLoading(false) }
  }

  return (
    <div style={{maxWidth: 800, margin:'32px auto', padding: 16}}>
      <h2 style={{fontSize:24, fontWeight:700, marginBottom:12}}>Business Card OCR</h2>
      <p style={{marginBottom:16}}>Upload a visiting card image, extract fields with OCR and Gemini, then review and save.</p>

      <div style={{display:'flex', gap:12, alignItems:'center', marginBottom:12}}>
        <input type="file" accept="image/*" onChange={e=> setFile(e.target.files?.[0] || null)} />
        <label style={{display:'flex', alignItems:'center', gap:6}}>
          <input type="checkbox" checked={useGemini} onChange={e=> setUseGemini(e.target.checked)} /> Use Gemini
        </label>
        <button onClick={onExtract} disabled={loading} style={{padding:'8px 12px'}}>Extract</button>
      </div>

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