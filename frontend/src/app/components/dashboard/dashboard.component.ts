import { Component, OnInit } from '@angular/core';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  imports: [CommonModule, FormsModule]
})
export class DashboardComponent implements OnInit {
  assignedTests: any[] = [];
  loading = true;
  error = '';
  userName = '';
  userRole = '';

  constructor(
    private dashboardService: DashboardService,
    private router: Router
  ) {}

ngOnInit(): void {
    const token = localStorage.getItem('token');
    const userInfo = localStorage.getItem('user'); // Optional: store user info at login

    if (userInfo) {
      const user = JSON.parse(userInfo);
      this.userName = user.name || '';
      this.userRole = user.role || '';
    }

    if (token) {
      
      this.dashboardService.getAssignedTests(token).subscribe({
        next: (data: any[]) => {
          
          this.assignedTests = data;
          this.loading = false;
        },
        error: (err) => {
          
          this.error = 'Failed to load assigned tests';
          this.loading = false;
        }
      });
    } else {
      this.error = 'User not authenticated';
      this.loading = false;
    }
  }

  startTest(testId: number): void {
    this.router.navigate(['/test', testId]);
  }

  viewResults(testId: number): void {
    this.router.navigate(['/results', testId]);
  }
}
