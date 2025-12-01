/* C:\coding_projects\dev\schoolflow\frontend\src\components\layout\Navbar.tsx */
import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../store/auth";
import { useStudents } from "../../api/queries";

export default function Navbar() {
  const auth = useAuth();
  const role: string | undefined = auth.user?.role;

  const isAdminLike =
    role === "admin" || role === "clerk" || role === "accountant";

  const roleLabel = role
    ? role.charAt(0).toUpperCase() + role.slice(1)
    : "User";

  // -----------------------------
  // Student name lookup
  // -----------------------------
  const { data: students } = useStudents();

  const studentName = useMemo(() => {
    const studentId = (auth.user as any)?.student_id;
    if (!studentId) return null;

    const list = Array.isArray(students) ? students : students ?? [];
    const match = list.find((s: any) => s.id === studentId);
    return match?.name ?? null;
  }, [students, (auth.user as any)?.student_id]);

  // -----------------------------
  // Display label on right side
  // -----------------------------
  let displayUser = roleLabel;
  if (isAdminLike) {
    const idLabel = auth.user?.id ? `#${auth.user.id}` : "";
    displayUser = [roleLabel, idLabel].filter(Boolean).join(" ");
  } else if (studentName) {
    displayUser = studentName;
  } else if (role === "student") {
    displayUser = "Student";
  }

  return (
    <header className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-16 flex items-center justify-between">
          {/* LEFT: brand + nav */}
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className="text-xl font-semibold text-slate-900 dark:text-white whitespace-nowrap"
            >
              SchoolFlow
            </Link>

            <nav className="flex items-center gap-4 md:gap-6 flex-wrap">
              {isAdminLike ? (
                <>
                  <Link
                    to="/invoices"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Invoices
                  </Link>
                  <Link
                    to="/receipts"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Receipts
                  </Link>
                  <Link
                    to="/fee-assignments"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Fee Assignments
                  </Link>
                  <Link
                    to="/class-sections"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Class Sections
                  </Link>
                  <Link
                    to="/students"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Students
                  </Link>
                  <Link
                    to="/fee-components"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Fee Components
                  </Link>
                  <Link
                    to="/fee-plans"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    Fee Plans
                  </Link>
                  <Link
                    to="/admin/csv"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    CSV Import
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/my/invoices"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    My Invoices
                  </Link>
                  <Link
                    to="/my/receipts"
                    className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
                  >
                    My Receipts
                  </Link>
                </>
              )}
              <Link
                to="/about"
                className="text-sm text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
              >
                About
              </Link>
            </nav>
          </div>

          {/* RIGHT: user + auth buttons */}
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300 whitespace-nowrap">
              {displayUser}
            </div>

            {auth.token ? (
              <button
                onClick={() => auth.logout()}
                className="text-sm text-red-600 hover:text-red-700 px-2 py-1"
              >
                Logout
              </button>
            ) : (
              <Link
                to="/login"
                className="text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
