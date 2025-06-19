import React, { useEffect, useState } from "react";
import axios from "axios";

function DashboardMetrics() {
  const [metrics, setMetrics] = useState("");

  useEffect(() => {
    axios.get("http://localhost:8000/metrics")
      .then(res => setMetrics(res.data))
      .catch(() => setMetrics("Could not load metrics"));
  }, []);

  return (
    <div>
      <h2>Prometheus Metrics</h2>
      <pre style={{background: "#222", color: "#0f0", padding: "1em", borderRadius: "8px", overflowX: "auto"}}>
        {metrics}
      </pre>
    </div>
  );
}

export default DashboardMetrics;