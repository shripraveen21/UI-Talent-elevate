import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { CommonModule } from '@angular/common';
import { BackButtonComponent } from '../shared/backbutton/backbutton.component';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css'],
  imports: [CommonModule,BackButtonComponent]
})
export class ResultsComponent implements OnInit {
  userName: string = '';
  userId: string = '';
  testId!: number;
  result: any;
  feedback: any;
  resources: any[] = [];
  loading = true;
  error = '';
  pending = false;
  
  expandedSections = {
  topicPerformance: false,   // default expanded
  strengths: false,
  weaknesses: false,
  resources: false
};

  employeeLogin : Boolean = true;

toggleSection(section: keyof typeof this.expandedSections) {
  this.expandedSections[section] = !this.expandedSections[section];
}


  constructor(
    private route: ActivatedRoute,
    private router : Router,
    private dashboardService: DashboardService
  ) {}

  ngOnInit(): void {
    const userObj = localStorage.getItem('user');
    let userName = 'User';
    let userId = '';
    if (userObj) {
      try {
        const user = JSON.parse(userObj);
        console.log(user,"user")
        userName = user.name || 'User';
        userId = user.user_id || '';
      } catch {
        userName = userObj || 'User';
        userId = '';
      }
    }
    this.userName = userName;
    this.userId = userId;
    this.testId = Number(this.route.snapshot.paramMap.get('id'));
    console.log(this.testId,"got the id")
    const token = localStorage.getItem('token');
    if (token && this.testId) {
      this.dashboardService.getTestResults(this.testId, token).subscribe({
        next: (data) => {
          this.result = data;
          this.loading = false;
          console.log(1)

          // Fetch test details to check if logged-in employee is the creator
          this.dashboardService.getTestDetails(this.testId, token).subscribe({
            next: (testDetails) => {
              console.log(testDetails,"test")
              const creator = testDetails.created_by;
              console.log(creator,"hekk",this.userId)
              this.employeeLogin = (creator === this.userId);
              console.log(this.employeeLogin,"hekk213")

            },
            error: (err) => {
              this.employeeLogin = false;
            }
          });

          // Get feedback using result_id from backend response
          if (data.result_id) {
            this.dashboardService.getTestFeedback(data.result_id, token).subscribe({
              next: (fb) => {
                this.feedback = fb;
                if (fb && fb.resources) {
                  this.resources = fb.resources;
                } else {
                  this.resources = [];
                }
              },
              error: () => {
                this.feedback = { error: 'Failed to load feedback analysis' };
              }
            });
          }
        },
        error: (err) => {
          if (err.status === 404) {
            this.pending = true;
            this.loading = false;
          } else {
            this.error = 'Failed to load test results';
            this.loading = false;
          }
        }
      });
    } else {
      this.error = 'Test or authentication info missing';
      this.loading = false;
    }
  }

  // Helper methods for the new UI
  getScorePercentage(): number {
    if (this.feedback?.quiz_result?.score_percentage) {
      return this.feedback.quiz_result.score_percentage;
    }
    return 0;
  }

  returnToDashboard(): void {
    this.router.navigate(['/manager-dashboard']);
}

  getGrade(): string {
    const score = this.getScorePercentage();
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  getCorrectAnswers(): number {
    if (this.feedback?.quiz_result?.correct_answers) {
      return this.feedback.quiz_result.correct_answers;
    }
    return 0;
  }

  getTotalQuestions(): number {
    if (this.feedback?.quiz_result?.total_questions) {
      return this.feedback.quiz_result.total_questions;
    }
    return 0;
  }

  // Get all analysis topics
  getAnalysis(): any[] {
    if (this.feedback?.analysis && Array.isArray(this.feedback.analysis)) {
      return this.feedback.analysis;
    }
    return [];
  }

  // Get topics categorized as strengths
  getStrengths(): any[] {
    return this.getAnalysis().filter(topic => topic.status === 'strength');
  }

  // Get topics categorized as weaknesses
  getWeaknesses(): any[] {
    return this.getAnalysis().filter(topic => topic.status === 'weakness');
  }

  // Get topic performance summary
  getTopicSummary(): any[] {
    return this.getAnalysis().map(topic => ({
      ...topic,
      totalQuestions: topic.score.correct + topic.score.incorrect,
      percentage: Math.round((topic.score.correct / (topic.score.correct + topic.score.incorrect)) * 100) || 0
    }));
  }

  // Get overall statistics
  getOverallStats() {
    const analysis = this.getAnalysis();
    const totalTopics = analysis.length;
    const strengthTopics = this.getStrengths().length;
    const weaknessTopics = this.getWeaknesses().length;
    
    return {
      totalTopics,
      strengthTopics,
      weaknessTopics,
      strengthPercentage: totalTopics > 0 ? Math.round((strengthTopics / totalTopics) * 100) : 0
    };
  }

  // Get resources for weak topics
  getRecommendedResources(): any[] {
    if (this.feedback?.resources && Array.isArray(this.feedback.resources)) {
      return this.feedback.resources;
    }
    return [];
  }
}
