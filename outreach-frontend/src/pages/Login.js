import { useState } from "react";
import API from "../lib/api";
import "../App.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);

      const res = await API.post("/auth/login", {
        email,
        password,
      });

      // save token
      localStorage.setItem("token", res.data.access_token);

      setMsg("✅ Login successful");

      // redirect
      window.location.href = "/";
    } catch (err) {
      console.error(err);
      setMsg("❌ Login failed");
    }

    setLoading(false);
  };

  return (
    <div className="container">
      <h1>🔐 Login</h1>

      {msg && <p className="msg">{msg}</p>}

      <input
        type="email"
        placeholder="Email"
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />

      <button
        onClick={handleLogin}
        className="btn"
        disabled={loading}
      >
        {loading ? "Logging in..." : "Login"}
      </button>

      <p>
        Don’t have an account? <a href="/signup">Signup</a>
      </p>
    </div>
  );
}