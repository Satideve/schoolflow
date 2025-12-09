/* C:\coding_projects\dev\schoolflow\frontend\src\components\layout\Shell.tsx */
import React from "react";
import Navbar from "./Navbar";

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <main className="flex-1">
          <div className="max-w-6xl mx-auto w-full py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
