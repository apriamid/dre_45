/* ================================
   MAIN DASHBOARD UI LAYOUT (FINAL)
   ================================ */

webix.ready(function () {

    webix.ui({
        rows:[
            {
                view:"toolbar",
                css:"webix_dark",
                height:50,
                cols:[
                    { view:"icon", icon:"fa-solid fa-bars", width:40 },
                    { view:"label", label:"<b>Sistem Kasir — Dashboard Admin</b>" },
                    {},
                    {
                        view:"button", value:"Logout", width:120, css:"webix_danger",
                        click:function(){ window.location.href = "/logout"; }
                    }
                ]
            },
            {
                cols:[
                    {
                        view:"sidebar",
                        id:"menuSidebar",
                        width:220,
                        css:"webix_dark",
                        data:[
                            { id:"karyawan", value:" Karyawan" },
                            { id:"produk", value:"Produk" },
                            { id:"pembelian", value:"Pembelian" },
                            { id:"shift", value:" Shift" },
                            { id:"laporan", value:"Laporan" }
                        ],
                        on:{
                          onAfterSelect:function(id){
                            // safe showBatch on mainContent
                            try{ $$("mainContent").showBatch(id); }catch(e){}
                          }
                        }
                    },

                    // mainContent must exist with at least one cell
                    {
                        view:"multiview",
                        id:"mainContent",
                        animate:true,
                        cells:[
                          { id:"placeholder", template:"Memuat..." }
                        ]
                    }
                ]
            }
        ]
    });

    // load modules (these functions are defined in other js files)
    try{ loadUI_karyawan(); }catch(e){ console.warn("loadUI_karyawan missing", e); }
    try{ loadUI_produk(); }catch(e){ console.warn("loadUI_produk missing", e); }
    try{ loadUI_pembelian(); }catch(e){ console.warn("loadUI_pembelian missing", e); }
    try{ loadUI_shift(); }catch(e){ console.warn("loadUI_shift missing", e); }
    try{ loadUI_laporan(); }catch(e){ console.warn("loadUI_laporan missing", e); }

    // show default view after a tiny delay so modules have time to add their views
    setTimeout(function(){
      if($$("menuSidebar")) $$("menuSidebar").select("karyawan");
      try{ $$("mainContent").showBatch("karyawan"); }catch(e){ console.warn("default showBatch failed", e); }
    }, 150);
});
