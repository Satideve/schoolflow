// C:\coding_projects\dev\schoolflow\frontend\src\pages\About.tsx
import React from "react";
import Card from "../components/ui/card";

const About: React.FC = () => {
  return (
    <Card>
      <h1 className="text-xl font-semibold mb-2">About SchoolFlow (Fees)</h1>
      <p className="text-sm text-slate-700 dark:text-slate-300">
        Frontend scaffold for SchoolFlow fee module. This app talks to your backend at <code>VITE_API_BASE</code>.
      </p>
      <div className="mt-4">
        <a className="text-sm text-sky-600" href="/api/v1/health/liveness" target="_blank" rel="noreferrer">Backend Liveness</a>
      </div>
    </Card>
  );
};

export default About;
