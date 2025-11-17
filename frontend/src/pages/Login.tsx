/* C:\coding_projects\dev\schoolflow\frontend\src\pages\Login.tsx */
import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../store/auth";
import { useNavigate } from "react-router-dom";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

type Form = z.infer<typeof schema>;

export default function Login() {
  const { register, handleSubmit } = useForm<Form>({ resolver: zodResolver(schema) });
  const auth = useAuth();
  const nav = useNavigate();

  const onSubmit = async (values: Form) => {
    try {
      // client-side login -> auth.login will POST x-www-form-urlencoded to backend
      await auth.login(values.email, values.password);
      // navigate on success
      nav("/invoices");
    } catch (err: any) {
      console.error("Login failed:", err);
      // user-visible feedback
      alert("Login failed: " + (err?.message || "Network or credentials error"));
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 bg-white p-6 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Sign in</h2>
      {/* IMPORTANT: no action attribute on the form to avoid browser navigation */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div>
          <label className="block text-sm">Email</label>
          <input {...register("email")} name="email" className="mt-1 w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm">Password</label>
          <input {...register("password")} name="password" type="password" className="mt-1 w-full border rounded px-3 py-2" />
        </div>
        <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded mt-4">Login</button>
      </form>
      <div className="mt-4 text-sm text-slate-600">
        Tip: use backend credentials — you can also verify login by calling the API from PowerShell.
      </div>
    </div>
  );
}
