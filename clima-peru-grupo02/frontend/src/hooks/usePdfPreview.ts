import { useState, useCallback } from 'react';
import { PdfReportOptions } from '../services/pdfGenerator';
import PDFPreview from '../components/PDFPreview';

export const usePdfPreview = () => {
  const [previewOptions, setPreviewOptions] = useState<PdfReportOptions | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const openPreview = useCallback((options: PdfReportOptions) => {
    setPreviewOptions(options);
    setIsPreviewOpen(true);
  }, []);

  const closePreview = useCallback(() => {
    setIsPreviewOpen(false);
    setPreviewOptions(null);
  }, []);

  const handleDownload = useCallback(() => {
    if (previewOptions) {
      // Importar dinámicamente PdfGenerator
      import('../services/pdfGenerator').then(({ pdfGenerator }) => {
        pdfGenerator.generate(previewOptions);
        closePreview();
      });
    }
  }, [previewOptions, closePreview]);

  return {
    isPreviewOpen,
    previewOptions,
    openPreview,
    closePreview,
    handleDownload,
  };
};

export default usePdfPreview;
