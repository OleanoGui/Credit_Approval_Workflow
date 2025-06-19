import React from "react";
import CreditRequestList from "../components/CreditRequestList";
import DashboardMetrics from "../components/DashboardMetrics";
import DashboardSummaryPanel from "../components/DashboardSummaryPanel";

export default function Dashboard() {
  return (
    <div>
      <h2>Dashboard</h2>
      <DashboardSummaryPanel />
      <CreditRequestList />
      <DashboardMetrics />
    </div>
  );
}