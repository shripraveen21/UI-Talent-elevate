import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MarkdownModule } from 'ngx-markdown';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';

@Component({
  selector: 'app-handson-result',
  templateUrl: './handson-result.component.html',
  styleUrls: ['./handson-result.component.css'],
  standalone: true,
  imports: [CommonModule, MarkdownModule]
})
export class HandsonResultComponent implements OnInit {
  result: any = null;
  loading = true;
  error = '';
  handsonId!: number;

  constructor(
    private sanitizer: DomSanitizer,
    private route: ActivatedRoute,
    private router: Router,
    private dashboardService: DashboardService
  ) {}

  ngOnInit(): void {
    this.handsonId = Number(this.route.snapshot.paramMap.get('id'));
    const token = localStorage.getItem('token');
    if (token && this.handsonId) {
      this.dashboardService.getHandsonResult(this.handsonId, token).subscribe({
        next: (data) => {
          if (data.pending) {
            this.result = null;
            this.loading = false;
            return;
          }
          console.log(data,"dataa")
          this.result = data.feedback_data;
          this.loading = false;
        },
        error: () => {
          this.error = 'Failed to load handson result data';
          this.loading = false;
        }
      });
    } else {
      this.error = 'Handson or authentication info missing';
      this.loading = false;
    }
  }

  /**
   * Returns the overall score, or null if not present.
   */
  getOverallScore(): number | null {
    if (this.result && typeof this.result.overall_score === 'number') {
      return this.result.overall_score;
    }
    return null;
  }

  /**
   * Returns the overall rating for a given key, or null if not present.
   * @param key Rating key (e.g., 'completeness')
   */
  getRating(key: string): number | null {
    if (
      this.result &&
      this.result.overall_ratings &&
      typeof this.result.overall_ratings[key] === 'number'
    ) {
      return this.result.overall_ratings[key];
    }
    return null;
  }

  /**
   * Returns the list of milestone evaluations, or empty array if not present.
   */
  getMilestones(): any[] {
    if (this.result && Array.isArray(this.result.milestone_evaluations)) {
      return this.result.milestone_evaluations;
    }
    return [];
  }

  /**
   * Returns the milestone rating for a given key, or null if not present.
   * @param milestone Milestone object
   * @param key Rating key
   */
  getMilestoneRating(milestone: any, key: string): number | null {
    if (
      milestone &&
      milestone.ratings &&
      typeof milestone.ratings[key] === 'number'
    ) {
      return milestone.ratings[key];
    }
    return null;
  }

  /**
   * Returns the CSS class for status badge based on score.
   * @param score Numeric score
   */
  getStatusBadgeClass(score: number): string {
    if (typeof score !== 'number') return 'status-fail';
    if (score >= 80) return 'status-pass';
    if (score >= 60) return 'status-partial';
    return 'status-fail';
  }

  /**
   * Returns the icon for the assessment status.
   * @param assessment Assessment string
   */
  getAssessmentIcon(assessment: string): string {
    switch (assessment) {
      case 'CORRECT': return '✅';
      case 'PARTIALLY_CORRECT': return '⚠️';
      case 'INCORRECT': return '❌';
      default: return '📋';
    }
  }

  /**
   * Sanitizes HTML text for safe rendering.
   * @param text Input HTML string
   */
  sanitize(text: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(text);
  }
}
