import React from "react";
import UserForm from "../components/UserForm";
import CreditRequestForm from "../components/CreditRequestForm";
import CreditRequestList from "../components/CreditRequestList";

export default function Home() {
  return (
    <div>
      <UserForm />
      <CreditRequestForm />
      <CreditRequestList />
    </div>
  );
}