import { useState } from "react";
import axios from "axios";
import "./App.css";

const API = "https://outreach-engine-pexa.onrender.com";

function App() {
  const [campaignId, setCampaignId] = useState("");
  const [file, setFile] = useState(null);
  const [prospects, setProspects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const createCampaign = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${API}/api/campaigns`, {
        name: "My Campaign",
      });
      setCampaignId(res.data.id);
      setMessage("✅ Campaign Created");
    } catch {
      setMessage("❌ Failed to create campaign");
    }
    setLoading(false);
  };

  const uploadCSV = async () => {
    if (!file) return setMessage("❌ Upload CSV first");

    try {
      const formData = new FormData();
      formData.append("file", file);

      setLoading(true);
      await axios.post(`${API}/api/campaigns/${campaignId}/upload`, formData);
      setMessage("📂 CSV Uploaded");
    } catch {
      setMessage("❌ Upload failed");
    }
    setLoading(false);
  };

  const generateEmails = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/api/campaigns/${campaignId}/generate`);
      setMessage("⚡ Emails Generated");
    } catch {
      setMessage("❌ Generation failed");
    }
    setLoading(false);
  };

  const sendEmails = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/api/campaigns/${campaignId}/send`);
      setMessage("🚀 Emails Sent");
    } catch {
      setMessage("❌ Sending failed");
    }
    setLoading(false);
  };

  const loadData = async () => {
    try {
      const res = await axios.get(
        `${API}/api/campaigns/${campaignId}/prospects`
      );
      setProspects(res.data);
    } catch {
      setMessage("❌ Failed to load data");
    }
  };

  return (
    <div className="container">
      <h1>🚀 Outreach AI</h1>
      <p className="subtitle">Automate your cold outreach with AI</p>

      {message && <p className="msg">{message}</p>}

      <div className="card">
        <button onClick={createCampaign} disabled={loading} className="btn">
          {loading ? "Creating..." : "Create Campaign"}
        </button>

        {campaignId && (
          <p>
            <b>Campaign ID:</b> {campaignId}
          </p>
        )}
      </div>

      <div className="card">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button onClick={uploadCSV} disabled={loading} className="btn">
          Upload CSV
        </button>
      </div>

      <div className="card">
        <button onClick={generateEmails} disabled={loading} className="btn">
          Generate Emails
        </button>

        <button onClick={sendEmails} disabled={loading} className="btn success">
          Send Emails
        </button>

        <button onClick={loadData} className="btn secondary">
          Load Data
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Status</th>
            <th>Opened</th>
          </tr>
        </thead>

        <tbody>
          {prospects.length === 0 && (
            <tr>
              <td colSpan="4">No data yet</td>
            </tr>
          )}

          {prospects.map((p) => (
            <tr key={p.id}>
              <td>{p.first_name}</td>
              <td>{p.email}</td>

              <td>
                <span
                  className={
                    p.generation_status === "sent"
                      ? "status sent"
                      : "status"
                  }
                >
                  {p.generation_status}
                </span>
              </td>

              <td>{p.opened ? "✅ Yes" : "❌ No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;s