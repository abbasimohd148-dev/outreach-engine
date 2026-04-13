import { useState, useEffect } from "react";
import API from "../lib/api";
import "../App.css";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // 🚀 Wake up backend (Render cold start fix)
  useEffect(() => {
    API.get("/health").catch(() => {});
  }, []);

  const handleSignup = async () => {
    try {
      setLoading(true);

      await API.post("/auth/signup", {
        email,
        password,
      });

      setMsg("✅ Signup successful");

      // Redirect to login
      setTimeout(() => {
        window.location.href = "/login";
      }, 1000);

    } catch (err) {
      console.error(err);
      setMsg("❌ Signup failed");
    }

    setLoading(false);
  };

  return (
    <div className="container">
      <h1>📝 Signup</h1>

      {msg && <p className="msg">{msg}</p>}

      <div className="card">
        <input
          type="email"
          placeholder="Enter Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Enter Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={handleSignup}
          className="btn"
          disabled={loading}
        >
          {loading ? "Creating..." : "Signup"}
        </button>

        <p style={{ marginTop: "10px" }}>
          Already have an account?{" "}
          <span
            style={{ color: "#00d4ff", cursor: "pointer" }}
            onClick={() => (window.location.href = "/login")}
          >
            Login
          </span>
        </p>
      </div>
    </div>
  );
}