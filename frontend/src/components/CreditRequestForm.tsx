import React, { useState, useEffect } from "react";
import api from "../services/api";
import { TextField, Button, Box, Select, MenuItem, InputLabel, FormControl } from "@mui/material";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function CreditRequestForm() {
  const [userId, setUserId] = useState<number>(0);
  const [amount, setAmount] = useState<number>(0);
  const [result, setResult] = useState<string | null>(null);

  const [metrics, setMetrics] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);

  useEffect(() => {
    api.get("/metrics-dashboard", { params: { status: statusFilter } })
      .then(res => setMetrics(res.data))
      .catch(() => setMetrics([]));
  }, [statusFilter]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post("/credit-requests/", null, {
        params: { user_id: userId, amount },
      });
      setResult(`Credit request created: ${JSON.stringify(res.data)}`);
    } catch (err: any) {
      setResult(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleBarClick = (elements: any) => {
    if (elements.length > 0) {
      const idx = elements[0].index;
      setSelectedEndpoint(metrics[idx]?.endpoint || null);
    }
  };

  return (
    <>
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{ mb: 2 }}
        aria-labelledby="credit-request-form-title"
        role="form"
      >
        <h2 id="credit-request-form-title">Create Credit Request</h2>
        <TextField
          label="User ID"
          type="number"
          value={userId}
          onChange={e => setUserId(Number(e.target.value))}
          required
          sx={{ mr: 2 }}
          inputProps={{ 'aria-label': 'User ID' }}
        />
        <TextField
          label="Amount"
          type="number"
          value={amount}
          onChange={e => setAmount(Number(e.target.value))}
          required
          sx={{ mr: 2 }}
          inputProps={{ 'aria-label': 'Amount' }}
        />
        <Button type="submit" variant="contained" aria-label="Create Credit Request">
          Create Credit Request
        </Button>
        {result && (
          <div
            style={{ marginTop: 10 }}
            role="status"
            aria-live="polite"
          >
            {result}
          </div>
        )}
      </Box>

      {/* Dashboard Filters and Chart */}
      <section aria-labelledby="dashboard-metrics-title">
        <h2 id="dashboard-metrics-title">Credit Requests Metrics</h2>
        <FormControl sx={{ minWidth: 120, mb: 2 }}>
          <InputLabel id="status-filter-label">Status</InputLabel>
          <Select
            labelId="status-filter-label"
            id="status-filter"
            value={statusFilter}
            label="Status"
            onChange={e => setStatusFilter(e.target.value)}
            aria-label="Filter by status"
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="approved">Approved</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="rejected">Rejected</MenuItem>
          </Select>
        </FormControl>
        <Bar
          data={{
            labels: metrics.map(m => m.endpoint),
            datasets: [{
              label: 'Requests',
              data: metrics.map(m => m.count),
              backgroundColor: 'rgba(75,192,192,0.6)'
            }]
          }}
          options={{
            onClick: (evt, elements) => handleBarClick(elements),
            plugins: {
              legend: { display: false }
            }
          }}
          aria-label="Requests per endpoint chart"
          role="img"
        />
        {selectedEndpoint && (
          <div style={{ marginTop: 20 }}>
            <h3>Details for: {selectedEndpoint}</h3>
            {/* Render more details for the selected endpoint here */}
            <pre aria-label="Endpoint details" tabIndex={0}>
              {JSON.stringify(metrics.find(m => m.endpoint === selectedEndpoint), null, 2)}
            </pre>
          </div>
        )}
      </section>
    </>
  );
}