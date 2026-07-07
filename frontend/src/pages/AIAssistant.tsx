import { useEffect, useState } from 'react';
import { get, post } from '../services/api';

export default function AIAssistant() {
  const [ollamaStatus, setOllamaStatus] = useState<any>(null);
  const [wazuhStatus, setWazuhStatus] = useState<any>(null);
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [model, setModel] = useState('llama3.2:3b');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    get('/ollama/status').then(setOllamaStatus).catch(() => {});
    get('/wazuh/status').then(setWazuhStatus).catch(() => {});
  }, []);

  const send = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setResponse('');
    try {
      const res = await post<{ response?: string }>('/ollama/chat', { model, prompt });
      setResponse(res?.response || JSON.stringify(res, null, 2));
    } catch (e) {
      setResponse('AI chat failed: ' + e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ display: 'grid', gap: 16 }}>
      <div style={{ background: '#0b1220ee', border: '1px solid #34d39933', borderRadius: 16, padding: 20 }}>
        <h1 style={{ fontSize: 22, marginBottom: 12 }}>AI Assistant</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          <div>
            <div style={{ color: '#94a3b8', fontSize: 12 }}>Ollama</div>
            <div style={{ color: '#e2e8f0' }}>{ollamaStatus ? ollamaStatus.status : '...'}</div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: 12 }}>Wazuh</div>
            <div style={{ color: '#e2e8f0' }}>{wazuhStatus ? wazuhStatus.status : '...'}</div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: 12 }}>Model</div>
            <select value={model} onChange={(e) => setModel(e.target.value)} style={{ background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 8, padding: '6px 8px', width: '100%' }}>
              <option value="llama3.2:3b">llama3.2:3b</option>
              <option value="llama3.2:1b">llama3.2:1b</option>
              <option value="gemma:2b">gemma:2b</option>
            </select>
          </div>
        </div>
      </div>

      <div style={{ background: '#0b1220ee', border: '1px solid #34d39933', borderRadius: 16, padding: 20 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask the local model..."
            style={{ flex: 1, background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: 8, padding: '10px 12px' }}
          />
          <button disabled={loading} onClick={send} style={{ background: '#10b981', color: '#022c22', border: 'none', borderRadius: 8, padding: '10px 14px', fontWeight: 600 }}>Send</button>
        </div>
        {response && (
          <pre style={{ marginTop: 12, color: '#94a3b8', whiteSpace: 'pre-wrap' }}>{response}</pre>
        )}
      </div>
    </section>
  );
}
