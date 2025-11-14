/* C:\coding_projects\dev\schoolflow\frontend\src\components\layout\Shell.tsx */
import React from "react";
import Navbar from "./Navbar";

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <main className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
