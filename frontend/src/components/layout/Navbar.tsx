// C:\coding_projects\dev\schoolflow\frontend\src\components\layout\Navbar.tsx
import React, { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../store/auth";
import { useStudents } from "../../api/queries";
import { useState } from "react";

export default function Navbar() {
  const auth = useAuth();
  const user = auth.user;
  const role: string | undefined = user?.role;
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isAdminLike =
  role === "admin" || role === "clerk" || role === "accountant";

  const isLoginPage =
    location.pathname === "/login" || location.pathname === "/register";

  // If user is NOT logged in → show only SchoolFlow + Login + Register
  if (!auth.token && isLoginPage) {
    return (
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 h-16 flex items-center justify-between">
          {/* LEFT */}
          <Link
            to="/"
            className="text-xl font-semibold text-slate-900 whitespace-nowrap"
          >
            SchoolFlow
          </Link>

          {/* RIGHT */}
          <div className="flex items-center gap-4">
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
          </div>
        </div>
        {/* 🔽 MOBILE MENU GOES HERE */}
      </header>        
      
    );
  }

  /* ----------------------------------------------------------
     NORMAL NAVBAR (user is logged in)
  ----------------------------------------------------------- */


  const { data: studentsData } = useStudents();
  const students = Array.isArray(studentsData)
    ? studentsData
    : studentsData ?? [];

  // Student display name resolution
  const displayStudentName = useMemo(() => {
    if (!user || role !== "student") return undefined;

    const studentId = (user as any).student_id as number | undefined;
    if (studentId && students.length > 0) {
      const match = students.find((s: any) => s.id === studentId);
      if (match?.name) return match.name;
    }

    return undefined;
  }, [user, role, students]);

  const primaryLabel =
    displayStudentName || user?.email || role?.toUpperCase();

  return (
    <header className="bg-white shadow">
      <div className="mx-auto max-w-7xl px-4 h-16 flex items-center justify-between">
        {/* LEFT SIDE */}
        <div className="flex items-center gap-6 min-w-0">
          <Link
            to="/"
            className="text-xl font-semibold text-slate-900 whitespace-nowrap"
          >
            SchoolFlow
          </Link>

          {/* NAV LINKS */}
          <nav className="hidden sm:flex items-center gap-6">
            {isAdminLike ? (
              <>
                <Link to="/invoices" className="text-sm text-slate-700 hover:text-black">
                  Invoices
                </Link>
                <Link to="/receipts" className="text-sm text-slate-700 hover:text-black">
                  Receipts
                </Link>
                <Link to="/fee-assignments" className="text-sm text-slate-700 hover:text-black">
                  Fee Assignments
                </Link>
                <Link to="/class-sections" className="text-sm text-slate-700 hover:text-black">
                  Class Sections
                </Link>
                <Link to="/students" className="text-sm text-slate-700 hover:text-black">
                  Students
                </Link>
                <Link to="/fee-components" className="text-sm text-slate-700 hover:text-black">
                  Fee Components
                </Link>
                <Link to="/fee-plans" className="text-sm text-slate-700 hover:text-black">
                  Fee Plans
                </Link>
                <Link to="/admin/csv" className="text-sm text-slate-700 hover:text-black">
                  CSV Import
                </Link>
                <Link
                  to="/help/admin"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 whitespace-nowrap transition"
                >
                  Help
                </Link>
              </>
            ) : (
              <>
                <Link to="/my/invoices" className="text-sm text-slate-700 hover:text-black">
                  My Invoices
                </Link>
                <Link to="/my/receipts" className="text-sm text-slate-700 hover:text-black">
                  My Receipts
                </Link>
                <Link
                  to="/help/student"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 whitespace-nowrap transition"
                >
                  Help
                </Link>
              </>
            )}

            <Link to="/about" className="text-sm text-slate-700 hover:text-black">
              About
            </Link>
          </nav>
        </div>

        {/* RIGHT SIDE */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="flex flex-col text-right">
            <span className="text-sm font-medium text-slate-800">
              {primaryLabel}
            </span>
            <span className="text-xs text-slate-500">
              {role?.toUpperCase()} #{user?.id}
            </span>
          </div>

          {/* HAMBURGER — MOBILE ONLY */}
          <button
            type="button"
            onClick={() => setMobileOpen(v => !v)}
            className="sm:hidden inline-flex items-center justify-center p-2 rounded-md text-slate-700 hover:bg-slate-100"
            aria-label="Toggle navigation"
          >
            {mobileOpen ? "✕" : "☰"}            
          </button>

          <button
            onClick={() => auth.logout()}
            className="text-sm text-red-600 hover:text-red-700 px-2 py-1"
          >
            Logout
          </button>
        </div>

      </div>
      {/* MOBILE MENU (mobile only) */}
      {mobileOpen && (
        <>
          {/* BACKDROP */}
          <div
            className="sm:hidden fixed inset-0 bg-black/20 z-40"
            onClick={() => setMobileOpen(false)}
          />

          {/* MENU PANEL */}
          <div className="sm:hidden relative z-50 border-t bg-white shadow">
            <nav className="px-4 py-3 flex flex-col gap-3">
              {isAdminLike ? (
                <>
                  <Link to="/invoices" onClick={() => setMobileOpen(false)}>Invoices</Link>
                  <Link to="/receipts" onClick={() => setMobileOpen(false)}>Receipts</Link>
                  <Link to="/fee-assignments" onClick={() => setMobileOpen(false)}>Fee Assignments</Link>
                  <Link to="/class-sections" onClick={() => setMobileOpen(false)}>Class Sections</Link>
                  <Link to="/students" onClick={() => setMobileOpen(false)}>Students</Link>
                  <Link to="/fee-components" onClick={() => setMobileOpen(false)}>Fee Components</Link>
                  <Link to="/fee-plans" onClick={() => setMobileOpen(false)}>Fee Plans</Link>
                  <Link to="/admin/csv" onClick={() => setMobileOpen(false)}>CSV Import</Link>
                  <Link to="/help/admin" onClick={() => setMobileOpen(false)}>Help</Link>
                </>
              ) : (
                <>
                  <Link to="/my/invoices" onClick={() => setMobileOpen(false)}>My Invoices</Link>
                  <Link to="/my/receipts" onClick={() => setMobileOpen(false)}>My Receipts</Link>
                  <Link to="/help/student" onClick={() => setMobileOpen(false)}>Help</Link>
                </>
              )}

              <Link to="/about" onClick={() => setMobileOpen(false)}>About</Link>
            </nav>
          </div>
        </>
      )}

    </header>
  );
}
