import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-delivery-manager-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './delivery-manager-dashboard.component.html',
  styleUrls: ['./delivery-manager-dashboard.component.css']
})
export class DeliveryManagerDashboardComponent implements OnInit {
  userName: string = '';
  teams: any[] = [];
  projects: any[] = [];
  readinessReports: any[] = [];
  progressData: any = {};
  loading: boolean = false;
  activeTab: string = 'teams';

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadTeams();
    this.loadProjects();
    this.loadProgressData();
    this.loadReadinessReports();

        const userInfo = localStorage.getItem('user'); // Optional: store user info at login

    if (userInfo) {
      const user = JSON.parse(userInfo);
      this.userName = user.name || '';
    }
  }

  loadUserData(): void {
    // Placeholder for user data loading
    this.userName = 'Delivery Manager';
  }

  loadTeams(): void {
    // Placeholder for teams data loading
    this.loading = true;
    // TODO: Connect to backend service
    setTimeout(() => {
      this.teams = [];
      this.loading = false;
    }, 1000);
  }

  loadProjects(): void {
    // Placeholder for projects data loading
    // TODO: Connect to backend service
    this.projects = [];
  }

  loadProgressData(): void {
    // Placeholder for progress data loading
    // TODO: Connect to backend service
    this.progressData = {
      totalTeams: 0,
      activeProjects: 0,
      readyTeams: 0,
      overallReadiness: 0
    };
  }

  loadReadinessReports(): void {
    // Placeholder for readiness reports loading
    // TODO: Connect to backend service
    this.readinessReports = [];
  }

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }

  assignTeamToProject(teamId: string): void {
    // Open team assignment modal or navigate to assignment page
    console.log('Assign team to project:', teamId);
  }

  createTeam(): void {
    // Navigate to team creation form
    console.log('Create new team');
  }

  editTeam(teamId: string): void {
    // Navigate to team edit form
    console.log('Edit team:', teamId);
  }

  viewTeamDetails(teamId: string): void {
    // Navigate to detailed team view
    console.log('View team details:', teamId);
  }

  trackProjectProgress(projectId: string): void {
    // Navigate to project progress tracking
    console.log('Track project progress:', projectId);
  }

  generateReadinessReport(): void {
    // Generate new readiness report
    console.log('Generate readiness report');
  }

  viewReport(reportId: string): void {
    // View detailed readiness report
    console.log('View report:', reportId);
  }

  exportReport(reportId: string): void {
    // Export readiness report
    console.log('Export report:', reportId);
  }

  escalateIssue(teamId: string): void {
    // Escalate team readiness issues
    console.log('Escalate issue for team:', teamId);
  }

  navigateToMcqQuiz(): void {
    this.router.navigate(['/mcq-quiz']);
  }

  navigateToDebugExercise(): void {
    this.router.navigate(['/debug-exercise']);
  }

  navigateToDirectory(): void {
    console.log("/directory")
    this.router.navigate(['/directory']);
  }

  navigateToAssessments(): void {
    this.router.navigate(['/create-assessment']);
  }

  navigateToAssignTests(): void {
    this.router.navigate(['/directory']);
  }

  navigateToFeedback(): void {
    this.router.navigate(['/feedback']);
  }
}
