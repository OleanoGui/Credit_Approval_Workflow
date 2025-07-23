import { render, screen, fireEvent } from "@testing-library/react";
import CreditRequestForm from "./CreditRequestForm";

test("renders credit request form", () => {
  render(<CreditRequestForm />);
  expect(screen.getByLabelText(/User ID/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Amount/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Create Credit Request/i })).toBeInTheDocument();
});

test("submits form with user input", () => {
  render(<CreditRequestForm />);
  fireEvent.change(screen.getByLabelText(/User ID/i), { target: { value: "2" } });
  fireEvent.change(screen.getByLabelText(/Amount/i), { target: { value: "5000" } });
  fireEvent.click(screen.getByRole("button", { name: /Create Credit Request/i }));
});