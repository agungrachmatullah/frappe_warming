import frappe
from frappe.utils import now_datetime, date_diff


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Document", "fieldname": "name", "fieldtype": "Link",
         "options": "Storage Agreement Request", "width": 150},
        {"label": "Partner", "fieldname": "partner_id", "fieldtype": "Link",
         "options": "Customer", "width": 180},
        {"label": "Created By", "fieldname": "created_by", "fieldtype": "Link",
         "options": "User", "width": 150},
        {"label": "Submitted On", "fieldname": "submitted_on", "fieldtype": "Datetime", "width": 160},
        {"label": "Age (days)", "fieldname": "age_days", "fieldtype": "Int", "width": 100},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    filters = filters or {}

    conditions = "status = 'Pending Approval'"
    values = {}

    if filters.get("partner_id"):
        conditions += " AND partner_id = %(partner_id)s"
        values["partner_id"] = filters["partner_id"]

    rows = frappe.db.sql(f"""
        SELECT name, partner_id, owner AS created_by, modified AS submitted_on, status
        FROM `tabStorage Agreement Request`
        WHERE {conditions}
        ORDER BY modified ASC
    """, values, as_dict=True)

    today = now_datetime()
    for row in rows:
        row["age_days"] = date_diff(today, row["submitted_on"])

    return rows