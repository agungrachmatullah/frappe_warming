import frappe
from frappe.model.document import Document

TRANSITIONS = {
    "Draft": ["Pending Approval"],
    "Pending Approval": ["Approved", "Rejected"],
    "Approved": ["Ready"],
    "Rejected": [],
    "Ready": ["Closed"],
    "Closed": [],
}

IMMUTABLE_STATES = ("Approved", "Ready", "Closed")


class StorageAgreementRequest(Document):
    def validate(self):
        self._check_immutability()
        self._validate_line_items()

    def _check_immutability(self):
        # Cegah edit field apa pun (selain lewat _transition) kalau status sudah final
        if self.is_new() or self.flags.get("allow_transition"):
            return
        old_status = frappe.db.get_value(self.doctype, self.name, "status")
        if old_status in IMMUTABLE_STATES:
            frappe.throw(f"Dokumen berstatus '{old_status}' bersifat final dan tidak dapat diubah.")

    def _validate_line_items(self):
        for row in self.request_package_ids:
            if row.quantity is not None and row.quantity < 0:
                frappe.throw(f"Quantity tidak boleh negatif (baris {row.idx}).")

    # ---- Internal transition engine ----
    def _transition(self, new_state, reason=None):
        current = self.status
        allowed = TRANSITIONS.get(current, [])
        if new_state not in allowed:
            frappe.throw(
                f"Transisi dari '{current}' ke '{new_state}' tidak diizinkan.",
                frappe.ValidationError,
            )

        old_state = self.status
        self.flags.allow_transition = True
        self.status = new_state
        self.save()

        frappe.get_doc({
            "doctype": "Storage Agreement Log",
            "agreement": self.name,
            "from_state": old_state,
            "to_state": new_state,
            "action": new_state,
            "performed_by": frappe.session.user,
            "reason": reason or "",
        }).insert(ignore_permissions=True)
        frappe.db.commit()

    def _require_role(self, role):
        if role not in frappe.get_roles(frappe.session.user):
            frappe.throw("Anda tidak memiliki hak untuk aksi ini.", frappe.PermissionError)

    def _forbid_self_approval(self):
        # Separation of duties: pembuat dokumen tidak boleh approve/reject miliknya sendiri
        if self.owner == frappe.session.user:
            frappe.throw(
                "Anda tidak dapat menyetujui/menolak dokumen yang Anda buat sendiri.",
                frappe.PermissionError,
            )

    # ---- Aksi publik (dipanggil dari API/Client Script) ----
    def submit_for_approval(self):
        if not self.request_package_ids:
            frappe.throw("Tidak bisa diajukan approval tanpa Requested Package.")
        self._transition("Pending Approval")

    def approve(self, reason=None):
        self._require_role("Stock Manager")
        self._forbid_self_approval()
        if not self.request_package_ids:
            frappe.throw("Tidak bisa approve tanpa item.")
        self._transition("Approved", reason)

    def reject(self, reason=None):
        self._require_role("Stock Manager")
        self._forbid_self_approval()
        if not reason:
            frappe.throw("Alasan penolakan wajib diisi.")
        self._transition("Rejected", reason)

    def set_ready(self, reason=None):
        self._require_role("Stock Manager")
        self._transition("Ready", reason)

    def close(self, reason=None):
        self._require_role("Stock Manager")
        self._transition("Closed", reason)
