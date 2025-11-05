/* ================================
   MODULE: LAPORAN (PROFIT) (FIXED)
   ================================ */

function loadUI_laporan(){

  $$("mainContent").addView({
    id:"laporan",
    batch:"laporan",
    rows:[
      { template:"<div id='laporan-content' style='padding:20px;text-align:center;'>Memuat laporan...</div>", height:500 }
    ]
  });

  function formatRupiah(angka){
    return new Intl.NumberFormat('id-ID', {style:'currency',currency:'IDR'}).format(angka||0);
  }

  function loadLaporanProfit() {
    const container = document.getElementById("laporan-content");
    if(!container) return;
    container.innerHTML = "<div id='chart' style='width:100%;height:400px;'></div>";

    fetch("/api/laporan/profit")
      .then(res => res.json())
      .then(data => {
        if (!data.success) throw new Error("Data gagal dimuat");
        const pembelian = data.total_pembelian || 0;
        const penjualan = data.total_penjualan || 0;
        const profit = data.profit || 0;
        const chartData = [
          { type: "Pembelian", total: pembelian },
          { type: "Penjualan", total: penjualan },
          { type: "Profit", total: profit }
        ];
        webix.ui({
          container: "chart",
          view: "chart",
          type: "bar",
          value: "#total#",
          barWidth: 60,
          tooltip: { template: "#type#: #total#" },
          color: function (obj) {
            if (obj.type === "Profit") return "#43A047";
            if (obj.type === "Penjualan") return "#1E88E5";
            return "#E53935";
          },
          xAxis: { template: "#type#" },
          yAxis: { start: 0, step: 50000 },
          data: chartData
        });
      })
      .catch(err => {
        if(document.getElementById("laporan-content")) document.getElementById("laporan-content").innerHTML = "<p style='color:red;'>Gagal memuat data profit.</p>";
        console.error(err);
      });
  }

  // panggil otomatis ketika view laporan muncul
  webix.attachEvent("onAfterViewChange", function(viewId){
    if(viewId == "laporan"){
      setTimeout(loadLaporanProfit, 200);
    }
  });

}
