import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { DashboardService } from '../../services/testAttempt/dashboard.service';

@Component({
  selector: 'app-employee-dashboard',
  standalone: true,
  imports: [CommonModule, DashboardComponent],
  templateUrl: './employee-dashboard.component.html',
  styleUrls: ['./employee-dashboard.component.css']
})
export class EmployeeDashboardComponent implements OnInit {
  userName: string = '';
  progressData: any = {};
  recommendedSkills: any[] = [];
  

  assignedTests: any[] = [];
    loading = true;
    error = '';
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
        this.loadUserData();
        this.loadProgressData();
        this.loadRecommendedSkills();
        
        this.dashboardService.getAssignedTests(token).subscribe({
          next: (data: any[]) => {
            
            this.assignedTests = data;
            this.loading = false;
          },
          error: () => {
            
            this.error = 'Failed to load assigned tests';
            this.loading = false;
          }
        });
      } else {
        this.error = 'User not authenticated';
        this.loading = false;
      }
    }

  loadUserData(): void {
    // Placeholder for user data loading
    this.userName = 'Employee User';
  }

  navigateToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  roundPercent(): number {
    const completed = this.getCompletedTestsCount();
    const pending = this.getPendingTestsCount();
    return Math.round((completed * 100) / (completed + pending) * 10) / 10;
  }


  getCompletedTestsCount(): number {
    return this.assignedTests.filter(test => test.attempted).length;
  }

  getPendingTestsCount(): number {
    return this.assignedTests.filter(test => !test.attempted).length;
  }

  getDebugTestsCount(): number {
    return this.assignedTests.filter(test => test.debug_test_id).length;
  }

  loadProgressData(): void {
    // Placeholder for progress data loading
    // TODO: Connect to backend service
    this.progressData = {};
  }

  loadRecommendedSkills(): void {
    // Placeholder for recommended skills loading
    // TODO: Connect to backend service
    this.recommendedSkills = [];
  }

  viewProgress(): void {
    // Navigate to detailed progress view
    console.log('View detailed progress');
  }

  exploreSkill(skillId: string): void {
    // Navigate to skill details or learning resources
    console.log('Explore skill:', skillId);
  }

  navigateToSkillUpgrade(): void {
    this.router.navigate(['/skill-upgrade']);
  }


}