### Storage Operation

Storage Transaction Management

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app storage_ops
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/storage_ops
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

##################################################################

1. overview
nama apps : storage operation
aplikasi ini digunakan untuk membangun fitur pencatatan transaksi peminjaman gudang untuk penyimpanan barang, pada dokumen ini mencatat barang apa dan berapa, dari tanggal berapa sampai tanggal berapa. pembuatan dokumen bisa dilakukan oleh user dan manager stock, namun untuk melakukan validasi harus dilakukan oleh user dengan role stock manager, dan pembuat dokumen tidak boleh melakukan validasi ke dokumen yg dia buat sendiri.

2. design rationale:
1. reuse: customer, item
penggunaan customer dan item dari erpnext adalah utamanya untuk memanfaatkan fitur yg sudah terbuat, seperti field untuk menampung alamt, kontak, histori, selain itu menghindari adanya duplikasi data, apabila dipaksakan untuk membuat master data sendiri (misal customer), diwaktu yg akan datang ketika ada object lain yg menggunakan data customer, kemudian ada kebutuhan untuk melihat transaksi storage operation base on customer juga, maka data akan terpecah, akan ada lebih dari multiple effort untuk mensinkronkan data dalam pengelolaan fitur nya.
Request Package (child table) , agreement audit log (doctype mandiri)
jika dilihat dari kebutuhan dari pelaporan/query independen atau dari parent, misal kebutuhan dalam pelaporan barang apa saja yg akan dititipkan, maka dalam konteks Storage Agreement Request maka tidak bisa dipisahkan data antara header (Storage Agreement Request) dan detail (Request Package) dari dokumen tersebut, yakni item, qty dan sebagainya yg berasal dari child table dan header table nya.
Lalu untuk Log, kita buat jadi doctype mandiri karena alasan permission yg berbeda dari parent nya (readonly untuk semua role, termasuk yang boleh edit parent nya), pada child table tidak mendukung permission independen seperti ini, permission table selalu mengikut permission dari parent atau header nya. maka jika dilihat dari segi permission maka Log harus menjadi doctype mandiri

3. Workflow tidak digunakan karena WorkFlow doctype bawaan frappe didesign untuk mudah diatur melalui UI, sisi negatifnya ini akan merubah aturan yg sudah disusun berdasarkan requirement kebutuhan, dan rawan akan adanya conflict dengan fitur lain. Dalam tugas ini, requerement sudah menentukan alur transisi yg harus berjalan seperti apa, maka penggunaan workflow doctype membuat aturan transisi tidak benar-benar terkunci berbeda dengan doctype yang dibangun melalui logika yg sudah di review dan dideploy sebagai kode.

4. Permission selain sembunyikan field / tombol
permission yang kami terapkan ada 4 lapis, dan semuanya ada di bagian server side:
1. role permission (storage_agreement_request.json) > access right untuk role
2. _require_role() di controller - berjalan tiap sebelum eksekusi logic transisi status.
3. _forbid_self_approval() validasi ini adalah validasi yg tidak bisa di ekspersikan melalui role permission manager bawaan frappe, dengan logika membandingkan langsung antara self.owner dengan frappe.session.user
4. doc.check_permission()/frappe.has_permission() pada tiap endpoint rest api > memastikan semua request yang melalui endpoint selalu di cek
Kombinasi ini membuat sistem untuk bisa menerima action dari user baik melalui UI atau pun endpoint API dengan tetap mengikuti aturan bisnis dan kondisi otorisasi yang sudah ditetapkan.

5. jaminan audit trail untuk log
yang bisa dijamin : Permission DocType ini di-set write: 0, create: 0, delete: 0 , sehingga semua action baik dari UI atau endpoint melalui role apapun terhadap Log, tidak akan bisa dilakukan, jalur create edit dan delete hanya melalui insert(ignore_permissions=True) yang dipanggil dalam method _transistion() di controller.
yang tidak dijamin : perlindungan ini hanya ada di level aplikasi frappe, bukan pada level data base. siapapun yang memiliki akses ke database maka dia bisa melakukan update/delete langsung ke tabel log. data log juga tidak di replikasikan ke database lain, sehingga apabila ada perubahan data, maka tidak ada salinan independen untuk dilakukan verifikasi.
hardening : 
1. (level db) buat mariadb trigger (before update/before delete) pada tabel, yang menolak operasi kecuali dari hak akses tertentu.
2. replikasi setiap entri ke penyimpanan eksternal

6. code custom dibangun pada apps baru (storage_ops), diinstal sebagai apps yang berdiri sendiri diatas erpnext, tidak ada perubahan apapun pada app erpnext seara langsung. dependency ke erpnext jelas ditulis required_apps = ["erpnext"] di hooks.py, kustomisasi ui tersimpan dalam bentuk code secara konsisten sehingga ter track di version controll (git) bukan berupa customize-form yang tersimpan di database.

7. role & permission matrix
DocType > Storage Agreement Request & Request Package
-----------------------------------------------------------------------------
Role              | Read | Write | Create | Submit | Cancel | Delete
-----------------------------------------------------------------------------
Stock User        |  Y   |   Y   |   Y    |   N    |   N    |   N
Stock Manager      |  Y   |   Y   |   N    |   Y    |   Y    |   N
-----------------------------------------------------------------------------

DocType > Agreement Audit Log
-----------------------------------------------------------------------------
Role              | Read | Write | Create | Delete
-----------------------------------------------------------------------------
Stock User        |  Y   |   N   |   N    |   N
Stock Manager      |  Y   |   N   |   N    |   N
-----------------------------------------------------------------------------

Rule                          | Enforced By
-------------------------------------------
Stock User no submit access    | Role Permission
Approve requires Stock Manager  | Python code (_require_role)
Cannot approve own document      | Python code (_forbid_self_approval)
Cannot skip state (Draft->Ready)  | Python code (_transition/TRANSITIONS)
Audit log immutable                | Role Permission (write:0,create:0)

8. production-readiness note
yang terjadi ketika bench migrate adalah pembacaan ulang dan sinkronisasi dari perubahan yg ada di docType (Storage Agreement Request , Request Package, Agreement Audit Log), yang perlu diperhatikan disini adalah ketika perubahan json dimaksudkan untuk menghapus field, karena selain menghapus field maka data dari field itu juga akan ikut dihapus.
fixtures yang synced di apps ini hanya 1 yaitu Workspace yang di deklarasikan di hooks.py : entri menu sidebar dan shortcut ke DocType utama.
fixture cocok untuk data konfigurasi statis, sedangkan patch cocok setiap kali perubahan membutuhkan perubahan data transaksional yang sudah ada. misal jika di waktu mendatang ada rilis opsi field status diganti namanya, atau perlu isi ulang value (backfill) unit_price / discount_percent pada data Request Package yg dibuat sebelum kedua field itu ada. untuk kasus semacm itu maka harus pakai patch sekali-jalan (didaftarkan di patches.txt di pre_model_sync atau post_model_sync).
langkah backup sebelum deploy ke produksi dan rencana restore :
1. backup di production > bench --site <site> backup --with-files 
2. menerapkan perubahan di environment staging yg datanya menyerupai produksi, dan menjalankan migrate > bench --site <site> migrate
3. apabila migrate selesai dengan aman, maka lanjutkan ke production
apabila terjadi maslaah ketika deployment, maka yang dilakukan adalah hentikan site yg terdampak, lalu jalankan restore > bench --site <site> restore <file-backup>. restore merupakan langkah ter aman dan cepat untuk handling permasalahan ini, dibandingnkan dengan pemenahan data manual

