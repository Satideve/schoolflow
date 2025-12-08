# SchoolFlow – End-to-End Test Scenario (Fresh DB)

This guide shows how to:

1. Reset the **test DB** to empty.
2. Load **master data via CSV Import** (Class Sections + Students).
3. Populate remaining tables via **frontend UI**.
4. Walk through an **end-to-end test**: plan → assignment → invoice → payment → receipt.

You can copy this whole file as `TEST_PLAN.md` if you like.

---

## 1. Reset the Database

> ⚠️ This **deletes all data** from `schoolflow_test_run`.

From `infra/` directory:

```bash
# 1. Open a psql shell (optional – just to double-check DB name)
docker compose exec db psql -U admin -d schoolflow_test_run

# 2. In psql, TRUNCATE all app tables (or run as a single -c command)
TRUNCATE TABLE
  fee_invoice_item,
  receipt,
  payment,
  fee_invoice,
  fee_assignment,
  fee_plan_component,
  fee_plan,
  fee_component,
  students,
  class_sections,
  "user"
RESTART IDENTITY CASCADE;

\q
You can also do in one line from your host:

bash
Copy code
docker compose exec db psql -U admin -d schoolflow_test_run -c \
"TRUNCATE TABLE fee_invoice_item, receipt, payment, fee_invoice, fee_assignment, fee_plan_component, fee_plan, fee_component, students, class_sections, \"user\" RESTART IDENTITY CASCADE;"
Now the DB is clean and all IDs will start from 1 again.

2. Prepare Master Data CSV Files
Create a folder (e.g. test_data/) and create the following CSV files.

2.1 class_sections.csv
csv
Copy code
name,academic_year
IX-A,2025
IX-B,2025
X-A,2025
X-B,2025
2.2 students.csv
Assumption: CSV import for students uses class_section_id (the numeric FK).
After truncation + import, class sections will get IDs 1,2,3,4 in the order above.

csv
Copy code
name,roll_number,class_section_id
Aarav Kumar,1,1
Diya Sharma,2,1
Vihaan Patel,1,2
Ananya Iyer,2,2
Rohan Singh,1,3
Sara Nair,2,3
If your CSV import expects slightly different headers
(e.g. class_section_name instead of class_section_id), adjust the header row
to match the error message from the backend.

3. Import Master Data via Frontend (CSV Import Page)
Start backend + frontend (if not already running):

bash
Copy code
# from infra/
docker compose up

# in another terminal, from frontend/
pnpm dev
Log in as admin in the frontend.

Click CSV Import in the navbar.

Import class sections:

In the Class Sections import block:

Choose file: class_sections.csv

Click Upload / Import.

Verify in Class Sections page:

Navbar → Class Sections

You should see: IX-A, IX-B, X-A, X-B with IDs 1–4.

Import students:

In the Students import block:

Choose file: students.csv

Click Upload / Import.

Verify in Students page:

Navbar → Students

Students should appear with correct class sections.

At this point these tables are populated:

class_sections

students

4. Populate Fee Master Data via UI
4.1 Create Fee Components
Navbar → Fee Components.

In Add Fee Component form, create these:

Name	Description
Tuition	Tuition fee
Transport	Transport fee
Lab Fee	Laboratory charges

Verify they appear in the table with IDs 1, 2, 3.

This populates fee_component.

4.2 Create a Fee Plan
Navbar → Fee Plans.

Under Add Fee Plan, create:

Name: Standard-IX-2025

Academic year: 2025

Frequency: monthly

Click Create.

In Existing Plans, you should see the new plan (ID 1).
Click the plan name to open Fee Plan Detail.

This populates fee_plan.

4.3 Add Components to the Plan (Fee Plan Components)
In the Fee Plan Detail page for Standard-IX-2025:

In Add Component block:

Add Tuition (component ID 1) with amount 2200.

Add Transport (component ID 2) with amount 700.

Add Lab Fee (component ID 3) with amount 150.

Verify in the Components table:

ID	Component	Description	Amount
1	Tuition	Tuition	2200
2	Transport	Transport	700
3	Lab Fee	Lab Fee	150

The Total at the top should show ₹3,050.00 (2200 + 700 + 150).

This populates fee_plan_component.

5. Assign Students to Fee Plan
Navbar → Fee Assignments.

Use the form to create an assignment for each student that should follow this plan.
For end-to-end testing, assign at least Student #1.

Example (for first student):

Student: the drop-down entry with Aarav Kumar (id 1).

Fee plan: Standard-IX-2025.

Concession: leave empty or 0.

Note: Test assignment.

Save. Verify in the table that assignment(s) exist:

ID	Student	Plan	Concession	Note
1	Aarav Kumar	Standard-IX-2025	0	Test assignment

This populates fee_assignment.

6. Create an Invoice (Admin UI)
Navbar → Invoices.

Click Create Invoice (or equivalent button for new invoice).

In Create Invoice form:

Invoice No: INV-TEST-001

Student ID: 1 (Aarav)

Period: 2025-12

Due Date: 2025-12-31

Base Amount (optional):
e.g. 500 (extra manual charge) – or leave blank if you only want plan-derived + line items.

Line Items (optional but good to test):

Click + Add Item

Description: Late fee

Amount: 100

Click + Add Item again

Description: Misc. charges

Amount: 50

Verify the summary:

Base amount (if you entered 500): ₹500.00

Line items total: ₹150.00

Final invoice amount: ₹650.00 (for these extra items).
The backend will also add the plan total (3050) if configured that way, so
total due in the invoice may be 3050 + 650 = 3700.

Click Create.

Expected:

A toast in console: Invoice created.

You are redirected to the Invoice Detail page for invoice ID (e.g. 1).

This populates:

fee_invoice

fee_invoice_item (for the extra line items you entered).

7. Verify Invoice Details + PDF
On Invoice Detail page:

Confirm header:

Correct invoice_no (INV-TEST-001)

Student: Aarav Kumar

Period 2025-12, Due 2025-12-31

In Line Items section you should see:

Items from the fee plan (Tuition / Transport / Lab Fee) if the backend includes them in the items list.

Extra items from the Create Invoice form:

Late fee – ₹100.00

Misc. charges – ₹50.00

Totals:

Items total should match the sum of all displayed items.

Total due should show the computed due amount.

Paid should be ₹0.00.

Balance should equal Total due.

Click Download PDF / View PDF:

Verify the PDF shows:

Student

All line items

Correct totals.

8. Collect Payment (Generate Receipt)
From the Invoice Detail page (as admin):

Click Collect Payment button.

In PaymentDialog:

Amount: set to the full outstanding balance (shown on page).

Provider: manual (or any allowed option).

Note: Full payment – test.

Submit.

Expected:

Toast (in console logs): "Payment recorded: Invoice and receipts refreshed."

The invoice detail page updates:

Paid becomes equal to Total due.

Balance becomes ₹0.00.

A Latest receipt panel appears with:

Receipt number (e.g. REC-XXXX).

Amount (same as payment).

Created at timestamp.

Download link.

This populates:

payment

receipt

Invoice totals (paid/balance) updated in fee_invoice.

9. Verify Receipts List + Receipt PDF
Navbar → Receipts.

You should see at least one row:

ID	Receipt No	Invoice ID	Student	Amount	Created At	Actions
1	REC-…	1	Aarav Kumar	₹…	…	Download

Click Download:

Receipt PDF should show:

Student

Invoice number

Paid amount

Line items matching the invoice (per your backend logic).

10. Quick Regression Checklist
With the same data, verify:

Class Sections

List + create/edit/delete operations (where implemented).

Students

List + create/edit/delete.

Fee Components

List + create.

Fee Plans

List + create, navigate to Fee Plan Detail.

Fee Plan Detail

Add / edit / delete plan components.

Total updates correctly.

Fee Assignments

Create assignment for another student (e.g. student #2).

Invoices

List all invoices (admin view).

Create a second invoice for a different period or student.

Invoice Detail

Edit line items via specialized UI if/when implemented.

Receipts

List shows all receipts.

Download links work.

You can now iterate on this script any time:

Truncate tables;

Re-import class_sections.csv and students.csv;

Recreate fee components, fee plan, assignments, invoice, payment.

That gives you a repeatable end-to-end test of both frontend UI and backend DB.