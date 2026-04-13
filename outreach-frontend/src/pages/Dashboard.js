import { useState, useEffect } from "react";
import API from "../lib/api";
import "../App.css";

function Dashboard() {
  const [campaignId, setCampaignId] = useState("");
  const [file, setFile] = useState(null);
  const [prospects, setProspects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // 🔐 Logout
  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  // 🚀 Create Campaign
  const createCampaign = async () => {
    try {
      setLoading(true);

      const res = await API.post("/api/campaigns", {
        name: "My Campaign",
      });

      setCampaignId(res.data.id);
      setMessage("✅ Campaign Created");

    } catch (err) {
      console.log(err);
      setMessage("❌ Failed to create campaign");
    }

    setLoading(false);
  };

  // 📂 Upload CSV
  const uploadCSV = async () => {
    if (!file) return setMessage("❌ Upload CSV first");

    try {
      const formData = new FormData();
      formData.append("file", file);

      setLoading(true);

      await API.post(
        `/api/campaigns/${campaignId}/upload`,
        formData
      );

      setMessage("📂 CSV Uploaded");

    } catch (err) {
      console.log(err);
      setMessage("❌ Upload failed");
    }

    setLoading(false);
  };

  // ⚡ Generate Emails
  const generateEmails = async () => {
    try {
      setLoading(true);

      await API.post(
        `/api/campaigns/${campaignId}/generate`
      );

      setMessage("⚡ Emails Generated");

    } catch (err) {
      console.log(err);
      setMessage("❌ Generation failed");
    }

    setLoading(false);
  };

  // 🚀 Send Emails (UPDATED FIX)
  const sendEmails = async () => {
    try {
      setLoading(true);

      const res = await API.post(
        `/api/campaigns/${campaignId}/send`
      );

      if (res.data.count === 0) {
        setMessage("⚠️ No emails sent");
      } else {
        setMessage(`🚀 ${res.data.count} Emails Sent`);
      }

    } catch (err) {
      console.log(err);
      setMessage("❌ Sending failed");
    }

    setLoading(false);
  };

  // 📊 Load Data
  const loadData = async () => {
    try {
      const res = await API.get(
        `/api/campaigns/${campaignId}/prospects`
      );

      setProspects(res.data);

    } catch (err) {
      console.log(err);
      setMessage("❌ Failed to load data");
    }
  };

  // 📊 Stats
  const total = prospects.length;
  const sent = prospects.filter(p => p.generation_status === "done").length;
  const opened = prospects.filter(p => p.opened).length;
  const openRate = total ? ((opened / total) * 100).toFixed(1) : 0;

  return (
    <div className="container">
      <h1>🚀 Outreach AI</h1>
      <p className="subtitle">Automate your cold outreach with AI</p>

      <button onClick={logout} className="btn danger">
        Logout
      </button>

      {message && <p className="msg">{message}</p>}

      {/* Stats */}
      <div className="stats">
        <div>Total: {total}</div>
        <div>Sent: {sent}</div>
        <div>Opened: {opened}</div>
        <div>Open Rate: {openRate}%</div>
      </div>

      {/* Create Campaign */}
      <div className="card">
        <button onClick={createCampaign} disabled={loading} className="btn">
          {loading ? "Creating..." : "Create Campaign"}
        </button>

        {campaignId && <p>ID: {campaignId}</p>}
      </div>

      {/* Upload CSV */}
      <div className="card">
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button onClick={uploadCSV} className="btn">
          Upload CSV
        </button>
      </div>

      {/* Actions */}
      <div className="card">
        <button onClick={generateEmails} className="btn">
          Generate Emails
        </button>

        <button onClick={sendEmails} className="btn success">
          Send Emails
        </button>

        <button onClick={loadData} className="btn secondary">
          Load Data
        </button>
      </div>

      {/* Table */}
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

              <td>{p.generation_status}</td>
              <td>{p.opened ? "✅ Yes" : "❌ No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Dashboard;