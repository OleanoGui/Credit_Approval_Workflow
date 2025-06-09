import React, { useEffect, useState } from "react";
import api from "../services/api";
import { Table, TableBody, TableCell, TableHead, TableRow, Paper, Typography } from "@mui/material";

type CreditRequest = {
  id: number;
  user_id: number;
  amount: number;
  status: string;
};

export default function CreditRequestList() {
  const [requests, setRequests] = useState<CreditRequest[]>([]);

  useEffect(() => {
    api.get("/credit-requests/").then(res => setRequests(res.data));
  }, []);

  return (
    <Paper sx={{ mt: 2, p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Credit Requests
      </Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>User ID</TableCell>
            <TableCell>Amount</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {requests.map(req => (
            <TableRow key={req.id}>
              <TableCell>{req.id}</TableCell>
              <TableCell>{req.user_id}</TableCell>
              <TableCell>{req.amount}</TableCell>
              <TableCell>{req.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}