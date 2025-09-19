import { Component, OnInit } from '@angular/core';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { FeedbackPdfService } from '../../services/feedback-pdf/feedback-pdf.service';
import { ToastService } from '../../services/toast/toast.service';
import { CommonModule } from '@angular/common';
import { MarkdownModule } from 'ngx-markdown';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { PdfDownloadModalComponent } from '../shared/pdf-download-modal/pdf-download-modal.component';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import 'prismjs';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-debug-results',
  templateUrl: './debug-results.component.html',
  styleUrls: ['./debug-results.component.css'],
  imports: [CommonModule, MarkdownModule]
})
export class DebugResultsComponent implements OnInit {
  userName: string = '';
  debugTestId!: number;
  result: any = null;
  loading = true;
  error = '';
  
  // PDF Modal state
  showPdfModal = false;
  isGeneratingPdf = false;
  currentExerciseForPdf: any = null;
  currentExerciseIndex = 0;
  selectedExerciseIndex = 0;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private dashboardService: DashboardService,
    private sanitizer: DomSanitizer,
    private feedbackPdfService: FeedbackPdfService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    const userObj = localStorage.getItem('username');
    let userName = 'User';
    if (userObj) {
      try {
        const user = JSON.parse(userObj);
        userName = user.name || 'User';
      } catch {
        userName = userObj || 'User';
      }
    }
    this.userName = userName;
    this.debugTestId = Number(this.route.snapshot.paramMap.get('id'));
    const token = localStorage.getItem('token');
    if (token && this.debugTestId) {
      this.dashboardService.getDebugResults(this.debugTestId, token).subscribe({
        next: (data) => {
          if (data.pending) {
            this.result = null;
            this.loading = false;
            return;
          }
          this.result = data;
          console.log(this.result)
          this.loading = false;
        },
        error: () => {
          this.error = 'Failed to load debug test results';
          this.loading = false;
        }
      });
    } else {
      this.error = 'Test or authentication info missing';
      this.loading = false;
    }
  }

  // Helper methods for the new UI
  getOverallScore(): number {
    if (this.result?.overall_score) {
      return this.result.overall_score;
    }
    return 0;
  }

  getOverallGrade(): string {
    if (this.result?.overall_grade) {
      return this.result.overall_grade;
    }
    return 'F';
  }

  getCorrectCount(): number {
    if (!this.result?.results) return 0;
    return this.result.results.filter((res: any) => res.status === 'CORRECT').length;
  }

  getPartialCount(): number {
    if (!this.result?.results) return 0;
    return this.result.results.filter((res: any) => res.status === 'PARTIAL').length;
  }

  getIncorrectCount(): number {
    if (!this.result?.results) return 0;
    return this.result.results.filter((res: any) => res.status === 'INCORRECT').length;
  }

  getCorrectnessScore(res: any): number {
    if (res.scoring_breakdown?.correctness !== undefined) {
      return res.scoring_breakdown.correctness;
    }
    return res.status === 'CORRECT' ? 100 : res.status === 'PARTIAL' ? 50 : 0;
  }

  getCodeQualityScore(res: any): number {
    if (res.scoring_breakdown?.code_quality !== undefined) {
      return res.scoring_breakdown.code_quality;
    }
    return res.status === 'CORRECT' ? 100 : res.status === 'PARTIAL' ? 50 : 30;
  }

  getCompletenessScore(res: any): number {
    if (res.scoring_breakdown?.completeness !== undefined) {
      return res.scoring_breakdown.completeness;
    }
    return res.status === 'CORRECT' ? 100 : res.status === 'PARTIAL' ? 50 : 20;
  }

  getLearningScore(res: any): number {
    if (res.scoring_breakdown?.learning_application !== undefined) {
      return res.scoring_breakdown.learning_application;
    }
    return res.status === 'CORRECT' ? 100 : res.status === 'PARTIAL' ? 50 : 10;
  }

  getResources(res: any): string[] {
    if (res.feedback?.resources) {
      // Only return actual markdown links [text](url)
      return res.feedback.resources.filter((item: string) => {
        if (!item || item.trim() === '') return false;
        // Check if it's a markdown link format [text](url)
        return /\[([^\]]+)\]\(([^)]+)\)/.test(item);
      });
    }
    return [];
  }

  getResourcesMarkdown(res: any): string {
    if (!res.feedback?.resources) return '';
    
    // Get all non-link content and render as markdown
    const nonLinkContent = res.feedback.resources
      .filter((item: string) => {
        if (!item || item.trim() === '') return false;
        // Exclude markdown links and separators
        return !/\[([^\]]+)\]\(([^)]+)\)/.test(item) && item !== '--' && item !== '***';
      })
      .join('\n');
    
    return nonLinkContent;
  }

  formatResourceText(resource: string): string {
    // Check if the resource contains a markdown link format [text](url)
    const linkMatch = resource.match(/\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      const text = linkMatch[1];
      const url = linkMatch[2];
      return `<span class="cursor-pointer">${text}</span>`;
    }
    return resource;
  }

  openResource(resource: string): void {
    // Extract URL from markdown link format [text](url)
    const linkMatch = resource.match(/\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      const url = linkMatch[2];
      window.open(url, '_blank');
    } else if (resource.startsWith('http')) {
      // If it's already a URL, open it directly
      window.open(resource, '_blank');
    }
  }

  getStrengths(res: any): string[] {
    if (res.feedback?.strengths) {
      return res.feedback.strengths.filter((item: string) => 
        item && item.trim() !== '' && item !== '--' && item !== '***'
      );
    }
    return [];
  }

  getAreasForImprovement(res: any): string[] {
    if (res.feedback?.areas_for_improvement) {
      return res.feedback.areas_for_improvement.filter((item: string) => 
        item && item.trim() !== '' && item !== '--' && item !== '***'
      );
    }
    return [];
  }

  getNextSteps(res: any): string[] {
    if (res.feedback?.next_steps) {
      return res.feedback.next_steps.filter((item: string) => 
        item && item.trim() !== '' && item !== '--' && item !== '***'
      );
    }
    return [];
  }

  formatFeedbackText(text: string): string {
    if (!text) return '';
    
    // Handle markdown formatting
    let formatted = text
      // Bold text **text** -> <strong>text</strong>
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic text *text* -> <em>text</em>
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Code `text` -> <code>text</code>
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
      // Line breaks
      .replace(/\n/g, '<br>');
    
    return formatted;
  }

  getStrengthsMarkdown(res: any): string {
    if (!res.feedback?.strengths) return '';
    
    const strengths = res.feedback.strengths
      .filter((item: string) => item && item.trim() !== '' && item !== '--' && item !== '***')
      .map((item: string) => `- ${item}`)
      .join('\n');
    
    return strengths;
  }

  getAreasForImprovementMarkdown(res: any): string {
    if (!res.feedback?.areas_for_improvement) return '';
    
    const improvements = res.feedback.areas_for_improvement
      .filter((item: string) => item && item.trim() !== '' && item !== '--' && item !== '***')
      .map((item: string) => `- ${item}`)
      .join('\n');
    
    return improvements;
  }

  getNextStepsMarkdown(res: any): string {
    if (!res.feedback?.next_steps) return '';
    
    const steps = res.feedback.next_steps
      .filter((item: string) => item && item.trim() !== '' && item !== '--' && item !== '***')
      .map((item: string, index: number) => `${index + 1}. ${item}`)
      .join('\n');
    
    return steps;
  }

  getResourceTitle(resource: string): string {
    // Extract title from markdown link format [title](url)
    const linkMatch = resource.match(/\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      return linkMatch[1]; // Return the title part
    }
    
    // If it's not a markdown link, return the resource as is
    return resource;
  }

  processValidationContent(validation: string): SafeHtml {
    if (!validation) return this.sanitizer.bypassSecurityTrustHtml('');
    
    // Process code blocks to ensure proper formatting
    let processed = validation
      // Fix code blocks that might not be properly formatted
      .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang || 'text';
        return `\`\`\`${language}\n${code.trim()}\n\`\`\``;
      })
      // Fix inline code that might be in backticks but not properly formatted
      .replace(/`([^`\n]+)`/g, '`$1`')
      // Ensure proper spacing around code blocks
      .replace(/\n```/g, '\n\n```')
      .replace(/```\n/g, '```\n\n');
    
    return this.sanitizer.bypassSecurityTrustHtml(processed);
  }

  getStructuredFeedback(validation: string, section: string): string {
    if (!validation) return '<p class="no-content">No feedback available for this section.</p>';
    
    // Enhanced code block processing with syntax highlighting
    const processCodeBlocks = (text: string): string => {
      return text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang || 'text';
        const trimmedCode = code.trim();
        return `<div class="code-block-container">
          <div class="code-block-header">
            <span class="code-language">${language.toUpperCase()}</span>
            <button class="copy-button" onclick="navigator.clipboard.writeText(\`${trimmedCode.replace(/`/g, '\\`')}\`)" title="Copy code">
              <svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
          <pre class="code-block"><code class="language-${language}">${this.escapeHtml(trimmedCode)}</code></pre>
        </div>`;
      });
    };

    // Process inline code
    const processInlineCode = (text: string): string => {
      return text.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');
    };

    // Process markdown formatting
    const processMarkdown = (text: string): string => {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="bold-text">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="italic-text">$1</em>')
        .replace(/\n\n/g, '</p><p class="paragraph">')
        .replace(/\n/g, '<br>');
    };

    // Extract section content based on keywords and structure
    let sectionContent = '';
    const lowerValidation = validation.toLowerCase();
    
    switch (section) {
      case 'correctness':
        sectionContent = this.extractSectionContent(validation, [
          'correctness', 'bug identified', 'solution analysis', 'fixes the bug', 'edge cases',
          'correct', 'incorrect', 'accuracy', 'functional'
        ]);
        break;
      case 'code_quality':
        sectionContent = this.extractSectionContent(validation, [
          'code quality', 'readability', 'best practices', 'performance', 'maintainability',
          'clean code', 'optimization', 'efficiency', 'style'
        ]);
        break;
      case 'completeness':
        sectionContent = this.extractSectionContent(validation, [
          'completeness', 'complete', 'missing', 'requirements', 'functionality',
          'implementation', 'coverage', 'thorough'
        ]);
        break;
      case 'alternatives':
        sectionContent = this.extractSectionContent(validation, [
          'alternative', 'other solutions', 'different approach', 'better way',
          'could also', 'another option', 'consider', 'alternatively'
        ]);
        break;
      case 'improvements':
        sectionContent = this.extractSectionContent(validation, [
          'improvement', 'enhance', 'better', 'optimize', 'refactor',
          'should', 'could', 'recommend', 'suggest'
        ]);
        break;
      case 'recommendations':
        sectionContent = this.extractSectionContent(validation, [
          'recommendation', 'best practice', 'guideline', 'standard',
          'convention', 'pattern', 'principle', 'advice'
        ]);
        break;
      case 'technical_notes':
        sectionContent = this.extractSectionContent(validation, [
          'technical', 'note', 'important', 'warning', 'caution',
          'remember', 'keep in mind', 'consider', 'be aware'
        ]);
        break;
      default:
        sectionContent = validation;
    }

    if (!sectionContent.trim()) {
      return '<p class="no-content">No specific feedback available for this section.</p>';
    }

    // Process the content
    let processed = processCodeBlocks(sectionContent);
    processed = processInlineCode(processed);
    processed = processMarkdown(processed);
    
    // Wrap in paragraph tags if not already wrapped
    if (!processed.includes('<p') && !processed.includes('<div') && !processed.includes('<ul') && !processed.includes('<ol')) {
      processed = `<p class="paragraph">${processed}</p>`;
    }

    return processed;
  }

  private extractSectionContent(validation: string, keywords: string[]): string {
    const lines = validation.split('\n');
    const relevantLines: string[] = [];
    let inRelevantSection = false;
    let sectionBuffer: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].toLowerCase();
      const isKeywordLine = keywords.some(keyword => line.includes(keyword));
      
      if (isKeywordLine) {
        if (sectionBuffer.length > 0) {
          relevantLines.push(...sectionBuffer);
          sectionBuffer = [];
        }
        relevantLines.push(lines[i]);
        inRelevantSection = true;
      } else if (inRelevantSection) {
        // Continue collecting lines until we hit another section or empty lines
        if (line.trim() === '' && sectionBuffer.length > 0) {
          relevantLines.push(...sectionBuffer);
          sectionBuffer = [];
          inRelevantSection = false;
        } else if (line.trim() !== '') {
          sectionBuffer.push(lines[i]);
        }
      }
    }

    // Add any remaining buffer content
    if (sectionBuffer.length > 0) {
      relevantLines.push(...sectionBuffer);
    }

    // If no specific content found, return a portion of the original validation
    if (relevantLines.length === 0) {
      const sentences = validation.split(/[.!?]+/);
      const relevantSentences = sentences.filter(sentence => 
        keywords.some(keyword => sentence.toLowerCase().includes(keyword))
      );
      return relevantSentences.slice(0, 3).join('. ') + (relevantSentences.length > 0 ? '.' : '');
    }

    return relevantLines.join('\n');
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Get status badge class based on score
  getStatusBadgeClass(score: number): string {
    if (score >= 80) return 'status-pass';
    if (score >= 60) return 'status-partial';
    return 'status-fail';
  }

  // Get status text based on score
  getStatusText(score: number): string {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Needs Improvement';
  }

  // Get progress bar color based on score
  getProgressBarColor(score: number): string {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  }

  // Get icon for assessment sections
  getSectionIcon(sectionType: string): string {
    const icons: { [key: string]: string } = {
      'correctness': '🎯',
      'code-quality': '⚡',
      'completeness': '✅',
      'alternatives': '🔄',
      'improvements': '🚀',
      'recommendations': '💡',
      'technical-notes': '📝'
    };
    return icons[sectionType] || '📋';
  }

  // Format bullet points from text
  formatBulletPoints(text: string): string[] {
    if (!text) return [];
    
    // Split by common bullet point patterns
    const bulletPatterns = /[•\-\*]\s+|\d+\.\s+|\n\s*[•\-\*]\s+|\n\s*\d+\.\s+/g;
    const points = text.split(bulletPatterns)
      .map(point => point.trim())
      .filter(point => point.length > 0);
    
    return points;
  }

  // Enhanced code block processing with language detection
  processCodeBlocks(content: string): string {
    if (!content) return '';
    
    // Enhanced regex to detect code blocks with optional language specification
    const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
    const inlineCodeRegex = /`([^`]+)`/g;
    
    let processedContent = content;
    
    // Process multi-line code blocks
    processedContent = processedContent.replace(codeBlockRegex, (match, language, code) => {
      const lang = language || 'text';
      const escapedCode = this.escapeHtml(code.trim());
      return `<div class="code-block" data-language="${lang}"><pre><code>${escapedCode}</code></pre></div>`;
    });
    
    // Process inline code
    processedContent = processedContent.replace(inlineCodeRegex, (match, code) => {
      const escapedCode = this.escapeHtml(code);
      return `<span class="inline-code">${escapedCode}</span>`;
    });
    
    return processedContent;
  }

  // Get table icon based on status
  getTableIcon(status: string): string {
    switch (status.toLowerCase()) {
      case 'pass':
      case 'passed':
      case 'excellent':
        return '✅';
      case 'fail':
      case 'failed':
      case 'needs improvement':
        return '❌';
      case 'partial':
      case 'good':
        return '⚠️';
      default:
        return '📊';
    }
  }

  // Get score color based on score value
  getScoreColor(score: number): string {
    if (score >= 80) return '#10b981'; // green
    if (score >= 60) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  }

  // New PDF download methods
  selectExercise(index: number): void {
    this.selectedExerciseIndex = index;
  }

  openPdfDownloadModal(exerciseResult: any, exerciseIndex: number): void {
    this.currentExerciseForPdf = exerciseResult;
    this.currentExerciseIndex = exerciseIndex;
    this.showPdfModal = true;
  }

  closePdfModal(): void {
    this.showPdfModal = false;
    this.isGeneratingPdf = false;
    this.currentExerciseForPdf = null;
  }

  async confirmPdfDownload(): Promise<void> {
    if (!this.currentExerciseForPdf) return;

    try {
      // Use the new client-side PDF generation method
      await this.generateDetailedFeedbackPDF(this.currentExerciseForPdf, this.currentExerciseIndex);
      
      // Close modal after successful generation
      this.closePdfModal();
      
    } catch (error) {
      console.error('Error generating PDF:', error);
      this.toastService.showError('Failed to generate PDF. Please try again.');
      this.isGeneratingPdf = false;
    }
  }

  private getUserIdFromToken(): string | null {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub || payload.user_id || payload.id;
      }
    } catch (error) {
      console.error('Error parsing token:', error);
    }
    return null;
  }

  async generateDetailedFeedbackPDF(exerciseResult: any, exerciseIndex: number): Promise<void> {
    try {
      this.isGeneratingPdf = true;
      
      // Create a temporary container for PDF content
      const pdfContainer = document.createElement('div');
      pdfContainer.id = 'pdf-content-container';
      pdfContainer.style.position = 'absolute';
      pdfContainer.style.left = '-9999px';
      pdfContainer.style.top = '0';
      pdfContainer.style.width = '210mm'; // A4 width
      pdfContainer.style.backgroundColor = 'white';
      pdfContainer.style.padding = '20mm';
      pdfContainer.style.fontFamily = 'Arial, sans-serif';
      pdfContainer.style.fontSize = '12px';
      pdfContainer.style.lineHeight = '1.6';
      pdfContainer.style.color = '#333';
      
      document.body.appendChild(pdfContainer);
      
      // Generate markdown content for the exercise
      const markdownContent = this.generateMarkdownContent(exerciseResult, exerciseIndex);
      
      // Use the service to generate PDF
      const fileName = `detailed-feedback-exercise-${exerciseIndex + 1}-${new Date().toISOString().split('T')[0]}.pdf`;
      
      await this.feedbackPdfService.generateClientSidePDF(markdownContent, pdfContainer, fileName);
      
      // Remove temporary container
      document.body.removeChild(pdfContainer);
      
      this.toastService.showSuccess('PDF downloaded successfully!');
      
    } catch (error) {
      console.error('Error generating PDF:', error);
      this.toastService.showError('Failed to generate PDF. Please try again.');
    } finally {
      this.isGeneratingPdf = false;
    }
  }

  // Generate markdown content for PDF
  private generateMarkdownContent(exerciseResult: any, exerciseIndex: number): string {
    const exerciseName = exerciseResult?.exercise_name || 'Code Analysis';
    const status = exerciseResult?.status || 'N/A';
    const score = exerciseResult?.score !== undefined ? `${exerciseResult.score}/100` : 'N/A';
    const difficulty = exerciseResult?.difficulty || 'N/A';
    const validation = exerciseResult?.validation || '';
    
    let markdown = `# Detailed Feedback Report\n\n`;
    markdown += `## Exercise: ${exerciseName}\n\n`;
    markdown += `**Status:** ${status}\n`;
    markdown += `**Score:** ${score}\n`;
    markdown += `**Difficulty:** ${difficulty}\n`;
    markdown += `**Generated:** ${new Date().toLocaleDateString()}\n\n`;
    
    // Add validation content as markdown
    if (validation) {
      const cleanedValidation = this.feedbackPdfService.parseAndCleanMarkdown(validation);
      markdown += `## Detailed Analysis\n\n${cleanedValidation}\n\n`;
    }
    
    // Add structured feedback sections
    const strengths = this.getStrengthsMarkdown(exerciseResult);
    if (strengths) {
      markdown += `## Strengths\n\n${strengths}\n\n`;
    }
    
    const improvements = this.getAreasForImprovementMarkdown(exerciseResult);
    if (improvements) {
      markdown += `## Areas for Improvement\n\n${improvements}\n\n`;
    }
    
    const nextSteps = this.getNextStepsMarkdown(exerciseResult);
    if (nextSteps) {
      markdown += `## Next Steps\n\n${nextSteps}\n\n`;
    }
    
    const resources = this.getResourcesMarkdown(exerciseResult);
    if (resources) {
      markdown += `## Additional Resources\n\n${resources}\n\n`;
    }
    
    return markdown;
  }

  // Generate PDF content with professional formatting (legacy method)
  private generatePDFContent(exerciseResult: any, exerciseIndex: number): string {
    const exerciseName = exerciseResult?.exercise_name || 'Code Analysis';
    const status = exerciseResult?.status || 'N/A';
    const score = exerciseResult?.score !== undefined ? `${exerciseResult.score}/100` : 'N/A';
    const difficulty = exerciseResult?.difficulty || 'N/A';
    
    return `
      <div style="max-width: 100%; margin: 0 auto; font-family: 'Segoe UI', Arial, sans-serif;">
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #667eea;">
          <h1 style="color: #2d3748; font-size: 28px; margin: 0 0 10px 0; font-weight: 700;">Detailed Feedback Report</h1>
          <h2 style="color: #4a5568; font-size: 20px; margin: 0; font-weight: 600;">Exercise ${exerciseIndex + 1}: ${exerciseName}</h2>
        </div>
        
        <!-- Exercise Summary -->
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid #667eea;">
          <h3 style="color: #2d3748; font-size: 18px; margin: 0 0 15px 0; font-weight: 600;">📊 Exercise Summary</h3>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
            <div>
              <strong style="color: #4a5568;">Status:</strong>
              <div style="color: ${status.toLowerCase() === 'passed' ? '#22543d' : '#742a2a'}; font-weight: 600;">${status}</div>
            </div>
            <div>
              <strong style="color: #4a5568;">Score:</strong>
              <div style="color: #2a4365; font-weight: 600;">${score}</div>
            </div>
            <div>
              <strong style="color: #4a5568;">Difficulty:</strong>
              <div style="color: #553c9a; font-weight: 600;">${difficulty}</div>
            </div>
          </div>
        </div>
        
        <!-- Validation Content -->
        ${this.generateValidationSectionsForPDF(exerciseResult.validation)}
        
        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; text-align: center; color: #718096; font-size: 12px;">
          <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
          <p>This report contains detailed feedback and recommendations for code improvement.</p>
        </div>
      </div>
    `;
  }

  // Generate validation sections for PDF
  private generateValidationSectionsForPDF(validation: string): string {
    if (!validation) {
      return '<div style="text-align: center; color: #718096; font-style: italic; padding: 40px;">No validation content available.</div>';
    }

    const sections = [
      { key: 'correctness', title: 'Correctness Assessment', icon: '🎯' },
      { key: 'code_quality', title: 'Code Quality Analysis', icon: '⚡' },
      { key: 'completeness', title: 'Completeness Check', icon: '✅' },
      { key: 'alternatives', title: 'Alternative Solutions', icon: '🔄' },
      { key: 'improvements', title: 'Specific Improvements Needed', icon: '🚀' },
      { key: 'recommendations', title: 'Code Quality Recommendations', icon: '💡' },
      { key: 'technical_notes', title: 'Technical Accuracy Notes', icon: '📝' }
    ];

    let sectionsHtml = '';
    
    sections.forEach(section => {
      const content = this.extractSectionContent(validation, this.getSectionKeywords(section.key));
      if (content.trim()) {
        sectionsHtml += `
          <div style="margin-bottom: 30px; break-inside: avoid;">
            <h3 style="color: #2d3748; font-size: 16px; margin: 0 0 15px 0; font-weight: 600; display: flex; align-items: center; gap: 8px; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 6px;">
              <span style="font-size: 18px;">${section.icon}</span>
              ${section.title}
            </h3>
            <div style="padding: 15px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; line-height: 1.6;">
              ${this.formatContentForPDF(content)}
            </div>
          </div>
        `;
      }
    });

    // Add complete validation as fallback if no sections found
    if (!sectionsHtml.trim()) {
      sectionsHtml = `
        <div style="margin-bottom: 30px;">
          <h3 style="color: #2d3748; font-size: 16px; margin: 0 0 15px 0; font-weight: 600; display: flex; align-items: center; gap: 8px; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 6px;">
            <span style="font-size: 18px;">📋</span>
            Complete Validation Report
          </h3>
          <div style="padding: 15px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; line-height: 1.6;">
            ${this.formatContentForPDF(validation)}
          </div>
        </div>
      `;
    }

    return sectionsHtml;
  }

  // Format content for PDF (convert markdown-like content to HTML)
  private formatContentForPDF(content: string): string {
    if (!content) return '<p style="color: #718096; font-style: italic;">No content available.</p>';
    
    let formatted = content
      // Convert code blocks
      .replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, language, code) => {
        return `<div style="background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 12px; margin: 10px 0; font-family: 'Courier New', monospace; font-size: 11px; overflow-x: auto;"><pre style="margin: 0; white-space: pre-wrap;">${this.escapeHtmlForPDF(code.trim())}</pre></div>`;
      })
      // Convert inline code
      .replace(/`([^`]+)`/g, '<code style="background: #f7fafc; padding: 2px 4px; border-radius: 3px; font-family: \'Courier New\', monospace; font-size: 11px; border: 1px solid #e2e8f0;">$1</code>')
      // Convert headers
      .replace(/^### (.*$)/gm, '<h4 style="color: #2d3748; font-size: 14px; font-weight: 600; margin: 15px 0 8px 0;">$1</h4>')
      .replace(/^## (.*$)/gm, '<h3 style="color: #2d3748; font-size: 16px; font-weight: 600; margin: 20px 0 10px 0;">$1</h3>')
      .replace(/^# (.*$)/gm, '<h2 style="color: #2d3748; font-size: 18px; font-weight: 600; margin: 25px 0 12px 0;">$1</h2>')
      // Convert bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight: 600; color: #2d3748;">$1</strong>')
      // Convert italic text
      .replace(/\*(.*?)\*/g, '<em style="font-style: italic; color: #4a5568;">$1</em>')
      // Convert bullet points
      .replace(/^[•\-\*]\s+(.*)$/gm, '<li style="margin: 4px 0;">$1</li>')
      // Convert numbered lists
      .replace(/^\d+\.\s+(.*)$/gm, '<li style="margin: 4px 0;">$1</li>')
      // Convert line breaks to paragraphs
      .split('\n\n')
      .map(paragraph => {
        if (paragraph.includes('<li>')) {
          return `<ul style="margin: 10px 0; padding-left: 20px;">${paragraph}</ul>`;
        } else if (paragraph.trim() && !paragraph.includes('<h') && !paragraph.includes('<div') && !paragraph.includes('<code')) {
          return `<p style="margin: 8px 0; text-align: justify;">${paragraph.trim()}</p>`;
        }
        return paragraph;
      })
      .join('\n');
    
    return formatted;
  }

  // Get section keywords for content extraction
  private getSectionKeywords(sectionKey: string): string[] {
    const keywordMap: { [key: string]: string[] } = {
      'correctness': ['correctness', 'bug identified', 'solution analysis', 'fixes the bug', 'edge cases', 'correct', 'incorrect', 'accuracy', 'functional'],
      'code_quality': ['code quality', 'readability', 'best practices', 'performance', 'maintainability', 'clean code', 'optimization', 'efficiency', 'style'],
      'completeness': ['completeness', 'complete', 'missing', 'requirements', 'functionality', 'implementation', 'coverage', 'thorough'],
      'alternatives': ['alternative', 'other solutions', 'different approach', 'better way', 'could also', 'another option', 'consider', 'alternatively'],
      'improvements': ['improvement', 'enhance', 'better', 'optimize', 'refactor', 'should', 'could', 'recommend', 'suggest'],
      'recommendations': ['recommendation', 'best practice', 'guideline', 'standard', 'convention', 'pattern', 'principle', 'advice'],
      'technical_notes': ['technical', 'note', 'important', 'warning', 'caution', 'remember', 'keep in mind', 'consider', 'be aware']
    };
    return keywordMap[sectionKey] || [];
  }

  // Escape HTML for PDF
  private escapeHtmlForPDF(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Helper methods for bug status and counts
  getBugStatus(bug: any): string {
    // Determine bug status based on assessment score
    if (!bug.assessment?.overall_score) {
      return 'failed';
    }
    
    const score = bug.assessment.overall_score;
    if (score >= 70) {
      return 'success';
    } else if (score >= 50) {
      return 'partial';
    } else {
      return 'failed';
    }
  }

  getSuccessfulBugs(): number {
    if (!this.result?.bug_wise_results) {
      return 0;
    }
    return this.result.bug_wise_results.filter((bug: any) => this.getBugStatus(bug) === 'success').length;
  }

  getPartialBugs(): number {
    if (!this.result?.bug_wise_results) {
      return 0;
    }
    return this.result.bug_wise_results.filter((bug: any) => this.getBugStatus(bug) === 'partial').length;
  }

  // Expandable sections state
  expandedSections = {
    bugResults: false
  };
}
