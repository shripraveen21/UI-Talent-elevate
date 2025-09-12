import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-employee-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './employee-dashboard.component.html',
  styleUrls: ['./employee-dashboard.component.css']
})
export class EmployeeDashboardComponent implements OnInit {
  userName: string = '';
  assessments: any[] = [];
  progressData: any = {};
  recommendedSkills: any[] = [];
  loading: boolean = false;

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadAssessments();
    this.loadProgressData();
    this.loadRecommendedSkills();
  }

  loadUserData(): void {
    // Placeholder for user data loading
    this.userName = 'Employee User';
  }

  navigateToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  loadAssessments(): void {
    // Placeholder for assessments data loading
    this.loading = true;
    // TODO: Connect to backend service
    setTimeout(() => {
      this.assessments = [];
      this.loading = false;
    }, 1000);
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

  startAssessment(assessmentId: string): void {
    this.router.navigate(['/test', assessmentId]);
  }

  viewProgress(): void {
    // Navigate to detailed progress view
    console.log('View detailed progress');
  }

  exploreSkill(skillId: string): void {
    // Navigate to skill details or learning resources
    console.log('Explore skill:', skillId);
  }
}