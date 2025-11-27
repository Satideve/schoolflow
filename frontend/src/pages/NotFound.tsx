/* C:\coding_projects\dev\schoolflow\frontend\src\pages\NotFound.tsx */
import React from "react";
import { Link } from "react-router-dom";

const NotFound: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-4">
      <div className="text-6xl">??</div>
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="text-sm text-slate-600 dark:text-slate-300 max-w-md">
        The page you are looking for doesn&apos;t exist or may have been moved.
      </p>
      <Link
        to="/"
        className="mt-2 inline-flex items-center px-4 py-2 rounded bg-blue-600 text-white text-sm"
      >
        Go back to dashboard
      </Link>
    </div>
  );
};

export default NotFound;
