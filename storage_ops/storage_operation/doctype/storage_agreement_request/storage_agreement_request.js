frappe.ui.form.on("Storage Agreement Request", {
    refresh: function (frm) {
        if (frm.doc.status === "Draft") {
            frm.add_custom_button("Submit for Approval", () => {
                frappe.call({
                    method: "storage_ops.api.submit_for_approval",
                    args: { name: frm.doc.name },
                    callback: () => frm.reload_doc(),
                });
            });
        }
        if (frm.doc.status === "Pending Approval") {
            frm.add_custom_button("Approve", () => {
                frappe.call({
                    method: "storage_ops.api.approve",
                    args: { name: frm.doc.name },
                    callback: () => frm.reload_doc(),
                });
            });
            frm.add_custom_button("Reject", () => {
                frappe.prompt("Alasan penolakan", (values) => {
                    frappe.call({
                        method: "storage_ops.api.reject",
                        args: { name: frm.doc.name, reason: values.reason },
                        callback: () => frm.reload_doc(),
                    });
                }, "Reject Request");
            });
        }
        if (frm.doc.status === "Approved") {
            frm.add_custom_button("Set Ready", () => {
                frappe.call({
                    method: "storage_ops.api.set_ready",
                    args: { name: frm.doc.name },
                    callback: () => frm.reload_doc(),
                });
            });
        }
        if (frm.doc.status === "Ready") {
            frm.add_custom_button("Close", () => {
                frappe.call({
                    method: "storage_ops.api.close",
                    args: { name: frm.doc.name },
                    callback: () => frm.reload_doc(),
                });
            });
        }
    },
});