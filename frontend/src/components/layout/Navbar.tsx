// C:\coding_projects\dev\schoolflow\frontend\src\components\layout\Navbar.tsx
import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../store/auth";
import { useStudents } from "../../api/queries";

export default function Navbar() {
  const auth = useAuth();
  const user = auth.user;
  const role: string | undefined = user?.role;

  const isAdminLike =
    role === "admin" || role === "clerk" || role === "accountant";

  const roleLabel = role
    ? role.charAt(0).toUpperCase() + role.slice(1)
    : "User";

  // Load all students (React Query cache is shared; this will be fast after first load)
  const { data: studentsData } = useStudents();
  const students = Array.isArray(studentsData)
    ? studentsData
    : studentsData ?? [];

  /**
   * Try to compute a human-friendly display name for the current user.
   *
   * For students:
   *   - Prefer looking up the Student row by user.student_id (linked in DB)
   *   - Fallback: any student whose name matches, or just "Student"
   * For admins:
   *   - Show email
   */
  const displayStudentName = useMemo(() => {
    if (!user || role !== "student") return undefined;

    const studentId = (user as any).student_id as number | undefined;
    if (studentId && students.length > 0) {
      const match = students.find((s: any) => s.id === studentId);
      if (match?.name) return match.name as string;
    }

    // Fallbacks if mapping is weird:
    // - Try a `student_name` field if backend ever sends it
    if ((user as any).student_name) {
      return (user as any).student_name as string;
    }
    // - Try a generic `name`
    if ((user as any).name) {
      return (user as any).name as string;
    }

    return undefined;
  }, [user, role, students]);

  // Primary label:
  // - For students: prefer displayStudentName; fallback to email
  // - For admins: prefer email; fallback to role
  const primaryLabel =
    displayStudentName || user?.email || roleLabel;

  // Secondary label: Role + #id for all authenticated users
  const secondaryLabel =
    user && roleLabel
      ? `${roleLabel}${user.id ? ` #${user.id}` : ""}`
      : "";

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

          {/* RIGHT: user info + auth actions */}
          <div className="flex items-center gap-4">
            {auth.token ? (
              <>
                <div className="flex flex-col items-end text-right">
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {primaryLabel}
                  </span>
                  {secondaryLabel && (
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {secondaryLabel}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => auth.logout()}
                  className="text-sm text-red-600 hover:text-red-700 px-2 py-1"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="text-sm text-slate-700 hover:text-slate-900 px-2 py-1 border border-slate-300 rounded-md"
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
