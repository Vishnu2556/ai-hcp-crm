import React from "react";
import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar__brand">HCP CRM</div>
      <div className="navbar__links">
        <NavLink to="/" className={({ isActive }) => (isActive ? "active" : "")}>
          Dashboard
        </NavLink>
        <NavLink to="/log-interaction" className={({ isActive }) => (isActive ? "active" : "")}>
          Log Interaction
        </NavLink>
      </div>
    </nav>
  );
}