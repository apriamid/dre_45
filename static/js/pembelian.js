/* ================================
   MODULE: PRODUK (FIXED)
   ================================ */

function loadUI_produk() {

  // ==== FORM PRODUK ====
  if (!$$("win_produk")) {
    webix.ui({
      view:"window", id:"win_produk", width:600, position:"center", modal:true,
      head:"Form Produk",
      body:{
        view:"form", id:"form_produk",
        elements:[
          { view:"text", name:"_id", hidden:true },
          { view:"text", name:"nama_produk", label:"Nama Produk" },
          { view:"text", name:"kategori", label:"Kategori" },
          { view:"text", name:"stok", label:"Stok" },
          { view:"text", name:"harga", label:"Harga" },
          
          { margin:10, cols:[
            { view:"button", value:"Simpan", css:"webix_primary", click:function(){
              var form = $$("form_produk");
              var data = form.getValues();

              // sanitize input
              for (let k in data)
                if (typeof data[k] === "string")
                  data[k] = data[k].replace(/<[^>]*>?/gm, '').trim();

              if (!data.nama_produk || !data.kategori || !data.stok || !data.harga){
                webix.message({type:"error", text:"Lengkapi data produk"});
                return;
              }

              if(data._id){
                var id = data._id;
                delete data._id;
                webix.ajax()
                  .headers({"Content-Type":"application/json"})
                  .put("/api/produk/"+id, JSON.stringify(data))
                  .then(function(){
                    $$("table_produk").clearAll();
                    $$("table_produk").load("/api/produk");
                    $$("win_produk").hide();
                    webix.message("Produk diperbarui!");
                  })
                  .catch(function(){ webix.message({type:"error", text:"Gagal update"}); });
              } 
              else {
                webix.ajax()
                  .headers({"Content-Type":"application/json"})
                  .post("/api/produk", JSON.stringify(data))
                  .then(function(){
                    $$("table_produk").clearAll();
                    $$("table_produk").load("/api/produk");
                    $$("win_produk").hide();
                    webix.message("Produk disimpan!");
                  })
                  .catch(function(){ webix.message({type:"error", text:"Gagal simpan"}); });
              }
            }},
            { view:"button", value:"Batal", click:function(){ $$("win_produk").hide(); } }
          ]}
        ]
      }
    });
  }

  // ==== DATATABLE PRODUK ====
  $$("mainContent").addView({
    id:"produk",
    batch:"produk",
    rows:[
      { view:"toolbar", css:"webix_dark", cols:[
        { view:"label", label:"PRODUK", align:"center" },{},
        { view:"button", value:"Tambah", css:"webix_primary", width:100, click:function(){
            $$("form_produk").clear();
            $$("win_produk").show();
        }}
      ]},

      {
        view:"datatable",
        id:"table_produk",
        url:"/api/produk",
        select:"row",
        columns:[
          {id:"id",header:"Kode Produk",width:120},
          { id:"nama_produk", header:"Nama Produk", fillspace:true },
          { id:"kategori", header:"Kategori", width:150 },
          { id:"stok", header:"Stok", width:80 },
          { id:"harga", header:"Harga", width:120, 
            template:function(obj){
              return obj.harga ? new Intl.NumberFormat('id-ID').format(obj.harga) : 0;
            }
          },
          { id:"aksi", header:"Aksi", width:100,
            template:
              "<span class='editBtn' style='cursor:pointer;margin-right:8px;color:#1E88E5'><i class='fa fa-edit'></i></span>" +
              "<span class='deleteBtn' style='cursor:pointer;color:#E53935'><i class='fa fa-trash'></i></span>"
          }
        ],

        onClick:{
          "editBtn": function(e,id){
            var item = this.getItem(id);
            $$("form_produk").setValues(item);
            $$("win_produk").show();
          },
          "deleteBtn": function(e,id){
            var item = this.getItem(id);
            webix.confirm("Hapus produk ini?").then(function(){
              webix.ajax().del("/api/produk/"+item._id).then(function(){
                $$("table_produk").remove(id);
                webix.message("Produk dihapus!");
              }).catch(function(){
                webix.message({ type:"error", text:"Gagal hapus" });
              });
            });
          }
        }
      }
    ]
  });
}
