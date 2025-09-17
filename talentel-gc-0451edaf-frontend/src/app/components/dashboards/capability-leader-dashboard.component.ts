import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TopicsService } from '../../services/topics/topics.service';
import { TestListingService } from '../../services/test-listing/test-listing.service';
import { SuggestionComponent } from '../suggestion/suggestion.component';

@Component({
  selector: 'app-capability-leader-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, SuggestionComponent],
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

  constructor(
    private router: Router,
    private topicsService: TopicsService,
    private assessmentsService: TestListingService
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadTopics();
    this.loadAssessments();
    this.loadTeamOverview();

        const userInfo = localStorage.getItem('user'); // Optional: store user info at login

    if (userInfo) {
      const user = JSON.parse(userInfo);
      this.userName = user.name || '';
    }
  }

  navigateToCollaborators() {
    this.router.navigate(['/manage-collaborator']);
  }

  loadUserData(): void {
    this.userName = 'Capability Leader';
  }

  loadTopics(): void {
    this.loading = true;
    this.topicsService.getTopics().subscribe({
      next: (topics) => {
        this.topics = topics;
        this.loading = false;
      },
      error: () => {
        this.topics = [];
        this.loading = false;
      }
    });
  }

  loadAssessments(): void {
    this.assessmentsService.getAssessments().subscribe({
      next: (assessments) => {
        this.assessments = assessments;
      },
      error: () => {
        this.assessments = [];
      }
    });
  }

  loadTeamOverview(): void {
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
    this.router.navigate(['/add-techstack']);
  }

  editTopic(topicId: string): void {
    console.log('Edit topic:', topicId);
  }

  deleteTopic(topicId: string): void {
    console.log('Delete topic:', topicId);
  }

  createAssessment(): void {
    console.log('Create new assessment');
  }

  editAssessment(assessmentId: string): void {
    console.log('Edit assessment:', assessmentId);
  }

  viewAssessmentResults(assessmentId: string): void {
    console.log('View assessment results:', assessmentId);
  }

  viewTeamDetails(): void {
    console.log('View team details');
  }

  exportReports(): void {
    console.log('Export reports');
  }

  navigateToFeedback() : void {
    this.router.navigate(['/feedback']);
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
    console.log('View topic details:', topicId);
  }

  navigateToDirectory(): void {
    this.router.navigate(['/directory']);
  }
}
