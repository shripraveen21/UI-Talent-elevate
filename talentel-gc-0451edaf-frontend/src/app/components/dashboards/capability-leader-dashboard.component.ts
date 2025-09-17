import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TopicsService } from '../../services/topics/topics.service';
import { TestListingService } from '../../services/test-listing/test-listing.service';

@Component({
  selector: 'app-capability-leader-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
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
  
  // Recent data for dashboard display
  recentTopics: any[] = [];
  recentSuggestions: any[] = [];

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
    this.loadRecentData();

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

  // Load recent data for dashboard display
  loadRecentData(): void {
    // Mock data for recent topics
    this.recentTopics = [
      { id: 1, name: 'React Advanced Patterns', status: 'Active' },
      { id: 2, name: 'System Design Fundamentals', status: 'Active' },
      { id: 3, name: 'Database Optimization', status: 'Active' },
      { id: 4, name: 'API Design Best Practices', status: 'Active' }
    ];

    // Mock data for recent suggestions
    this.recentSuggestions = [
      { 
        id: 1, 
        title: 'Suggestions for You',
        author: 'Tom Clark',
        date: 'Feb 4, 2023, 12:00:00 PM',
        tech: 'Java',
        description: 'Suggest Jane for Python project'
      },
      { 
        id: 2, 
        title: 'Suggestion',
        author: 'Bob Wilson',
        date: 'Feb 2, 2023, 10:00:00 AM',
        tech: 'Python',
        description: 'Bob is suitable for Java debugging'
      },
      { 
        id: 3, 
        title: 'Suggestion',
        author: 'Jane Smith',
        date: 'Feb 1, 2023, 09:00:00 AM',
        tech: 'Python',
        description: 'Suggest Jane for Python project'
      }
    ];
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

  // Navigation methods for dashboard action cards
  navigateToTopics(): void {
    // Navigate to add-techstack route for managing topics/tech stacks
    this.router.navigate(['/add-techstack']);
  }

  navigateToAssessments(): void {
    // Navigate to create-assessment route for building assessments
    this.router.navigate(['/create-assessment']);
  }

  navigateToAssignTests(): void {
    // Navigate to directory route for assigning tests to team members
    this.router.navigate(['/directory']);
  }

  navigateToFeedback(): void {
    // Navigate to feedback route for viewing feedback and suggestions
    this.router.navigate(['/feedback']);
  }
}
