import frappe


def _get_doc_with_permission(name):
    doc = frappe.get_doc("Storage Agreement Request", name)
    doc.check_permission("write")
    return doc


@frappe.whitelist()
def submit_for_approval(name):
    doc = _get_doc_with_permission(name)
    doc.submit_for_approval()
    return {"status": doc.status}


@frappe.whitelist()
def approve(name, reason=None):
    doc = _get_doc_with_permission(name)
    doc.approve(reason)
    return {"status": doc.status}


@frappe.whitelist()
def reject(name, reason=None):
    doc = _get_doc_with_permission(name)
    doc.reject(reason)
    return {"status": doc.status}


@frappe.whitelist()
def set_ready(name, reason=None):
    doc = _get_doc_with_permission(name)
    doc.set_ready(reason)
    return {"status": doc.status}


@frappe.whitelist()
def close(name, reason=None):
    doc = _get_doc_with_permission(name)
    doc.close(reason)
    return {"status": doc.status}

@frappe.whitelist()
def get_status_and_history(name):
    """
    Mengembalikan status terkini sebuah Storage Agreement Request beserta
    riwayat audit trail-nya (siapa, kapan, dari-ke status apa, alasan).

    Permission: read-level check eksplisit — user harus punya akses baca
    ke dokumen spesifik ini (menghormati Role Permission + User Permission
    Frappe, bukan sekadar cek role secara umum).
    """
    if not frappe.db.exists("Storage Agreement Request", name):
        frappe.throw("Dokumen tidak ditemukan.", frappe.DoesNotExistError)

    doc = frappe.get_doc("Storage Agreement Request", name)
    doc.check_permission("read")  # <- permission check eksplisit, WAJIB sesuai requirement

    history = frappe.get_list(
        "Storage Agreement Log",
        filters={"agreement": name},
        fields=["from_state", "to_state", "action", "performed_by", "reason", "creation"],
        order_by="creation asc",
    )

    return {
        "name": doc.name,
        "current_status": doc.status,
        "partner": doc.partner_id,
        "owner": doc.owner,
        "history": history,
    }