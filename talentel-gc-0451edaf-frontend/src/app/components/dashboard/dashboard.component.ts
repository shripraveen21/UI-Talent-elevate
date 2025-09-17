import { Component, OnInit } from '@angular/core';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ToastService } from '../../services/toast/toast.service';


@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  imports: [CommonModule, FormsModule, ReactiveFormsModule]
})
export class DashboardComponent implements OnInit {
  assignedTests: any[] = [];
  loading = true;
  error = '';
  userName = '';
  userRole = '';

  constructor(
    private dashboardService: DashboardService,
    private router: Router,
    private toastService: ToastService
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
          console.log(this.assignedTests)
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

  
  startTest(test: any): void {
    console.log(test)
    if (test.quiz_id) {
      this.router.navigate(['/test', test.test_id]);
    } else if (test.debug_test_id) {
      console.log("debug")
      this.router.navigate(['/debug-test', test.debug_test_id]);
    } else {
      // Fallback: show error or do nothing
      console.log("no test")
      this.toastService?.showError?.('No available test type for this assignment.');
    }
  }

  viewResults(testId: number): void {
    this.router.navigate(['/results', testId]);
  }
  startDebugTest(test: any): void {
    if (test.debug_attempted) {
      alert('You have already attempted this debug test. Access is not allowed.');
      return;
    }
    this.router.navigate(['/debug-test', test.debug_test_id]);
  }
  
  viewDebugResults(debugTestId: number): void {
    this.router.navigate(['/debug-results', debugTestId]);
  }

  // Helper methods for stats cards
  getCompletedTestsCount(): number {
    return this.assignedTests.filter(test => test.attempted).length;
  }

  getPendingTestsCount(): number {
    return this.assignedTests.filter(test => !test.attempted).length;
  }

  getDebugTestsCount(): number {
    return this.assignedTests.filter(test => test.debug_test_id).length;
  }
}