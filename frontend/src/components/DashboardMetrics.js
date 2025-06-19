import React, { useEffect, useState } from "react";
import axios from "axios";
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function parseRequests(metricsText) {
  const lines = metricsText.split('\n');
  const requests = {};
  lines.forEach(line => {
    if (line.startsWith('http_requests_total')) {
      // Exemplo: http_requests_total{handler="/token",method="POST",status="2xx"} 2.0
      const match = line.match(/handler="([^"]+)",method="([^"]+)",status="([^"]+)"} ([\d.]+)/);
      if (match) {
        const handler = match[1];
        const method = match[2];
        const status = match[3];
        const count = Number(match[4]);
        const key = `${method} ${handler} (${status})`;
        requests[key] = count;
      }
    }
  });
  return requests;
}

export default function DashboardMetrics() {
  const [metrics, setMetrics] = useState("");
  const [requestsData, setRequestsData] = useState({});

  useEffect(() => {
    axios.get("http://localhost:8000/metrics")
      .then(res => {
        setMetrics(res.data);
        setRequestsData(parseRequests(res.data));
      })
      .catch(() => setMetrics("Could not load metrics"));
  }, []);

  return (
    <div>
      <h2>Prometheus Metrics</h2>
      <Bar
        data={{
          labels: Object.keys(requestsData),
          datasets: [{
            label: 'Requests per endpoint',
            data: Object.values(requestsData),
            backgroundColor: 'rgba(75,192,192,0.6)'
          }]
        }}
      />
      <pre style={{background: "#222", color: "#0f0", padding: "1em", borderRadius: "8px", overflowX: "auto"}}>
        {metrics}
      </pre>
    </div>
  );
}