import React, { useEffect, useState } from "react";
import axios from "axios";

type DashboardSummary = {
  total_requests: number;
  pending: number;
  approved: number;
  rejected: number;
};

export default function DashboardSummaryPanel() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    axios.get("http://localhost:8000/dashboard/summary")
      .then(res => setSummary(res.data))
      .catch(() => setSummary(null));
  }, []);

if (!summary) return (
  <div role="status" aria-live="polite">
    Loading dashboard summary...
  </div>
);

return (
  <section aria-labelledby="dashboard-summary-title">
    <h3 id="dashboard-summary-title">Dashboard Summary</h3>
    <ul>
      <li>Total Requests: {summary.total_requests}</li>
      <li>Pending: {summary.pending}</li>
      <li>Approved: {summary.approved}</li>
      <li>Rejected: {summary.rejected}</li>
    </ul>
  </section>
);
}