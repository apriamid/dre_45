/* ================================
   MODULE: SHIFT
   ================================ */

function loadUI_shift() {

  function hitungDurasi(jamMulai, jamSelesai){
    if(!jamMulai || !jamSelesai) return "";
    try{
      const [h1,m1] = jamMulai.split(":").map(Number);
      const [h2,m2] = jamSelesai.split(":").map(Number);
      let total = (h2*60+m2) - (h1*60+m1);
      if(total < 0) total += 24*60;
      return (total/60).toFixed(2);
    }catch(e){ return ""; }
  }

  /* ==== WINDOW MASTER SHIFT ==== */
  if(!$$("win_master_shift")){
    webix.ui({
      view:"window", id:"win_master_shift", width:600, position:"center", modal:true,
      head:"Form Master Shift",
      body:{
        view:"form", id:"form_master_shift",
        elements:[
          { view:"text", name:"_id", hidden:true },
          { view:"text", name:"nama_shift", label:"Nama Shift" },
          { view:"text", name:"jam_mulai", label:"Jam Mulai", placeholder:"HH:MM" },
          { view:"text", name:"jam_selesai", label:"Jam Selesai", placeholder:"HH:MM" },
          { view:"text", name:"durasi_jam", label:"Durasi (Jam)", readonly:true },
          { view:"checkbox", name:"status_aktif", labelRight:"Aktif", value:true },

          { cols:[
            { view:"button", value:"Simpan", css:"webix_primary", click:function(){

              var data = $$("form_master_shift").getValues();
              if(!data.nama_shift || !data.jam_mulai || !data.jam_selesai){
                webix.message({type:"error", text:"Lengkapi fields"});
                return;
              }

              data.durasi_jam = hitungDurasi(data.jam_mulai, data.jam_selesai) || 0;

              if(data._id){
                let id=data._id; delete data._id;
                webix.ajax().headers({"Content-Type":"application/json"})
                  .put("/api/shift/"+id, JSON.stringify(data))
                  .then(()=>{
                    $$("table_shift_combined").clearAll();
                    $$("table_shift_combined").load("/api/shift/all");
                    $$("win_master_shift").hide();
                    webix.message("Shift diperbarui!");
                  });
              }
              else {
                webix.ajax().headers({"Content-Type":"application/json"})
                  .post("/api/shift", JSON.stringify(data))
                  .then(()=>{
                    $$("table_shift_combined").clearAll();
                    $$("table_shift_combined").load("/api/shift/all");
                    $$("win_master_shift").hide();
                    webix.message("Shift ditambahkan!");
                  });
              }
            }},
            { view:"button", value:"Batal", click:function(){ $$("win_master_shift").hide(); } }
          ]}
        ]
      }
    });

    $$("form_master_shift").attachEvent("onChange", function(name,value){
      try{
        var vals = $$("form_master_shift").getValues();
        var d = hitungDurasi(vals.jam_mulai, vals.jam_selesai);
        $$("form_master_shift").setValues({ durasi_jam: d }, true);
      }catch(e){}
    });
  }

  /* ==== WINDOW OPEN SHIFT ==== */
  if(!$$("win_open_shift")){
    webix.ui({
      view:"window", id:"win_open_shift", width:480, position:"center", modal:true,
      head:"Open Shift (Admin)",
      body:{
        view:"form", id:"form_open_shift",
        elements:[
          { view:"text", name:"id_karyawan", label:"ID Karyawan" },
          { view:"text", name:"nama_kasir", label:"Nama Kasir" },
          { view:"richselect", name:"id_shift", label:"Pilih Shift", options:"/api/shift" },
          { view:"text", name:"open_cash", label:"Saldo Awal (Cash)", value:0 },
          { cols:[
            { view:"button", value:"Buka Shift", css:"webix_primary", click:function(){
              var d = $$("form_open_shift").getValues();
              if(!d.id_karyawan || !d.id_shift){
                webix.message({type:"error", text:"Lengkapi data"});
                return;
              }
              webix.ajax().headers({"Content-Type":"application/json"})
              .post("/api/shift/open", JSON.stringify({
                id_karyawan: d.id_karyawan,
                nama_kasir: d.nama_kasir,
                id_shift: d.id_shift,
                open_cash: parseInt(d.open_cash||0)
              })).then(()=>{
                $$("table_shift_combined").clearAll();
                $$("table_shift_combined").load("/api/shift/all");
                $$("win_open_shift").hide();
                webix.message("Shift dibuka!");
              });
            }},
            { view:"button", value:"Batal", click:function(){ $$("win_open_shift").hide(); } }
          ]}
        ]
      }
    });
  }

  /* ==== WINDOW CLOSE SHIFT ==== */
  if(!$$("win_close_shift")){
    webix.ui({
      view:"window", id:"win_close_shift", width:480, position:"center", modal:true,
      head:"Close Shift (Admin)",
      body:{
        view:"form", id:"form_close_shift",
        elements:[
          { view:"text", name:"id_karyawan", label:"ID Karyawan" },
          { view:"text", name:"close_cash", label:"Saldo Akhir (Cash)", value:0 },
          { view:"text", name:"kasir_sales_total", label:"Total Penjualan (optional)", value:0 },
          { cols:[
            { view:"button", value:"Tutup Shift", css:"webix_danger", click:function(){
              var d = $$("form_close_shift").getValues();
              if(!d.id_karyawan){
                webix.message({type:"error", text:"Masukkan ID karyawan"});
                return;
              }
              webix.ajax().headers({"Content-Type":"application/json"})
              .post("/api/shift/close", JSON.stringify({
                id_karyawan: d.id_karyawan,
                close_cash: parseInt(d.close_cash||0),
                kasir_sales_total: parseInt(d.kasir_sales_total||0)
              })).then(()=>{
                $$("table_shift_combined").clearAll();
                $$("table_shift_combined").load("/api/shift/all");
                $$("win_close_shift").hide();
                webix.message("Shift ditutup!");
              });
            }},
            { view:"button", value:"Batal", click:function(){ $$("win_close_shift").hide(); }}
          ]}
        ]
      }
    });
  }

  /* ==== TABLE SHIFT + LOG ==== */
  $$("main").addView({
    id:"shift",
    batch:"shift",
    rows:[
      { view:"toolbar", css:"webix_dark", cols:[
        { view:"label", label:"SHIFT (Master & Log)", align:"center" },{},
        { view:"button", value:"Tambah Master Shift", css:"webix_primary", width:180, click:function(){
            $$("form_master_shift").clear();
            $$("win_master_shift").show();
        }},
        { view:"button", value:"Open Shift", width:140, click:function(){
            $$("form_open_shift").clear();
            $$("win_open_shift").show();
        }},
        { view:"button", value:"Close Shift", width:140, css:"webix_danger", click:function(){
            $$("form_close_shift").clear();
            $$("win_close_shift").show();
        }}
      ]},

      {
        view:"datatable",
        id:"table_shift_combined",
        url:"/api/shift/all",
        select:"row",
        columns:[
          { id:"_id", header:"ID Shift", width:110 },
          { id:"nama_shift", header:"Nama Shift", fillspace:true },
          { id:"jam_mulai", header:"Mulai", width:100 },
          { id:"jam_selesai", header:"Selesai", width:100 },
          { id:"durasi_jam", header:"Durasi", width:120, template:o=>o.durasi_jam || hitungDurasi(o.jam_mulai,o.jam_selesai) },
          { id:"nama_kasir", header:"Kasir", width:150 },
          { id:"status", header:"Status", width:100 },
          { id:"waktu_mulai", header:"Waktu Mulai", width:180, template:o=>o.waktu_mulai?new Date(o.waktu_mulai).toLocaleString():"" },
          { id:"waktu_selesai", header:"Waktu Selesai", width:180, template:o=>o.waktu_selesai?new Date(o.waktu_selesai).toLocaleString():"" },
          { id:"aksi_shift", header:"Aksi", width:80, 
            template:"<span class='editBtn' style='cursor:pointer;color:#1E88E5'><i class='fa fa-edit'></i></span>"
          }
        ],

        onClick:{
          "editBtn":function(e,id){
            var it=this.getItem(id);
            if(!it) return false;
            var masterData = {
              _id: it._id,
              nama_shift: it.nama_shift,
              jam_mulai: it.jam_mulai,
              jam_selesai: it.jam_selesai,
              durasi_jam: it.durasi_jam || hitungDurasi(it.jam_mulai, it.jam_selesai),
              status_aktif: (typeof it.status_aktif !== "undefined") ? it.status_aktif : true
            };
            $$("form_master_shift").setValues(masterData);
            $$("win_master_shift").show();
            return false;
          }
        }
      }
    ]
  });

}
