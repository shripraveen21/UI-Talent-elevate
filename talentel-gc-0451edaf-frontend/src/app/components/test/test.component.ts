import { Component, OnInit, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { DebugTestService } from '../../services/debug-test/debug-test.service';
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
  @ViewChild('testContainer', { static: true }) testContainer!: ElementRef;

  // UI state
  showFullscreenModal = false;
  showStartModal = true;
  showAlreadyAttendedModal = false; // Modal for already attended test
  loading = true;
  error = '';
  submitted = false;

  // test metadata & data
  testId!: number;
  testDetails: any;
  answers: any = {};

  // timing
  timeRemaining = 0; // seconds (single timer used)
  timeDisplay = '00:00';
  private timerInterval?: number;

  // other
  debug_id: number | null = null;
  startTime = new Date();
  testTitle = 'Test Assessment';
  testDescription = 'Multiple Choice Questions Assessment';
  currentUserName = '';
  warningShown = false;

  // bound handler so add/remove pair matches
  private fullscreenChangeHandler = this.handleFullscreenChange.bind(this);

  constructor(
    private route: ActivatedRoute,
    private dashboardService: DashboardService,
    private debugTestService: DebugTestService,
    private router: Router,
    private toastService: ToastService,
    private loginService: LoginService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.testId = Number(this.route.snapshot.paramMap.get('id'));
    this.startTime = new Date();
    this.getCurrentUserName();

    // Add beforeunload handler
    window.addEventListener('beforeunload', this.handleBeforeUnload);

    // Use the same handler for add/remove so it can be removed in ngOnDestroy
    document.addEventListener('fullscreenchange', this.fullscreenChangeHandler);

    const token = localStorage.getItem('token');
    if (!token || !this.testId) {
      this.error = 'Test or authentication info missing';
      this.loading = false;
      return;
    }

    if (localStorage.getItem('testAutoSubmitted') === 'true') {
        localStorage.removeItem('testAutoSubmitted');
        this.router.navigate(['/results', this.testId]);
        // if (this.debug_id) {
        //   this.router.navigate(['/debug-test', this.debug_id]);
        // } else {
        //   this.router.navigate(['/employee-dashboard']);
        // }
        return;
      } 
      
      

    // Check if the user has already attempted the test or not
    this.dashboardService.getTestResults(this.testId, token).subscribe({
      next: (resultData) => {
        // If the test status is completed, redirect to results
        if (resultData ) {
          this.router.navigate(['/results', this.testId]);
        } else {
          // Show modal before navigating to employee dashboard
          this.showAlreadyAttendedModal = true;
        }
        this.loading = false;
      },
      error: () => {
        // No prior submission / allowed to take the test -> load test details
        this.loadTestDetails(token);
      }
    });

  }

  ngOnDestroy(): void {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    document.removeEventListener('fullscreenchange', this.fullscreenChangeHandler);
    this.stopTimer();
  }

  getCurrentUserName(): void {
    const user = this.loginService.getCurrentUser();
    if (user && user.name) this.currentUserName = user.name;
    else this.currentUserName = 'User';
  }

  // --- Test details & timing ---
  private loadTestDetails(token: string) {
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
        console.log(this.testDetails,"test details")

        this.testTitle = data.test_name || this.testTitle;
        this.testDescription = 'Multiple Choice Questions Assessment';
        this.loading = false;

        // Calculate remaining time using started_at from backend if available
        const startedAt = data.started_at ? new Date(data.started_at) : new Date();
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - startedAt.getTime()) / 1000);

        const durationSeconds = this.parseDurationToSeconds(data.test_duration);
        const remaining = Math.max(durationSeconds - elapsed, 0);

        this.timeRemaining = remaining;
        this.updateTimeDisplay();
        this.startTimer();
      },
      error: (err) => {
        console.error('Failed to load test details', err);
        this.error = 'Failed to load test details';
        this.loading = false;
      }
    });
  }

  // Accepts "MM:SS" or "HH:MM:SS" or "M:SS" etc.
  private parseDurationToSeconds(durationStr: string): number {
    if (!durationStr || typeof durationStr !== 'string') return 0;
    const parts = durationStr.split(':').map(p => Number(p));
    if (parts.length === 2) {
      // MM:SS
      const [m, s] = parts;
      return (isNaN(m) ? 0 : m) * 60 + (isNaN(s) ? 0 : s);
    } else if (parts.length === 3) {
      // HH:MM:SS
      const [h, m, s] = parts;
      return (isNaN(h) ? 0 : h) * 3600 + (isNaN(m) ? 0 : m) * 60 + (isNaN(s) ? 0 : s);
    } else {
      // fallback: try parse as seconds number
      const n = Number(durationStr);
      return isNaN(n) ? 0 : n;
    }
  }

  private startTimer() {
    this.stopTimer(); // ensure no duplicate interval
    this.timerInterval = window.setInterval(() => {
      this.timeRemaining--;
      this.updateTimeDisplay();

      if (this.timeRemaining === 60 && !this.warningShown) {
        this.toastService.showWarning('⚠️ 1 minute left, please finish your test!');
        this.warningShown = true;
      }

      if (this.timeRemaining <= 0) {
        this.stopTimer();
        this.onTimeUp();
      }
    }, 1000);
  }

  private stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = undefined;
    }
  }

  private updateTimeDisplay() {
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    this.timeDisplay = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  onTimeUp() {
    this.toastService.showError('Time is up! Auto-submitting your test...');
    this.submit();
  }

  // --- Answering & submission ---
  handleAnswer(questionId: string, value: any) {
    this.answers[questionId] = value;
  }

  submit() {
    if (this.submitted) return;
    this.stopTimer();
    this.submitted = true;
    this.showFullscreenModal = false;

    const token = localStorage.getItem('token');
    if (!token) {
      this.error = 'Authentication token missing';
      this.submitted = false;
      return;
    }

    const payload = { answers: this.answers, start_time: this.startTime.toISOString() };
    this.dashboardService.submitTestAnswers(this.testId, payload, token).subscribe({
      next: () => {
          this.router.navigate(['/results', this.testId]);
        // if (this.debug_id) {
        //   this.router.navigate(['/debug-test', this.debug_id]);
        // } else {
        //   this.router.navigate(['/employee-dashboard']);
        // }
      },
      error: (err) => {
        console.error('Submit failed', err);
        this.error = 'Failed to submit answers';
        this.submitted = false;
      }
    });
  }

  // --- Fullscreen behavior ---
  private handleFullscreenChange() {
    if (!document.fullscreenElement && !this.submitted && !this.showStartModal) {
      this.showFullscreenModal = true;
    } else {
      this.showFullscreenModal = false;
    }
    this.cdr.detectChanges();
  }

  startTestInFullscreen() {
    const container = this.testContainer?.nativeElement || document.documentElement;
    if (container.requestFullscreen) {
      container.requestFullscreen()
        .then(() => {
          this.showStartModal = false;
          this.cdr.detectChanges();
        })
        .catch((err: any) => console.warn('requestFullscreen failed', err));
    } else {
      // Fallback: hide start modal and start anyway
      this.showStartModal = false;
      this.cdr.detectChanges();
    }
  }

  goToFullScreen() {
    const container = this.testContainer?.nativeElement || document.documentElement;
    if (container.requestFullscreen) {
      container.requestFullscreen().catch((err: any) => console.warn('requestFullscreen failed', err));
    }
  }

  submitTestFromModal() {
    this.submit();
  }

  // Handler for already attended modal "Continue" button
  continueToDashboard() {
    this.showAlreadyAttendedModal = false;
    this.router.navigate(['/employee-dashboard']);
  }

  // --- helpers & UI progress ---
  handleBeforeUnload = (event: BeforeUnloadEvent) => {
    if (!this.submitted && this.timeRemaining > 0) {
      // Fire a submit and set a flag so we can redirect after reload
      try {
        // best-effort synchronous action: mark flag and let submit() handle async
        localStorage.setItem('testAutoSubmitted', 'true');
        this.submit();
      } catch (e) {
        // ignore localStorage errors
      }
      event.preventDefault();
      event.returnValue = '';
    }
  };

  getAnsweredQuestionsCount(): number {
    return Object.keys(this.answers).length;
  }

  getProgressPercentage(): number {
    if (!this.testDetails || !this.testDetails.questions) return 0;
    const total = this.testDetails.questions.length;
    const answered = this.getAnsweredQuestionsCount();
    return total > 0 ? (answered / total) * 100 : 0;
  }

  formatTimer(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }
}
