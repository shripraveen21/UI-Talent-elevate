import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DashboardService } from '../../services/testAttempt/dashboard.service';
import { CommonModule } from '@angular/common';
import { BackButtonComponent } from '../shared/backbutton/backbutton.component';
import * as Prism from 'prismjs';
import 'prismjs/themes/prism.css';

@Component({
  selector: 'app-debug-test',
  templateUrl: './debug-test.component.html',
  styleUrls: ['./debug-test.component.css'],
  imports: [CommonModule, BackButtonComponent]
})
export class DebugTestComponent implements OnInit, OnDestroy, AfterViewInit {
  debugTestId!: number;
  exercises: any[] = [];
  answers: { [id: string]: string } = {};
  savedAnswers: { [id: string]: boolean } = {}; // Track which answers are saved
  testName = '';
  testDuration = '';
  timer = 0;
  interval: any;
  submitted = false;
  loading = true;   // <-- loading flag for UI state
  error = '';
  startTime: Date = new Date();
  currentExerciseIndex = 0;

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
        // Load any previously saved answers
        this.loadSavedAnswers();
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

  ngAfterViewInit(): void {
    // Dynamically load PrismJS language components to ensure proper initialization order
    this.loadPrismLanguages().then(() => {
      // Highlight code blocks after all languages are loaded
      setTimeout(() => {
        Prism.highlightAll();
      }, 100);
    });
  }

  private async loadPrismLanguages(): Promise<void> {
    try {
      // Ensure Prism object is properly initialized
      if (typeof Prism === 'undefined' || !Prism.languages) {
        console.warn('Prism object not properly initialized');
        return;
      }

      // Load language components dynamically to avoid initialization issues
      // Using type assertion to avoid TypeScript declaration errors
      await import('prismjs/components/prism-javascript' as any);
      await import('prismjs/components/prism-python' as any);
      await import('prismjs/components/prism-java' as any);
      await import('prismjs/components/prism-csharp' as any);
      await import('prismjs/components/prism-cpp' as any);
      await import('prismjs/components/prism-typescript' as any);
      
      // Verify languages are loaded
      console.log('PrismJS languages loaded:', Object.keys(Prism.languages));
    } catch (error) {
      console.warn('Failed to load some PrismJS language components:', error);
    }
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
    // Mark as unsaved when user types
    this.savedAnswers[exerciseId] = false;
  }

  saveAnswer(exerciseId: string): void {
    if (this.answers[exerciseId] && this.answers[exerciseId].trim() !== '') {
      // Save to localStorage for persistence
      const savedData = {
        testId: this.debugTestId,
        answers: this.answers,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem(`debugTest_${this.debugTestId}`, JSON.stringify(savedData));
      this.savedAnswers[exerciseId] = true;
      
      // Show success feedback (you can replace with a toast service)
      console.log(`Answer saved for exercise ${exerciseId}`);
    }
  }

  loadSavedAnswers(): void {
    const savedData = localStorage.getItem(`debugTest_${this.debugTestId}`);
    if (savedData) {
      try {
        const parsed = JSON.parse(savedData);
        if (parsed.testId === this.debugTestId) {
          this.answers = parsed.answers || {};
          // Mark all loaded answers as saved
          Object.keys(this.answers).forEach(id => {
            if (this.answers[id] && this.answers[id].trim() !== '') {
              this.savedAnswers[id] = true;
            }
          });
        }
      } catch (error) {
        console.error('Error loading saved answers:', error);
      }
    }
  }

  getLanguageFromTechnology(technology: string): string {
    const techMap: { [key: string]: string } = {
      'javascript': 'javascript',
      'python': 'python',
      'java': 'java',
      'c#': 'csharp',
      'csharp': 'csharp',
      'c++': 'cpp',
      'cpp': 'cpp',
      'typescript': 'typescript'
    };
    return techMap[technology?.toLowerCase()] || 'javascript';
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

  get progressPercentage(): number {
    if (this.exercises.length === 0) return 0;
    return (this.currentExerciseIndex / (this.exercises.length - 1)) * 100;
  }

  getSolvedCount(): number {
    return Object.keys(this.answers).filter(id => this.answers[id] && this.answers[id].trim() !== '').length;
  }

  getSavedCount(): number {
    return Object.keys(this.savedAnswers).filter(id => this.savedAnswers[id]).length;
  }

  saveAllAnswers(): void {
    // Save all answered exercises
    Object.keys(this.answers).forEach(exerciseId => {
      if (this.answers[exerciseId] && this.answers[exerciseId].trim() !== '') {
        this.saveAnswer(exerciseId);
      }
    });
  }

  runTest(exerciseId: string, code: string): void {
    // This method can be implemented to run the code and show results
    // For now, it's a placeholder that could integrate with a code execution service
    console.log('Running test for exercise:', exerciseId, 'with code:', code);
    // You can add actual code execution logic here
  }

  goToPrevious(): void {
    if (this.currentExerciseIndex > 0) {
      this.currentExerciseIndex--;
      // Re-highlight code blocks when navigating
      setTimeout(() => {
        Prism.highlightAll();
      }, 100);
    }
  }

  goToNext(): void {
    if (this.currentExerciseIndex < this.exercises.length - 1) {
      this.currentExerciseIndex++;
      // Re-highlight code blocks when navigating
      setTimeout(() => {
        Prism.highlightAll();
      }, 100);
    }
  }

  // Navigation method for back button
  returnToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }
}