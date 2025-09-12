import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css'],
  imports: [CommonModule]
})
export class ResultsComponent implements OnInit {
  testId!: number;
  result: any;
  feedback: any;
  resources: any[] = [];
  loading = true;
  error = '';
  pending = false;

  constructor(
    private route: ActivatedRoute,
    private dashboardService: DashboardService
  ) {}

  ngOnInit(): void {
    this.testId = Number(this.route.snapshot.paramMap.get('id'));
    const token = localStorage.getItem('token');
    if (token && this.testId) {
      this.dashboardService.getTestResults(this.testId, token).subscribe({
        next: (data) => {
          this.result = data;
          this.loading = false;
          // Get feedback using result_id from backend response
          if (data.result_id) {
            this.dashboardService.getTestFeedback(data.result_id, token).subscribe({
              next: (fb) => {
                this.feedback = fb;
                if (fb && fb.resources) {
                  this.resources = fb.resources;
                } else {
                  this.resources = [];
                }
              },
              error: () => {
                this.feedback = { error: 'Failed to load feedback analysis' };
              }
            });
          }
        },
        error: (err) => {
          if (err.status === 404) {
            this.pending = true;
            this.loading = false;
          } else {
            this.error = 'Failed to load test results';
            this.loading = false;
          }
        }
      });
    } else {
      this.error = 'Test or authentication info missing';
      this.loading = false;
    }
  }
}
