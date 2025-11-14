/* C:\coding_projects\dev\schoolflow\frontend\src\pages\Login.tsx */
/**
 * Login page — uses react-hook-form + zod validation and useAuth.
 */

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../store/auth";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ui/use-toast";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

type Form = z.infer<typeof schema>;

export default function Login() {
  const { register, handleSubmit } = useForm<Form>({ resolver: zodResolver(schema) });
  const auth = useAuth();
  const nav = useNavigate();
  const toast = useToast();

  const onSubmit = async (values: Form) => {
    try {
      await auth.login(values.email, values.password);
      toast.push("Logged in");
      nav("/invoices");
    } catch (err) {
      console.error("login error", err);
      toast.push("Login failed");
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 bg-white p-6 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Sign in</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm">Email</label>
          <input {...register("email")} className="mt-1 w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm">Password</label>
          <input {...register("password")} type="password" className="mt-1 w-full border rounded px-3 py-2" />
        </div>
        <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">Login</button>
      </form>
    </div>
  );
}
