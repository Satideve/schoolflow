/* C:\coding_projects\dev\schoolflow\frontend\src\components\layout\Navbar.tsx */
import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../store/auth";

export default function Navbar() {
  const auth = useAuth();

  const role: string | undefined = auth.user?.role;
  const isAdminLike =
    role === "admin" || role === "clerk" || role === "accountant";

  const roleLabel = role
    ? role.charAt(0).toUpperCase() + role.slice(1)
    : "User";

  const idLabel = auth.user?.id ? `#${auth.user.id}` : "";

  return (
    <header className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-6xl mx_auto px-4 sm:px-6 lg:px-8">
        <div className="h-16 flex items-center justify-between">
          {/* Left side: brand + nav links */}
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="text-xl font-semibold text-slate-900 dark:text-white"
            >
              SchoolFlow
            </Link>
            {/* Always show nav links (no hidden sm:flex) */}
            <nav className="flex gap-3 flex-wrap">
              {isAdminLike ? (
                <>
                  <Link
                    to="/invoices"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Invoices
                  </Link>
                  <Link
                    to="/receipts"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Receipts
                  </Link>
                  <Link
                    to="/fee-assignments"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Fee Assignments
                  </Link>
                  <Link
                    to="/class-sections"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Class Sections
                  </Link>
                  <Link
                    to="/students"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Students
                  </Link>
                  <Link
                    to="/fee-components"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Fee Components
                  </Link>
                  <Link
                    to="/fee-plans"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    Fee Plans
                  </Link>
                  <Link
                    to="/admin/csv"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    CSV Import
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/my/invoices"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    My Invoices
                  </Link>
                  <Link
                    to="/my/receipts"
                    className="text-sm text-slate-600 dark:text-slate-300"
                  >
                    My Receipts
                  </Link>
                </>
              )}
              <Link
                to="/about"
                className="text-sm text-slate-600 dark:text-slate-300"
              >
                About
              </Link>
            </nav>
          </div>

          {/* Right side: auth controls + dynamic user label */}
          <div className="flex items-center gap-3">
            <div className="text-sm text-slate-600 dark:text-slate-300">
              {roleLabel} {idLabel}
            </div>

            {auth.token ? (
              <button
                onClick={() => auth.logout()}
                className="text-sm text-red-600"
              >
                Logout
              </button>
            ) : (
              <Link to="/login" className="text-sm text-blue-600">
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
