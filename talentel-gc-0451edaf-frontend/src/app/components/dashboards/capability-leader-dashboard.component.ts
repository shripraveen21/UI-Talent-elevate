import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TopicsService } from '../../services/topics/topics.service';
import { TestListingService } from '../../services/test-listing/test-listing.service';
import { SuggestionComponent } from '../suggestion/suggestion.component';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';

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
  
  // Recent data for dashboard display
  recentTopics: any[] = [];
  recentSuggestions: any[] = [];
  recentTechStacks: any[] = [];

  constructor(
    private router: Router,
    private topicsService: TopicsService,
    private assessmentsService: TestListingService,
    private techStackAgentService: TechStackAgentService
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadTopics();
    this.loadAssessments();
    this.loadTeamOverview();
    this.loadRecentData();

    // Fetch recent tech stacks from service
    this.techStackAgentService.getCapabilityLeaderId().subscribe({
  next: (leaderId) => {
    this.techStackAgentService.getCollaborators().subscribe({
      next: (collaborators) => {
        // Build allowed user IDs: leader + collaborators
        const allowedUserIds: number[] = [];
        if (leaderId !== null && !isNaN(Number(leaderId))) {
          allowedUserIds.push(Number(leaderId));
        }
        collaborators.forEach((collab: any) => {
          if (collab.collaborator_id !== null && !isNaN(Number(collab.collaborator_id))) {
            allowedUserIds.push(Number(collab.collaborator_id));
          }
        });
        this.techStackAgentService.getTechStacks().subscribe({
          next: (techStacks) => {
            const stacks = Array.isArray(techStacks)
              ? techStacks
              : (techStacks?.data || []);
            // Filter tech stacks by allowed user IDs (all numbers)
            this.recentTechStacks = stacks.filter(
              (stack: any) => allowedUserIds.includes(Number(stack.created_by))
            );
          },
          error: () => {
            this.recentTechStacks = [];
          }
        });
      },
      error: () => {
        // If collaborator fetch fails, fallback to only leader's tech stacks
        this.techStackAgentService.getTechStacks().subscribe({
          next: (techStacks) => {
            const stacks = Array.isArray(techStacks)
              ? techStacks
              : (techStacks?.data || []);
            this.recentTechStacks = stacks.filter(
              (stack: any) => stack.created_by === leaderId
            );
          },
          error: () => {
            this.recentTechStacks = [];
          }
        });
      }
    });
  },
  error: () => {
    // If leaderId fetch fails, fallback to only collaborators
    this.techStackAgentService.getCollaborators().subscribe({
      next: (collaborators) => {
        const allowedUserIds: number[] = [];
        collaborators.forEach((collab: any) => {
          if (collab.collaborator_id !== null && !isNaN(Number(collab.collaborator_id))) {
            allowedUserIds.push(Number(collab.collaborator_id));
          }
        });
        this.techStackAgentService.getTechStacks().subscribe({
          next: (techStacks) => {
            const stacks = Array.isArray(techStacks)
              ? techStacks
              : (techStacks?.data || []);
            this.recentTechStacks = stacks.filter(
              (stack: any) => allowedUserIds.includes(Number(stack.created_by))
            );
          },
          error: () => {
            this.recentTechStacks = [];
          }
        });
      },
      error: () => {
        this.recentTechStacks = [];
      }
    });
  }
});

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

  viewTopicDetails(topicId: string, techStackName: string): void {
    this.router.navigate(['/updateTopics', topicId], { queryParams: { name: techStackName } });
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
