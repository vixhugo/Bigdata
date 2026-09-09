import React, { useState, useRef, useEffect } from 'react';
import { jsPDF } from 'jspdf';
import {
  X, FileDown, RotateCcw, ZoomIn, ZoomOut, RotateCw,
  ChevronLeft, ChevronRight, Maximize2, Minimize2
} from 'lucide-react';
import { pdfGenerator, PdfReportOptions } from '../services/pdfGenerator';

interface PDFPreviewProps {
  options: PdfReportOptions;
  onCancel: () => void;
  onDownload: () => void;
}

export const PDFPreview: React.FC<PDFPreviewProps> = ({ options, onCancel, onDownload }) => {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const previewRef = useRef<HTMLDivElement>(null);

  // Generar PDF para previsualizar usando el generador real
  const generatePDFPreview = async () => {
    setIsLoading(true);
    try {
      // Crear una instancia temporal de jsPDF para obtener el blob
      const isLandscape = options.orientation === 'landscape'
        || options.orientation === undefined && options.columns.length > 6;

      const doc = new jsPDF({
        orientation: isLandscape ? 'landscape' : 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const pw = doc.internal.pageSize.getWidth();
      const ph = doc.internal.pageSize.getHeight();
      const ml = 14;
      const mr = 14;
      const cw = pw - ml - mr;

      // Dibujar encabezado
      const hh = 38;
      doc.setFillColor(2, 132, 199);
      doc.rect(0, 0, pw, hh, 'F');
      doc.setFillColor(14, 165, 233);
      doc.rect(0, hh - 8, pw, 8, 'F');

      // Logo
      doc.setFillColor(255, 255, 255);
      doc.roundedRect(ml, 8, 18, 18, 2, 2, 'F');
      doc.setTextColor(2, 132, 199);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.text('PE', ml + 9, 19.5, { align: 'center' });

      // Título
      doc.setTextColor(255, 255, 255);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.text(options.title.toUpperCase(), ml + 22, 15, { maxWidth: cw - 22 - 40 });

      // Subtítulo
      if (options.subtitle) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(186, 230, 253);
        doc.text(options.subtitle, ml + 22, 22);
      }

      // Marca
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(186, 230, 253);
      doc.text('METEOPERÚ PRO', pw - mr, 12, { align: 'right' });

      // Fecha
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      const now = new Date().toLocaleString('es-PE', {
        timeZone: 'America/Lima',
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
      doc.text(`Generado: ${now}`, pw - mr, 19, { align: 'right' });
      doc.text('Hora Perú (UTC-5)', pw - mr, 24, { align: 'right' });

      // KPIs
      let y = hh + 4;
      if (options.kpis && options.kpis.length > 0) {
        doc.setFillColor(14, 165, 233);
        doc.rect(ml, y, cw, 5.5, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(255, 255, 255);
        doc.text('INDICADORES PRINCIPALES', ml + 3, y + 3.8);
        y += 8;

        const perRow = Math.min(4, options.kpis.length);
        const cardW = (cw - (perRow - 1) * 4) / perRow;
        const cardH = 22;

        options.kpis.forEach((kpi, i) => {
          const x = ml + (i % perRow) * (cardW + 4);
          const color = kpi.color ?? [14, 165, 233];

          doc.setFillColor(241, 245, 249);
          doc.roundedRect(x, y, cardW, cardH, 2, 2, 'F');

          doc.setFillColor(...color);
          doc.roundedRect(x, y, 3, cardH, 1, 1, 'F');

          doc.setFont('helvetica', 'bold');
          doc.setFontSize(15);
          doc.setTextColor(...color);
          const valStr = `${kpi.value}${kpi.unit ? ' ' + kpi.unit : ''}`;
          doc.text(valStr, x + 7, y + 10);

          doc.setFont('helvetica', 'normal');
          doc.setFontSize(7);
          doc.setTextColor(71, 85, 105);
          doc.text(kpi.label.toUpperCase(), x + 7, y + 15.5);
        });

        y += cardH + 6;
      }

      // Resumen de datos
      if (options.rows && options.rows.length > 0) {
        doc.setFillColor(14, 165, 233);
        doc.rect(ml, y, cw, 5.5, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(255, 255, 255);
        doc.text(`DATOS (${options.rows.length} registros)`, ml + 3, y + 3.8);
        y += 8;

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(71, 85, 105);
        doc.text('El PDF completo incluye tablas detalladas con todos los registros.', ml, y + 10);
        y += 20;
      }

      // Análisis
      if (options.analysis && options.analysis.length > 0) {
        doc.setFillColor(14, 165, 233);
        doc.rect(ml, y, cw, 5.5, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(255, 255, 255);
        doc.text('ANÁLISIS AUTOMÁTICO', ml + 3, y + 3.8);
        y += 8;

        options.analysis.forEach((point, i) => {
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(7);
          doc.setTextColor(14, 165, 233);
          doc.text('▶', ml + 4, y + 6 + i * 8);

          doc.setTextColor(15, 23, 42);
          doc.text(point.label + ': ', ml + 8, y + 6 + i * 8);

          doc.setFont('helvetica', 'normal');
          doc.setTextColor(71, 85, 105);
          const labelW = doc.getTextWidth(point.label + ': ') + 8;
          doc.text(point.value, ml + labelW, y + 6 + i * 8);
        });
      }

      // Pie de página
      const fy = ph - 9;
      doc.setFillColor(241, 245, 249);
      doc.rect(0, fy - 2, pw, 12, 'F');
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(6.5);
      doc.setTextColor(148, 163, 184);
      doc.text('METEOPERÚ — Sistema Meteorológico del Perú', ml, fy + 2);
      doc.text(options.title, pw / 2, fy + 2, { align: 'center' });
      doc.text('Página 1 de 1', pw - mr, fy + 2, { align: 'right' });

      const output = doc.output();
      const blob = new Blob([output], { type: 'application/pdf' });
      setPdfBlob(blob);

      // Calcular páginas estimadas
      const rows = options.rows || [];
      const estimatedPages = Math.max(1, Math.ceil(rows.length / 30) + 1);
      setTotalPages(estimatedPages);
    } catch (error) {
      console.error('Error generando preview:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const [pdfBlob, setPdfBlob] = useState<Blob | null>(null);

  useEffect(() => {
    generatePDFPreview();
  }, [options]);

  const handleDownload = async () => {
    setIsLoading(true);
    try {
      await pdfGenerator.generate(options);
      onDownload();
    } catch (error) {
      console.error('Error generando PDF:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrint = () => {
    if (pdfBlob) {
      const url = URL.createObjectURL(pdfBlob);
      const win = window.open(url, '_blank');
      if (win) {
        win.focus();
        win.print();
      }
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/95 backdrop-blur-sm p-4">
      <div className="w-full max-w-5xl max-h-[90vh] flex flex-col rounded-3xl overflow-hidden shadow-2xl bg-white dark:bg-slate-900">
        
        {/* Header */}
        <div className="h-16 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 bg-slate-50 dark:bg-slate-950/50">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
              <FileDown className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                {options.title}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Vista previa del PDF • {currentPage} / {totalPages}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-4 py-2 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-sm font-semibold border border-blue-500/30 transition-colors flex items-center gap-2"
            >
              <RotateCw className="w-4 h-4" />
              <span>Imprimir</span>
            </button>
            <button
              onClick={handleDownload}
              className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold shadow-lg shadow-sky-500/20 transition-all flex items-center gap-2"
            >
              <FileDown className="w-4 h-4" />
              <span>Descargar PDF</span>
            </button>
            <button
              onClick={onCancel}
              className="px-3 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 text-sm font-semibold transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="h-12 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 bg-slate-50 dark:bg-slate-950/50">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setScale(Math.max(0.5, scale - 0.1))}
              className="p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm text-slate-600 dark:text-slate-400 min-w-[60px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => setScale(Math.min(2, scale + 0.1))}
              className="p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <div className="w-px h-5 bg-slate-200 dark:bg-slate-700 mx-2" />
            <button
              onClick={() => setRotation(rotation - 90)}
              className="p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700"
            >
              <RotateCw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              className="p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-slate-200 dark:border-slate-700"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-slate-700 dark:text-slate-300 font-medium min-w-[100px] text-center">
              Página {currentPage} de {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage >= totalPages}
              className="p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-slate-200 dark:border-slate-700"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Preview Container */}
        <div className="flex-1 overflow-auto bg-slate-100 dark:bg-slate-950/50 flex items-center justify-center p-8">
          <div
            ref={previewRef}
            className="transition-transform duration-300 ease-out"
            style={{
              transform: `scale(${scale}) rotate(${rotation}deg)`,
              transformOrigin: 'center center',
              width: '210mm',
              height: options.orientation === 'landscape' ? '297mm' : '210mm',
              backgroundColor: '#ffffff',
              padding: '15mm',
              boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
              position: 'relative',
            }}
          >
            {/* Page header */}
            <div className="mb-8 pb-4 border-b-2 border-sky-500/20">
              <h1 className="text-3xl font-bold text-sky-900 dark:text-sky-400 mb-2 uppercase">
                {options.title}
              </h1>
              {options.subtitle && (
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {options.subtitle}
                </p>
              )}
            </div>

            {/* KPIs Preview */}
            {options.kpis && options.kpis.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 mb-4 uppercase tracking-wider text-sm">
                  Indicadores Clave
                </h3>
                <div className="grid grid-cols-4 gap-3">
                  {options.kpis.slice(0, 4).map((kpi: any, i: number) => (
                    <div key={i} className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl">
                      <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase mb-1">
                        {kpi.label}
                      </p>
                      <p className="text-xl font-bold text-sky-600 dark:text-sky-400">
                        {kpi.value}
                        {kpi.unit && <span className="text-sm ml-1">{kpi.unit}</span>}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preview de gráficas */}
            {options.charts && options.charts.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 mb-3 uppercase tracking-wider text-sm">
                  Visualización
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {options.charts.slice(0, 2).map((chart: any, i: number) => (
                    <div key={i} className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl h-32 flex items-center justify-center border border-slate-200 dark:border-slate-700">
                      <span className="text-xs text-slate-500 dark:text-slate-400 text-center">
                        Gráfica: {chart.title}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preview de tabla */}
            {options.rows && options.rows.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 mb-2 uppercase tracking-wider text-sm">
                  Tabla de Datos
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-sky-500 text-white">
                        {options.columns.slice(0, 5).map((col: any, i: number) => (
                          <th key={i} className="px-2 py-2 text-left font-semibold">
                            {col.header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {options.rows.slice(0, 3).map((row: any, i: number) => (
                        <tr key={i} className="border-b border-slate-200 dark:border-slate-700">
                          {options.columns.slice(0, 5).map((col: any, j: number) => (
                            <td key={j} className="px-2 py-1">
                              {col.format ? col.format(row[col.key]) : row[col.key]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {options.rows.length > 3 && (
                  <p className="text-xs text-slate-500 mt-2 text-center">
                    ... ({options.rows.length} registros totales)
                  </p>
                )}
              </div>
            )}

            {/* Footer */}
            <div className="mt-12 pt-4 border-t border-slate-200 dark:border-slate-700 flex justify-between text-[10px] text-slate-400">
              <span>MeteoPerú - Sistema Meteorológico del Perú</span>
              <span>Página {currentPage} • {new Date().toLocaleDateString('es-PE')}</span>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-500/5 border-t border-blue-500/20 p-4 text-center">
          <p className="text-sm text-blue-700 dark:text-blue-400">
            <span className="font-semibold">Nota:</span> Esta es una vista previa. Usa "Descargar PDF" para guardar el archivo completo con todas las gráficas y análisis.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PDFPreview;
