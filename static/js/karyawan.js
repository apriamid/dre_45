/* ================================
   MODULE: KARYAWAN (FIXED)
   ================================ */

function loadUI_karyawan() {

  // ==== FORM KARYAWAN ====
  if (!$$("win_karyawan")) {
    webix.ui({
      view: "window", id: "win_karyawan", width: 600, position: "center", modal: true,
      head: "Form Karyawan",
      body: {
        view: "form", id: "form_karyawan",
        elements: [
          { view: "text", name: "_id", hidden: true },
          { view: "text", name: "nama", label: "Nama" },
          {
            view: "richselect", name: "jabatan", label: "Jabatan",
            options: [{ id: "Admin", value: "Admin" }, { id: "Kasir", value: "Kasir" }],
            required: true
          },
          { view: "text", name: "gaji", label: "Gaji" },
          { view: "text", name: "username", label: "Username (Login)" },
          { view: "text", type: "password", name: "password", label: "Password (Login)" },
          {
            margin: 10, cols: [
              {
                view: "button", value: "Simpan", css: "webix_primary", click: function () {
                  var form = $$("form_karyawan");
                  var data = form.getValues();

                  if (!data.nama || !data.username || !data.password || !data.jabatan) {
                    webix.message({ type: "error", text: "Lengkapi data karyawan" });
                    return;
                  }

                  // sanitize
                  for (let k in data)
                    if (typeof data[k] === "string")
                      data[k] = data[k].replace(/<[^>]*>?/gm, '').trim();

                  if (data._id) {
                    var id = data._id;
                    delete data._id;

                    webix.ajax()
                      .headers({ "Content-Type": "application/json" })
                      .put("/api/karyawan/" + id, JSON.stringify(data))
                      .then(function () {
                        $$("table_karyawan").clearAll();
                        $$("table_karyawan").load("/api/karyawan");
                        $$("win_karyawan").hide();
                        webix.message("Karyawan berhasil diperbarui");
                      })
                      .catch(function () {
                        webix.message({ type: "error", text: "Gagal update" });
                      });

                  } else {
                    webix.ajax()
                      .headers({ "Content-Type": "application/json" })
                      .post("/api/karyawan", JSON.stringify(data))
                      .then(function () {
                        $$("table_karyawan").clearAll();
                        $$("table_karyawan").load("/api/karyawan");
                        $$("win_karyawan").hide();
                        webix.message("Karyawan berhasil ditambahkan");
                      })
                      .catch(function () {
                        webix.message({ type: "error", text: "Gagal simpan" });
                      });
                  }
                }
              },
              {
                view: "button", value: "Batal",
                click: function () { $$("win_karyawan").hide(); }
              }
            ]
          }
        ]
      }
    });
  }

  // ==== DATATABLE KARYAWAN ====
  $$("mainContent").addView({
    id: "karyawan",
    batch: "karyawan",
    rows: [
      {
        view: "toolbar", css: "webix_dark",
        cols: [
          { view: "label", label: "KARYAWAN", align: "center" }, {},
          {
            view: "button", value: "Tambah", css: "webix_primary", width: 100,
            click: function () {
              $$("form_karyawan").clear();
              $$("win_karyawan").show();
            }
          }
        ]
      },
      {
        view: "datatable",
        id: "table_karyawan",
        url: "/api/karyawan",
        select: "row",
        columns: [
          { id: "_id", header: "ID", width: 100 },
          { id: "nama", header: "Nama", fillspace: true },
          { id: "jabatan", header: "Jabatan", width: 150 },
          {
            id: "gaji", header: "Gaji", width: 120,
            template: function (obj) {
              return obj.gaji ? new Intl.NumberFormat('id-ID').format(obj.gaji) : 0;
            }
          },
          {
            id: "status_aktif", header: "Status", width: 100,
            template: function (obj) { return obj.status_aktif ? "Aktif" : "Nonaktif"; }
          },
          {
            id: "tanggal_dibuat", header: "Dibuat", width: 160,
            template: function (obj) {
              return obj.tanggal_dibuat ? new Date(obj.tanggal_dibuat).toLocaleString() : "";
            }
          },
          {
            id: "aksi", header: "Aksi", width: 100,
            template:
              "<span class='editBtn' style='cursor:pointer;margin-right:8px;color:#1E88E5'><i class='fa fa-edit'></i></span>" +
              "<span class='deleteBtn' style='cursor:pointer;color:#E53935'><i class='fa fa-trash'></i></span>"
          }
        ],
        onClick: {
          "editBtn": function (e, id) {
            var item = this.getItem(id);
            $$("form_karyawan").setValues(item);
            $$("win_karyawan").show();
          },
          "deleteBtn": function (e, id) {
            var item = this.getItem(id);
            webix.confirm("Hapus karyawan ini?")
              .then(function () {
                webix.ajax()
                  .del("/api/karyawan/" + item._id)
                  .then(function () {
                    $$("table_karyawan").remove(id);
                    webix.message("Karyawan dihapus");
                  });
              });
          }
        }
      }
    ]
  });
}
