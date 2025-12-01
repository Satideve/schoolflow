// C:\coding_projects\dev\schoolflow\frontend\src\pages\Register.tsx
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import { useToast } from "../components/ui/use-toast";

type RegisterForm = {
  email: string;
  password: string;
  role: string;
};

const Register: React.FC = () => {
  const [form, setForm] = useState<RegisterForm>({
    email: "",
    password: "",
    role: "student",
  });
  const [submitting, setSubmitting] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  const handleChange = (field: keyof RegisterForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit: React.FormEventHandler = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) return;

    setSubmitting(true);
    try {
      // Backend endpoint: POST /api/v1/auth/register
      await api.post("/api/v1/auth/register", {
        email: form.email.trim(),
        password: form.password,
        role: form.role,
      });

      toast.push("Account created. Please login.");
      navigate("/login");
    } catch (err: any) {
      console.error("register failed", err);
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Registration failed. Please try again.";
      toast.push(String(detail));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-full max-w-md bg-white dark:bg-gray-900 shadow rounded-lg p-6 space-y-5">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
            Create an account
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            For now, this is intended mainly for student/parent self-signup.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
              Email
            </label>
            <input
              type="email"
              autoComplete="email"
              className="w-full border rounded px-3 py-2 text-sm bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.email}
              onChange={(e) => handleChange("email", e.target.value)}
              required
            />
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
              Password
            </label>
            <input
              type="password"
              autoComplete="new-password"
              className="w-full border rounded px-3 py-2 text-sm bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.password}
              onChange={(e) => handleChange("password", e.target.value)}
              required
            />
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">
              Role
            </label>
            <select
              className="w-full border rounded px-3 py-2 text-sm bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.role}
              onChange={(e) => handleChange("role", e.target.value)}
            >
              <option value="student">Student</option>
              <option value="parent">Parent</option>
              {/* We deliberately do NOT expose admin-like roles here */}
            </select>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full inline-flex items-center justify-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium disabled:opacity-60 hover:bg-blue-700"
          >
            {submitting ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="text-xs text-slate-600 dark:text-slate-400">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 hover:text-blue-700">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
