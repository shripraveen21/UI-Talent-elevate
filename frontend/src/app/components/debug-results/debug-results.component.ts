import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-debug-results',
  templateUrl: './debug-results.component.html',
  styleUrls: ['./debug-results.component.css'],
  imports: [CommonModule]
})
export class DebugResultsComponent implements OnInit {
  debugTestId!: number;
  result: any = null;
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private dashboardService: DashboardService
  ) {}

  ngOnInit(): void {
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
}
