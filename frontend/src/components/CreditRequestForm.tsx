import React, { useState } from "react";
import api from "../services/api";
import { TextField, Button, Box } from "@mui/material";

export default function CreditRequestForm() {
  const [userId, setUserId] = useState<number>(0);
  const [amount, setAmount] = useState<number>(0);
  const [result, setResult] = useState<string | null>(null);

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

return (
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
);
}