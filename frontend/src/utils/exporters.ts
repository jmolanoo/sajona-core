function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function exportAsTxt(title: string, columns: string[], rows: Array<Array<string | number>>): void {
  const sep = " | ";
  const lines = [
    `SAJONA NÚCLEO — ${title}`,
    `Generado: ${new Date().toLocaleString("es-CO")}`,
    "-".repeat(60),
    columns.join(sep),
    "-".repeat(60),
    ...rows.map((r) => r.join(sep)),
  ];
  triggerDownload(
    new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" }),
    `${title.toLowerCase().replace(/\s+/g, "_")}.txt`
  );
}

export async function exportAsExcel(
  title: string,
  columns: string[],
  rows: Array<Array<string | number>>
): Promise<void> {
  const ExcelJS = (await import("exceljs")).default;
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet(title.slice(0, 31));
  ws.addRow([`SAJONA NÚCLEO — ${title}`]);
  ws.addRow(columns);
  ws.getRow(2).font = { bold: true };
  for (const r of rows) ws.addRow(r);
  const buf = await wb.xlsx.writeBuffer();
  triggerDownload(
    new Blob([buf], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }),
    `${title.toLowerCase().replace(/\s+/g, "_")}.xlsx`
  );
}

export async function exportAsPdf(
  title: string,
  columns: string[],
  rows: Array<Array<string | number>>
): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const autoTable = (await import("jspdf-autotable")).default;
  const doc = new jsPDF({ orientation: "landscape" });
  doc.setFontSize(13);
  doc.text(`SAJONA NÚCLEO — ${title}`, 14, 15);
  doc.setFontSize(9);
  doc.text(`Generado localmente: ${new Date().toLocaleString("es-CO")}`, 14, 21);
  autoTable(doc, {
    startY: 26,
    head: [columns],
    body: rows.map((r) => r.map(String)),
    styles: { fontSize: 8 },
  });
  doc.save(`${title.toLowerCase().replace(/\s+/g, "_")}.pdf`);
}
