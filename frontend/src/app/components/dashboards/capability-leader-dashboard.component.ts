import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-capability-leader-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './capability-leader-dashboard.component.html',
  styleUrls: ['./capability-leader-dashboard.component.css']
})
export class CapabilityLeaderDashboardComponent implements OnInit {
  userName: string = '';
  topics: any[] = [];
  assessments: any[] = [];
  teamOverview: any = {};
  loading: boolean = false;
  activeTab: string = 'topics';

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadTopics();
    this.loadAssessments();
    this.loadTeamOverview();
  }

  loadUserData(): void {
    // Placeholder for user data loading
    this.userName = 'Capability Leader';
  }

  loadTopics(): void {
    // Placeholder for topics data loading
    this.loading = true;
    // TODO: Connect to backend service
    setTimeout(() => {
      this.topics = [];
      this.loading = false;
    }, 1000);
  }

  loadAssessments(): void {
    // Placeholder for assessments data loading
    // TODO: Connect to backend service
    this.assessments = [];
  }

  loadTeamOverview(): void {
    // Placeholder for team overview data loading
    // TODO: Connect to backend service
    this.teamOverview = {
      totalEmployees: 0,
      activeAssessments: 0,
      completionRate: 0,
      averageScore: 0
    };
  }

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }

  createTopic(): void {
    // Navigate to topic creation form
    this.router.navigate(['/add-techstack']);
  }

  editTopic(topicId: string): void {
    // Navigate to topic edit form
    console.log('Edit topic:', topicId);
  }

  deleteTopic(topicId: string): void {
    // Delete topic with confirmation
    console.log('Delete topic:', topicId);
  }

  createAssessment(): void {
    // Navigate to assessment creation form
    console.log('Create new assessment');
  }

  editAssessment(assessmentId: string): void {
    // Navigate to assessment edit form
    console.log('Edit assessment:', assessmentId);
  }

  viewAssessmentResults(assessmentId: string): void {
    // Navigate to assessment results view
    console.log('View assessment results:', assessmentId);
  }

  viewTeamDetails(): void {
    // Navigate to detailed team view
    console.log('View team details');
  }

  exportReports(): void {
    // Export team reports
    console.log('Export reports');
  }

  navigateToCreateTopic(): void {
    this.router.navigate(['/add-techstack']);
  }

  navigateToMcqQuiz(): void {
    this.router.navigate(['/mcq-quiz']);
  }

  navigateToDebugExercise(): void {
    this.router.navigate(['/debug-exercise']);
  }

  viewTopicDetails(topicId: string): void {
    // Navigate to topic details view
    console.log('View topic details:', topicId);
  }
}