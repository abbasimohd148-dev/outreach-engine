import { useState } from "react";
import axios from "axios";

const API = "https://outreach-engine-pexa.onrender.com";

function App() {
  const [campaignId, setCampaignId] = useState("");
  const [file, setFile] = useState(null);
  const [prospects, setProspects] = useState([]);

  const createCampaign = async () => {
    const res = await axios.post(`${API}/api/campaigns`, {
      name: "My Campaign",
    });
    setCampaignId(res.data.id);
    alert("Campaign Created");
  };

  const uploadCSV = async () => {
    const formData = new FormData();
    formData.append("file", file);

    await axios.post(`${API}/api/campaigns/${campaignId}/upload`, formData);
    alert("CSV Uploaded");
  };

  const generateEmails = async () => {
    await axios.post(`${API}/api/campaigns/${campaignId}/generate`);
    alert("Emails Generated");
  };

  const sendEmails = async () => {
    await axios.post(`${API}/api/campaigns/${campaignId}/send`);
    alert("Emails Sent");
  };

  const fetchProspects = async () => {
    const res = await axios.get(
      `${API}/api/campaigns/${campaignId}/prospects`
    );
    setProspects(res.data);
  };

  return (
    <div style={{ padding: "30px", fontFamily: "Arial" }}>
      <h1>🚀 Outreach SaaS Dashboard</h1>

      <button onClick={createCampaign}>Create Campaign</button>

      <h3>Campaign ID:</h3>
      <p>{campaignId}</p>

      <hr />

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={uploadCSV}>Upload CSV</button>

      <hr />

      <button onClick={generateEmails}>Generate Emails</button>
      <button onClick={sendEmails}>Send Emails</button>

      <hr />

      <button onClick={fetchProspects}>Load Data</button>

      <table border="1" cellPadding="10" style={{ marginTop: "20px" }}>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Status</th>
            <th>Opened</th>
          </tr>
        </thead>
        <tbody>
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

export default App;