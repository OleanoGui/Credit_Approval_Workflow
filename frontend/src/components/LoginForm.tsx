import React, { useState } from "react";
import api from "../services/api";
import { TextField, Button, Box } from "@mui/material";

export default function LoginForm({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [result, setResult] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post("/token", new URLSearchParams({ username, password }));
      onLogin(res.data.access_token);
      setResult("Login successful!");
    } catch (err: any) {
      setResult(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <TextField
        label="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        required
        sx={{ mr: 2 }}
      />
      <TextField
        label="Password"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
        sx={{ mr: 2 }}
      />
      <Button type="submit" variant="contained">Login</Button>
      {result && <div style={{ marginTop: 10 }}>{result}</div>}
    </Box>
  );
}