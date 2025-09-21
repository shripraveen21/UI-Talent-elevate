import { Component, OnInit } from '@angular/core';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ToastService } from '../../services/toast/toast.service';

import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { TestListingService } from '../../services/test-listing/test-listing.service';
import { SkillUpgradeService } from '../../services/skill-upgrade.service';



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
  token: string = '';
  userId: any = ''; // Added userId property
  testDropdownSelections: string[] = []; // Tracks dropdown selection for each test

  constructor(
    private dashboardService: DashboardService,
    private router: Router,
    private toastService: ToastService,
    private skillUpgradeService: SkillUpgradeService,
    private testListingService: TestListingService
  ) { }
    



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

      // update status as completed
      await this.dashboardService.markHandsonCompleted(test.handson_id).toPromise();

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
    // Get token from localStorage, fallback to empty string if not found
    this.token = localStorage.getItem('token') || '';
    const userInfo = localStorage.getItem('user'); // Optional: store user info at login

    if (userInfo) {
      const user = JSON.parse(userInfo);
      this.userName = user.name || '';
      this.userRole = user.role || '';
      this.userId = user.user_id || ''; 
    }

    if (this.token) {
      this.dashboardService.getAssignedTests(this.token).subscribe({
        next: (data: any[]) => {
          this.assignedTests = data;
          this.testDropdownSelections = data.map(() => 'Quiz'); // Default selection is 'Quiz'
          console.log(this.assignedTests, "m");
          this.loading = false;

          this.assignedTests.forEach(test => {
            this.testListingService.getTestSubmitStatus(test.test_id).subscribe({
              next: (status) => {
                test.quiz_isSubmitted = status.quiz_isSubmitted;
                test.debug_isSubmitted = status.debug_isSubmitted;
                test.handson_isSubmitted = status.handson_isSubmitted;
              },
              error: (err) => {
                // If error, default to false
                test.quiz_isSubmitted = false;
                test.debug_isSubmitted = false;
                test.handson_isSubmitted = false;
              }
            });
          });
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

  // checkTestCompleteStatus(testId: number, type: string): boolean {
    
  //         this.testListingService.getTestSubmitStatus(testId).subscribe({
  //           next: (status) => {
  //             switch (type) {
  //               case 'Quiz':
  //                 return status.quiz_isSubmitted;
  //               case 'Debug':
  //                 return status.debug_isSubmitted;
  //               case 'Handson':
  //                 console.log(status.handson_isSubmitted,"handson stauts")
  //                 return status.handson_isSubmitted;
  //               default:
  //                 return false;
  //             }
  //           },
  //           error: (err) => {
  //             return false;
  //           }
  //         });
  //         return false
        
        
  // }


  checkTestOwner(test_id: number,): import('rxjs').Observable<boolean> {
    return this.dashboardService.getTestDetails(test_id, this.token).pipe(
      // Map the API response to a boolean
      map((testDetails: any) => {
        const creator = testDetails.created_by;
        return creator === this.userId;
      }),
      // On error, return false
      catchError(() => of(false))
    );
  }


  checkTestCompleteStatus(test_id: number, type: string): boolean {
    const test = this.assignedTests.find(t => t.test_id === test_id);
    if (!test) return false;
    if (type === 'Quiz') {
      return !test.quiz_isSubmitted;
    } else if (type === 'Debug') {
      return !test.debug_isSubmitted;
    } else if (type === 'Handson') {
      return !test.handson_isSubmitted;
    }
    return false;
  }

  startTest(test: any): void {
    if (test.quiz_id) {
      this.router.navigate(['/test', test.test_id]);
    } else {
      this.toastService?.showError?.('No available quiz for this assignment.');
    }
  }

  navigateToQuizResults(quizId: number): void {
    this.router.navigate(['/results', quizId]);
  }

  navigateToDebugResults(debugId: number): void {
    this.router.navigate(['/debug-results', debugId]);
  }

  navigateToHandsOnResults(handsonId: number): void {
    this.router.navigate(['/handson-result', handsonId]);
  }

  dueDateOver(test: any): boolean {
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

  // Skill Upgrade Completion Logic
  async markSkillUpgradeComplete(test: any): Promise<void> {
    try {
      const testId = test.test_id;
      const employeeId = JSON.parse(localStorage.getItem('user') || '{}').id;
      const token = localStorage.getItem('token') || '';

      // Call backend endpoint to complete skill upgrade
      await this.skillUpgradeService.completeSkillUpgrade(token, testId).toPromise();

      this.toastService?.showSuccess?.('Skill upgrade completion requested. The backend will process your request.');
    } catch (error: any) {
      this.toastService?.showError?.('Error processing skill upgrade completion.');
      console.error(error);
    }
  }
}
