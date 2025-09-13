import { Component, NgModule, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastService } from '../../services/toast/toast.service';
import { LoginService } from '../../services/login/login.service';

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.css'],
  imports: [CommonModule, FormsModule]
})

export class TestComponent implements OnInit, OnDestroy {
  testId!: number;
  testDetails: any;
  answers: any = {};
  loading = true;
  error = '';
  submitted = false;
  timer: number = 0;
  interval: any;
  startTime: Date = new Date();
  
  // Dynamic properties for test display (matching MCQ quiz)
  testTitle: string = 'Test Assessment';
  testDescription: string = 'Multiple Choice Questions Assessment';
  timeRemaining: number = 0; // in seconds
  timeDisplay: string = '00:00';
  private timerInterval?: number;
  
  // User information
  currentUserName: string = '';
  warningShown: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private dashboardService: DashboardService,
    private router: Router,
    private toastService: ToastService,
    private loginService: LoginService
  ) {}

  ngOnInit(): void {
    this.testId = Number(this.route.snapshot.paramMap.get('id'));
    this.startTime = new Date();
    
    // Get current user's name
    this.getCurrentUserName();
    
    // Redirect to results page if auto-submitted on refresh
    if (localStorage.getItem('testAutoSubmitted') === 'true') {
      localStorage.removeItem('testAutoSubmitted');
      this.router.navigate(['/results', this.testId]);
      return;
    }
    // Add beforeunload handler to auto-submit on refresh/close
    window.addEventListener('beforeunload', this.handleBeforeUnload);

    const token = localStorage.getItem('token');
    if (token && this.testId) {
      // First, check if the user has already attempted the test
      this.dashboardService.getTestResults(this.testId, token).subscribe({
        next: (resultData) => {
          // If result exists, redirect to results page
          this.router.navigate(['/results', this.testId]);
        },
        error: () => {
          // If no result, proceed to load test details
          this.dashboardService.getTestDetails(this.testId, token).subscribe({
            next: (data) => {
              // Map backend fields to frontend expectations
              this.testDetails = {
                test_name: data.test_name,
                test_duration: data.test_duration,
                questions: Object.entries(data.test_data || {}).map(([id, q]) => {
                  const questionObj = q as any;
                  return {
                    id,
                    text: questionObj.question,
                    type: questionObj.options ? 'multiple_choice' : 'text',
                    options: questionObj.options
                      ? Object.entries(questionObj.options).map(([key, value]) => ({ key, value }))
                      : undefined
                  };
                })
              };
              
              // Set dynamic title and description
              this.testTitle = data.test_name || 'Test Assessment';
              this.testDescription = 'Multiple Choice Questions Assessment';
              
              this.loading = false;
              
              // Calculate remaining time using started_at from backend
              const startedAt = data.started_at ? new Date(data.started_at) : new Date();
              const now = new Date();
              const elapsed = Math.floor((now.getTime() - startedAt.getTime()) / 1000); // seconds
              // Parse "MM:SS" string to seconds
              function parseDuration(durationStr: string): number {
                const [minutes, seconds] = durationStr.split(':').map(Number);
                return minutes * 60 + seconds;
              }

              const durationSeconds = parseDuration(data.test_duration);
              const remaining = Math.max(durationSeconds - elapsed, 0);
              this.timer = remaining;
              this.timeRemaining = remaining;
              this.updateTimeDisplay();
              this.startNewTimer();
            },
            error: (err) => {
              this.error = 'Failed to load test details';
              this.loading = false;
            }
          });
        }
      });
    } else {
      this.error = 'Test or authentication info missing';
      this.loading = false;
    }
  }

  ngOnDestroy(): void {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    clearInterval(this.interval);
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }

  // Get current user's name
  getCurrentUserName(): void {
    const user = this.loginService.getCurrentUser();
    if (user && user.name) {
      this.currentUserName = user.name;
    } else {
      this.currentUserName = 'User'; // Fallback if name is not available
    }
  }

  // New timer functionality matching MCQ quiz
  startNewTimer() {
    this.updateTimeDisplay();
    
    this.timerInterval = window.setInterval(() => {
      this.timeRemaining--;
      this.timer = this.timeRemaining; // Keep old timer for compatibility
      this.updateTimeDisplay();
      
      // Show warning at 1 minute remaining
      if (this.timeRemaining === 60 && !this.warningShown) {
        this.toastService.showWarning('⚠️ 1 minute left, please finish your test!');
        this.warningShown = true;
      }
      
      if (this.timeRemaining <= 0) {
        this.stopNewTimer();
        this.onTimeUp();
      }
    }, 1000);
  }

  stopNewTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = undefined;
    }
  }

  updateTimeDisplay() {
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    this.timeDisplay = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  onTimeUp() {
    // Handle when time runs out
    this.toastService.showError('Time is up! Auto-submitting your test...');
    this.submit();
  }

  handleBeforeUnload = (event: BeforeUnloadEvent) => {
    if (!this.submitted && this.timer > 0) {
      this.submit();
      // Set flag to redirect after refresh
      localStorage.setItem('testAutoSubmitted', 'true');
      event.preventDefault();
      event.returnValue = '';
    }
  };

  startTimer() {
    this.interval = setInterval(() => {
      if (this.timer > 0) {
        this.timer--;
      } else {
        clearInterval(this.interval);
        this.submit();
      }
    }, 1000);
  }

  handleAnswer(questionId: string, value: any) {
    this.answers[questionId] = value;
  }

  submit() {
    if (this.submitted) return; // Prevent double submission
    clearInterval(this.interval);
    this.stopNewTimer(); // Stop the new timer
    this.submitted = true;
    const token = localStorage.getItem('token');
    // Send start_time in ISO format
    this.dashboardService.submitTestAnswers(
      this.testId,
      { answers: this.answers, start_time: this.startTime.toISOString() },
      token!
    ).subscribe({
      next: () => {
        this.router.navigate(['/results', this.testId]);
      },
      error: () => {
        this.error = 'Failed to submit answers';
        this.submitted = false;
      }
    });
  }

  formatTimer(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  // Helper method to get answered questions count
  getAnsweredQuestionsCount(): number {
    return Object.keys(this.answers).length;
  }

  // Helper method to get progress percentage
  getProgressPercentage(): number {
    if (!this.testDetails || !this.testDetails.questions) {
      return 0;
    }
    const totalQuestions = this.testDetails.questions.length;
    const answeredQuestions = this.getAnsweredQuestionsCount();
    return totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
  }
}
