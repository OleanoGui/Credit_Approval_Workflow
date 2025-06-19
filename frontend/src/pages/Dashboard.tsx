import React from "react";
import CreditRequestList from "../components/CreditRequestList";
import DashboardMetrics from "../components/DashboardMetrics";

export default function Dashboard() {
  return (
    <div>
      <h2>Dashboard</h2>
      <CreditRequestList />
      <DashboardMetrics />
    </div>
  );
}