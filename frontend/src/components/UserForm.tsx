import React, { useState } from "react";
import api from "../services/api";
import { TextField, Button, Box } from "@mui/material";

export default function UserForm() {
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("");
  const [result, setResult] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post("/users/", null, {
        params: { username, role },
      });
      setResult(`User created: ${JSON.stringify(res.data)}`);
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
        label="Role"
        value={role}
        onChange={e => setRole(e.target.value)}
        required
        sx={{ mr: 2 }}
      />
      <Button type="submit" variant="contained">Create User</Button>
      {result && <div style={{ marginTop: 10 }}>{result}</div>}
    </Box>
  );
}