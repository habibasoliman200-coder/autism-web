import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import axios from "axios";
import "./Layout.css";

const links = [
  { to: "/live", label: "Live monitor" },
  { to: "/alerts", label: "Alert history" },
  { to: "/trends", label: "Trends" },
  { to: "/profile", label: "Child profile" },
  { to: "/caregivers", label: "Caregivers" },
];

export default function Layout() {
  const navigate = useNavigate();
  const [sensorData, setSensorData] = useState([]);

  useEffect(() => {
    // جلب البيانات مباشرة من سيرفر Flask
    axios
      .get("http://127.0.0.1:5000/api/sensor")
      .then((res) => {
        if (res.data) {
          setSensorData(res.data);
        }
      })
      .catch((err) => console.error("خطأ في جلب البيانات:", err));
  }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">CalmiSense</div>

        {/* عرض القراءات */}
        <div
          style={{
            padding: "10px",
            margin: "10px 0",
            backgroundColor: "#1e293b",
            borderRadius: "8px",
            color: "#fff",
          }}
        >
          <p style={{ fontSize: "12px", fontWeight: "bold", marginBottom: "5px" }}>
            قراءات السوار الحالية:
          </p>
          {sensorData.length === 0 ? (
            <p style={{ fontSize: "11px", color: "#94a3b8" }}>جاري التحميل...</p>
          ) : (
            <div style={{ fontSize: "12px" }}>
              <p>❤️ النبض: {sensorData[0]?.heart_rate ?? "N/A"}</p>
              <p>🌡️ الحرارة: {sensorData[0]?.temperature ?? "N/A"}</p>
              <p>⚡ GSR: {sensorData[0]?.gsr ?? "N/A"}</p>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <button
          className="signout"
          onClick={() => {
            localStorage.removeItem("loggedIn");
            navigate("/login");
          }}
        >
          Sign out
        </button>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}