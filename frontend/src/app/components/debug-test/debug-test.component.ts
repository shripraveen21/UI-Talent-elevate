import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-debug-test',
  templateUrl: './debug-test.component.html',
  styleUrls: ['./debug-test.component.css'],
  imports: [CommonModule]
})
export class DebugTestComponent implements OnInit, OnDestroy {
  debugTestId!: number;
  exercises: any[] = [];
  answers: { [id: string]: string } = {};
  testName = '';
  testDuration = '';
  timer = 0;
  interval: any;
  submitted = false;
  loading = true;   // <-- loading flag for UI state
  error = '';
  startTime: Date = new Date();

  constructor(
    private route: ActivatedRoute,
    private dashboardService: DashboardService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.debugTestId = Number(this.route.snapshot.paramMap.get('id'));
    this.startTime = new Date();

    // Auto-redirect if test was already autosubmitted
    if (localStorage.getItem('debugTestAutoSubmitted') === 'true') {
      localStorage.removeItem('debugTestAutoSubmitted');
      this.router.navigate(['/debug-results', this.debugTestId]);
      return;
    }

    window.addEventListener('beforeunload', this.handleBeforeUnload);

    const token = localStorage.getItem('token');
    if (!token || !this.debugTestId) {
      this.error = 'Test or authentication info missing';
      this.loading = false;
      return;
    }

    this.dashboardService.getDebugTestDetails(this.debugTestId, token).subscribe({
      next: (data) => {
        this.testName = data.test_name;
        this.testDuration = data.test_duration;
        this.exercises = data.exercises;
        // Parse MM:SS string to seconds for timer
        const [min, sec] = (data.test_duration || '20:00').split(':').map(Number);
        this.timer = min * 60 + sec;
        this.loading = false;
        this.startTimer();
      },
      error: () => {
        this.error = 'Failed to load debug test details';
        this.loading = false;
      }
    });
  }

  ngOnDestroy(): void {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    clearInterval(this.interval);
  }

  handleBeforeUnload = (event: BeforeUnloadEvent) => {
    if (!this.submitted && this.timer > 0) {
      this.submit();
      localStorage.setItem('debugTestAutoSubmitted', 'true');
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

  handleAnswer(exerciseId: string, value: string) {
    this.answers[exerciseId] = value;
  }

  submit() {
    if (this.submitted) return;
    clearInterval(this.interval);
    this.submitted = true;
    const token = localStorage.getItem('token');
    this.dashboardService.submitDebugAnswers(
      this.debugTestId,
      { answers: this.answers, start_time: this.startTime.toISOString() },
      token!
    ).subscribe({
      next: () => {
        this.router.navigate(['/debug-results', this.debugTestId]);
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
}