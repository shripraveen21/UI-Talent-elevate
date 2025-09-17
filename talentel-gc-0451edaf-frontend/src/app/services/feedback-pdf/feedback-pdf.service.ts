import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { marked } from 'marked';

@Injectable({
  providedIn: 'root'
})
export class FeedbackPdfService {
  private baseUrl = `${environment.apiUrl}/api/feedback`;

  constructor(private http: HttpClient) {}

  generatePDF(validationContent: string, userId: string, filename?: string): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    const body = {
      validation_content: validationContent,
      user_id: userId,
      filename: filename
    };

    return this.http.post(`${this.baseUrl}/generate-pdf`, body, { headers });
  }

  downloadPDF(fileId: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/download/${fileId}`, {
      responseType: 'blob'
    });
  }

  triggerDownload(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Generate PDF from markdown content using client-side libraries
   * @param markdownContent - The markdown content to convert to PDF
   * @param contentElement - The HTML element containing the rendered content
   * @param filename - Optional filename for the PDF
   */
  generateClientSidePDF(markdownContent: string, contentElement: HTMLElement, filename: string = 'detailed-feedback.pdf'): Promise<void> {
    return new Promise(async (resolve, reject) => {
      try {
        // Convert markdown to HTML
        const htmlContent = await marked(markdownContent);
        
        // Set the HTML content in the provided element
        contentElement.innerHTML = htmlContent;
        
        // Use a small delay to ensure the browser has rendered the HTML content fully
        setTimeout(() => {
          html2canvas(contentElement, { 
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
          }).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            
            // Calculate dimensions for A4 page
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();
            const canvasWidth = canvas.width;
            const canvasHeight = canvas.height;
            const ratio = canvasWidth / canvasHeight;
            const calculatedHeight = pdfWidth / ratio;
            
            // If content is longer than one page, we might need multiple pages
            if (calculatedHeight <= pdfHeight) {
              // Content fits in one page
              pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, calculatedHeight);
            } else {
              // Content needs multiple pages
              let position = 0;
              const pageHeight = pdfWidth / ratio;
              
              while (position < canvasHeight) {
                const pageCanvas = document.createElement('canvas');
                const pageCtx = pageCanvas.getContext('2d');
                pageCanvas.width = canvasWidth;
                pageCanvas.height = Math.min(canvasHeight - position, canvasWidth / (pdfWidth / pdfHeight));
                
                if (pageCtx) {
                  pageCtx.drawImage(canvas, 0, -position);
                  const pageImgData = pageCanvas.toDataURL('image/png');
                  
                  if (position > 0) {
                    pdf.addPage();
                  }
                  
                  pdf.addImage(pageImgData, 'PNG', 0, 0, pdfWidth, Math.min(pdfHeight, pageCanvas.height * pdfWidth / canvasWidth));
                }
                
                position += pageCanvas.height;
              }
            }
            
            // Save the PDF
            pdf.save(filename);
            
            // Clear the content after generation
            contentElement.innerHTML = '';
            
            resolve();
          }).catch(error => {
            console.error('Error generating canvas:', error);
            reject(error);
          });
        }, 100);
      } catch (error) {
        console.error('Error in PDF generation:', error);
        reject(error);
      }
    });
  }

  /**
   * Parse JSON-like string and extract markdown content
   * @param rawData - Raw JSON string containing validation content
   * @returns Cleaned markdown content
   */
  parseAndCleanMarkdown(rawData: string): string {
    try {
      const parsed = JSON.parse(rawData);
      return parsed.validation || parsed.content || rawData;
    } catch (error) {
      // If parsing fails, return the raw data
      return rawData;
    }
  }
}