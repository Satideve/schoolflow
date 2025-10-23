# backend/ops/inspect_receipt.py
"""
Inspect a receipt's rendering context and produce an HTML preview.

Usage:
  - This file should be placed under backend/ops and your docker-compose already mounts ops into /app/backend/ops.
  - Run inside container with:
      PYTHONPATH=/app/backend python /app/backend/ops/inspect_receipt.py <receipt_id>
    (receipt_id defaults to 1 if not supplied)
"""

from pathlib import Path
import sys
import pprint

def main():
    try:
        rid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    except Exception:
        rid = 1

    # Lazy imports (avoid import-time side effects)
    from app.db.session import get_db
    from app.services.pdf.context_loader import load_receipt_context
    import jinja2

    db = next(get_db())
    try:
        ctx = load_receipt_context(rid, db)
    except Exception as e:
        print("ERROR: failed to load context for receipt id", rid)
        print("Exception:", repr(e))
        db.close()
        sys.exit(2)

    # Print a compact summary
    print("=== Context summary ===")
    print("receipt_id:", ctx.get("receipt_id"))
    print("receipt_no:", ctx.get("receipt_no"))
    print("amount:", repr(ctx.get("amount")))
    print("paid_amount:", repr(ctx.get("paid_amount")))
    items = ctx.get("items") or []
    print("items_count:", len(items))
    for i, it in enumerate(items[:10], start=1):
        # defensive: it may be object-like or dict-like
        try:
            iid = it.get("id") if isinstance(it, dict) else getattr(it, "id", None)
            desc = it.get("description") if isinstance(it, dict) else getattr(it, "description", None)
            amt = it.get("amount") if isinstance(it, dict) else getattr(it, "amount", None)
        except Exception:
            iid = getattr(it, "id", None)
            desc = getattr(it, "description", None)
            amt = getattr(it, "amount", None)
        print(f"  item {i}: id={iid} desc={desc} amount={amt}")

    payments = ctx.get("payments") or []
    print("payments_count:", len(payments))
    for p in payments[:6]:
        # show a small dict for each payment
        info = {
            "id": getattr(p, "id", None),
            "amount": getattr(p, "amount", None),
            "provider": getattr(p, "provider", None),
            "provider_txn_id": getattr(p, "provider_txn_id", None),
            "created_at": getattr(p, "created_at", None),
            "status": getattr(p, "status", None),
        }
        print("  payment:", info)

    print("invoice_present:", bool(ctx.get("invoice")))
    inv = ctx.get("invoice")
    if inv:
        print("  invoice.id:", getattr(inv, "id", None), "invoice_no:", getattr(inv, "invoice_no", None),
              "amount_due:", getattr(inv, "amount_due", None))

    # Render template to HTML
    tpl_path = Path("/app/backend/app/templates/receipts/receipt.html")
    if not tpl_path.exists():
        print("Template not found at", tpl_path)
        db.close()
        sys.exit(3)

    tpl_src = tpl_path.read_text(encoding="utf-8")
    env = jinja2.Environment(loader=jinja2.BaseLoader(), autoescape=False)
    template = env.from_string(tpl_src)

    rendered = template.render(**ctx)
    out = Path("/tmp/receipt_debug.html")
    out.write_text(rendered, encoding="utf-8")
    print("Wrote rendered HTML to", out)
    print("\n--- HTML excerpt (first 800 chars) ---\n")
    excerpt = rendered[:800].replace("\r", "")
    print(excerpt)
    print("\n--- end excerpt ---")

    db.close()

if __name__ == "__main__":
    main()
