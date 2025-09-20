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
  testDropdownSelections: string[] = []; // Tracks dropdown selection for each test

  constructor(
    private dashboardService: DashboardService,
    private router: Router,
    private toastService: ToastService
  ) {}


  async markDebugCompleted(test: any): Promise<void> {
    try {
      test.debugCompleted = true;

      // Call evaluation endpoint
      const test_id = test.test_id;
      if (!test_id) {
        this.toastService?.showError?.('Debug ID not found.');
        return;
      }

      // Call the service method (to be implemented in DashboardService)
      await this.dashboardService.evaluateDebugTest(test_id).toPromise();

      test.debugSubmitted = true;

      console.log(JSON.stringify({
        level: 'INFO',
        message: 'Debug test marked as completed and submitted for evaluation',
        testId: test_id,
        githubUrl: test.debugGithubUrl || test.debug_url,
        timestamp: new Date().toISOString()
      }));

      this.toastService?.showSuccess?.('Submitted for evaluation');

    } catch (error: any) {
      console.error(JSON.stringify({
        level: 'ERROR',
        message: 'Failed to submit Debug test for evaluation',
        error: error?.message || error,
        testId: test.test_id,
        timestamp: new Date().toISOString()
      }));
      this.toastService?.showError?.('Error submitting Debug test for evaluation.');
    }
  }

 
  async markHandsonCompleted(test: any): Promise<void> {
    try {
      test.handsonCompleted = true;

      // Call evaluation endpoint
      const test_id = test.test_id;
      if (!test_id) {
        this.toastService?.showError?.('Handson ID not found.');
        return;
      }

      // Call the service method (to be implemented in DashboardService)
      await this.dashboardService.evaluateHandsonTest(test_id).toPromise();

      test.handsonSubmitted = true;

      console.log(JSON.stringify({
        level: 'INFO',
        message: 'Handson test marked as completed and submitted for evaluation',
        testId: test_id,
        githubUrl: test.handsonGithubUrl || test.handson_url,
        timestamp: new Date().toISOString()
      }));

      this.toastService?.showSuccess?.('Submitted for evaluation');

    } catch (error: any) {
      console.error(JSON.stringify({
        level: 'ERROR',
        message: 'Failed to submit Handson test for evaluation',
        error: error?.message || error,
        testId: test.test_id,
        timestamp: new Date().toISOString()
      }));
      this.toastService?.showError?.('Error submitting Handson test for evaluation.');
    }
  }

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
          this.testDropdownSelections = data.map(() => 'Quiz'); // Default selection is 'Quiz'
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
    if (test.quiz_id) {
      this.router.navigate(['/test', test.test_id]);
    } else {
      this.toastService?.showError?.('No available quiz for this assignment.');
    }
  }

  dueDateOver(test:any) : Boolean {
    return new Date() > new Date(test.due_date);
  }

  getGithubUrl(test: any, type: string): string {
    if (type === 'Debug') {
      return test.debug_url;
    } else if (type === 'Handson') {
      return test.handson_url;
    }
    return '';
  }

  onDropdownChange(index: number, value: string): void {
    this.testDropdownSelections[index] = value;
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
