import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import API from "./lib/api";

function App() {
  // 🔥 PRE-WARM BACKEND
  useEffect(() => {
    API.get("/health").catch(() => {});
  }, []);

  const token = localStorage.getItem("token");

  return (
    <Router>
      <Routes>
        {!token ? (
          <>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="*" element={<Login />} />
          </>
        ) : (
          <>
            <Route path="/" element={<Dashboard />} />
            <Route path="*" element={<Dashboard />} />
          </>
        )}
      </Routes>
    </Router>
  );
}

export default App;