
# SchoolFlow – Admin / Accounts Help

This guide is for **school admins, clerks, and accountants** using **SchoolFlow** to manage school fees.

It covers:

- The **correct order** to set up and use the system  
- How to **import data using CSV files**  
- How to **manage data using the web interface**  
- How to **create invoices, record payments, and download PDFs**  
- How to **create portal accounts for students**



## 1. How SchoolFlow is Structured

Key concepts:

- **Class Sections**  
  Examples: `X-A (2025-2026)`, `X-B (2025-2026)`, `IX-A (2025-2026)`  

- **Students**  
  Each student has a **name**, **roll_number**, and belongs to a **class_section**.

- **Fee Components**  
  Individual fee heads such as:
  - `Tuition`
  - `Transport`
  - `Lab Fee`
  - `Sports`
  - `Picnic`

- **Fee Plans**  
  A plan is a bundle of fee components for a group of students.  
  Example: `Standard Plan 2025 (monthly)`.

- **Fee Plan Components**  
  The actual amounts for each component in a plan.  
  Example:  
  `Standard Plan 2025` → `Tuition 2200`, `Transport 700`, `Lab Fee 150`.

- **Fee Assignments**  
  Links a student to a fee plan.  
  Example: “Anjali Singh → Standard Plan 2025”.

- **Invoices**  
  Bills for a student for a given period (month/term).  
  Example: invoice `INV-22` for period `2025-12`.

- **Payments & Receipts**  
  A payment recorded against an invoice creates a **receipt** and **PDF**.

- **Portal Accounts**  
  Login accounts for students/parents so they can see **only their own** invoices and receipts.

---

## 2. Correct Order of Operations (Very Important)

To avoid relational errors, always follow this order when setting up data:

1. **Class Sections**
2. **Students**
3. **Fee Components**
4. **Fee Plans**
5. **Fee Plan Components** (amounts within each plan)
6. **Fee Assignments** (link students to plans)
7. **Invoices**
8. **Payments**
9. **Receipts**

> ✅ **Golden rule:**  
> Never create an **invoice** for a student until they have a **fee assignment**.  
> In short: **“No Assignment → No Invoice”**

You can bootstrap steps 1–6 using CSV imports, then manage everything via the web UI.

---

## 3. Logging In as Admin

1. Open the SchoolFlow URL (e.g. `http://localhost:5173/` or your cloud URL).
2. Click **Login**.
3. Enter your **admin email** and **password**.
4. Click **Login**.

After logging in as admin, you should see:

- An **Admin Dashboard** (with metrics for invoices and receipts).
- A navbar with admin links:
  - `Invoices`, `Receipts`
  - `Class Sections`, `Students`
  - `Fee Components`, `Fee Plans`, `Fee Assignments`
  - `CSV Import`
  - `About`

If you see a “Welcome, Student” view and only “My Invoices / My Receipts”, you are logged in as a **student**, not an admin.

---

## 4. Initial Data Setup with CSV Imports

For a new school year, the fastest path is:

1. Import **Class Sections**
2. Import **Students**
3. Import **Fee data** (`seed_fees`) which defines:
   - Plans
   - Components
   - Plan-component amounts
   - Student-plan assignments

You do all CSV imports from the **CSV Import** page.

### 4.1 Opening the CSV Import Page

1. Log in as admin.  
2. Click **CSV Import** in the navbar.  
3. You will see one or more upload sections for:
   - Class sections CSV  
   - Students CSV  
   - Fee / plan / assignments CSV (seed fees)

The exact labels may vary, but concept is the same.

---

## 5. Example CSV Files

Below are **example templates**. Adjust them to your school’s data.

> ⚠️ Column names are important.  
> They should match what the backend expects.

### 5.1 `class_sections.csv`

Each row is a class section.

```csv
name,academic_year
"X-A","2025-2026"
"X-B","2025-2026"
"IX-A","2025-2026"

5.2 students.csv

Each row is a student.

name,roll_number,class_section_name,academic_year
"Anjali Singh","1A-001","X-B","2025-2026"
"Rahul Sharma","1A-002","X-B","2025-2026"
"Ashok Sharma","1A-003","X-B","2025-2026"
"Prawal Narayan","1A-004","X-B","2025-2026"
"Narender","1A-005","IX-A","2025-2026"


name – student’s full name

roll_number – must be unique across all students

class_section_name – must match a row from class_sections.csv

academic_year – should match the section’s academic_year

✅ The database has a UNIQUE index on roll_number.
If you try to create or edit a student to have a duplicate roll number, the backend will reject it.

After import, check Students page:

Names, roll numbers, and sections should match your expectations.

5.3 seed_fees.csv (plans, components, assignments)

This CSV defines:

Fee components (e.g. Tuition, Transport)

Fee plans

Amounts per component per plan

Fee assignments linking students to plans

Example:

student_roll_number,plan_name,academic_year,frequency,component_name,component_amount
"1A-001","Standard Plan 2025","2025-2026","monthly","Tuition",2200
"1A-001","Standard Plan 2025","2025-2026","monthly","Transport",700
"1A-001","Standard Plan 2025","2025-2026","monthly","Lab Fee",150
"1A-002","Standard Plan 2025","2025-2026","monthly","Tuition",2200
"1A-002","Standard Plan 2025","2025-2026","monthly","Transport",700
"1A-002","Standard Plan 2025","2025-2026","monthly","Lab Fee",150


A typical importer will:

Ensure a Fee Plan "Standard Plan 2025" exists for 2025-2026 with frequency="monthly".

Ensure Fee Components (Tuition, Transport, Lab Fee) exist.

Create Fee Plan Components with the amounts given.

Look up the student by student_roll_number.

Create a Fee Assignment linking that student to the plan.

After import, verify:

Fee Components page – components exist

Fee Plans page – plan is created

Fee Plan Detail – plan has correct component amounts

Fee Assignments – students are linked to the right plan

6. Managing Data via the Web UI

Once the initial import is done, day-to-day work should happen through the web interface.

6.1 Class Sections

Go to Class Sections:

Create new sections (name + academic year)

Edit section names / academic year

Delete sections (only if nothing depends on them)

6.2 Students

Go to Students:

Add new students:

Name

Roll number

Class section

Edit existing students:

Name, roll number, class section

Delete students (only if not referenced by assignments/invoices)

There is also a Portal Account column that shows:

The linked portal login email, or

“Not linked” if there is no user account yet.

6.3 Fee Components

Go to Fee Components:

Add each fee head (Tuition, Transport, etc.)

Optionally add descriptions

Edit or delete components (careful if already used in plans)

6.4 Fee Plans & Plan Components

Go to Fee Plans.

Create a plan:

Name, e.g. Standard Plan 2025

Academic year, e.g. 2025-2026

Frequency, e.g. monthly, term

Click on a plan to open Fee Plan Detail.

For each component:

Select a fee component

Enter an amount

Save

You will see:

List of components with amounts (per plan)

Plan total (sum of all component amounts)

6.5 Fee Assignments (Student → Plan)

Go to Fee Assignments:

For each student, choose:

Student

Fee plan

Optionally:

Add concession (numeric discount)

Add a note

Without an assignment, invoices won’t know what to charge for that student.

✅ Always ensure every student who should be billed has a fee assignment before generating invoices.

7. Creating Invoices
7.1 Creating a New Invoice

Go to Invoices.

Click Create Invoice.

Fill in:

Student – select the student (current UI may use an ID dropdown or input)

Invoice No – your numbering scheme, e.g. INV-2025-0001

Period – e.g. 2025-12

Due Date – e.g. 2025-12-31

Optional extra amount (top-up on top of plan)

Optional custom line items (description + amount)

Submit.

Under the hood, the system:

Finds the student’s fee assignment.

Gets all plan components and their amounts.

Adds your custom line items.

Calculates:

items_total – sum of all components + custom items

total_due

paid_amount (initially 0)

balance

You can then:

View the invoice details

Download the invoice PDF

Record payments

7.2 Invoice Detail View

From Invoices, click an invoice.

You’ll see:

Invoice number and ID

Student name

Period & due date

Line items table:

Plan components

Extra items (e.g. Picnic)

Items total, total due, paid, balance

A Download/View PDF button

A Collect Payment button

Latest receipt info (once payments exist)

8. Recording Payments & Generating Receipts
8.1 Recording Payment

Open the invoice detail page.

Click Collect Payment.

Enter:

Paid amount

Provider (e.g. Cash, NEFT, UPI)

Optional note (e.g. transaction reference)

Submit.

The backend will:

Create a payment record.

Update paid amount and balance on the invoice.

Create a receipt.

Generate a receipt PDF.

8.2 Viewing Receipts

Go to Receipts:

See a list of all receipts

Columns typically include:

Receipt no

Invoice ID

Amount

Created date

Download link

Click Download to view the PDF.

Students (via portal login) see receipts in My Receipts.

9. Creating Portal Accounts for Students

Portal accounts allow students/parents to log in and see:

Only their own invoices

Only their own receipts

Status of payments and balances

9.1 Creating a Portal User from Students Page

Go to Students.

Find the student row.

Use Create Portal User action (e.g. a button in that row).

In the dialog:

Enter Portal email (login email shared with the student/parent)

Enter Initial password

Design details:

The inputs start empty (no auto-filled admin email/password).

Each student can be linked to at most one user account.

After successfully creating:

The Portal Account column shows the linked email.

Student/parent can log in at the Login page using this email/password.

Their dashboard shows only their invoices & receipts.

10. Session & Security Behavior

Frontend stores the token in memory only.

When you close the browser, the user is effectively logged out.

Clicking Logout in the navbar:

Clears the token

Returns to an unauthenticated state

Good practice for shared computers:

Always click Logout after finishing work.

Close the browser window.

11. Year-Start Checklist (Admin)

For each new academic year:

Class Sections

Create sections for the new year (e.g. X-B (2025-2026)).

Students

Import or add students.

Ensure unique roll numbers.

Fee Components

Define all fee heads.

Fee Plans

Create fee plans for the new year.

Fee Plan Components

Set amounts per component per plan.

Fee Assignments

Link each student to the appropriate plan.

Invoices

Generate invoices (monthly/term).

Payments & Receipts

Record collections and print/supply receipts.

Portal Accounts

For students who should use the portal, create portal users.

If a student’s portal view seems empty:

Check that:

They are linked to the correct student record (via student_id on the user).

They have fee assignments.

Invoices have been generated for them.

Once basic data is consistent, SchoolFlow should support a smooth, repeatable fee workflow for your school.
---
CRITICAL ACCOUNTING DEFINITIONS (LOCKED)

These definitions are **non-negotiable** and must be respected everywhere (DB, API, UI, PDFs):

| Concept | Meaning |
|------|-------|
| **Base Amount** | A flat amount manually added by the school (NOT derived from fee plan) |
| **Base Amount Description** | Human explanation shown to parents |
| **Items** | Fee plan components + admin line items |
| **Items Total** | Sum of all items (including negative concession) |
| **Concession** | Discount applied once, represented as a negative item |
| **Total Due** | `base_amount + items_total` |
| **Paid Amount** | Sum of all payments |
| **Balance** | `total_due - paid_amount` |
---------------------------------------
