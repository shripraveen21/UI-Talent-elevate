import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DashboardComponent } from '../dashboard/dashboard.component';

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
  


  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadUserData();
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