import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { McqFormComponent } from '../mcq-form/mcq-form.component';
import { McqQuestionComponent, MCQQuestion } from '../mcq-question/mcq-question.component';
import { McqAgentService, QuizParams, AgentMessage } from '../../services/mcq-agent/mcq-agent.service';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { ToastService } from '../../services/toast/toast.service';
import { LoginService } from '../../services/login/login.service';

@Component({
  selector: 'app-mcq-quiz',
  templateUrl: './mcq-quiz.component.html',
  styleUrls: ['./mcq-quiz.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, McqFormComponent, McqQuestionComponent]
})
export class McqQuizComponent implements OnInit, OnDestroy {
  quizParams?: QuizParams;
  quizQuestions: MCQQuestion[] = [];
  loading: boolean = false;
  error: string = '';
  reviewIteration: number = 0;
  showAnswers: boolean = false;
  reviewMode: boolean = false;
  feedback: string = '';
  showRegenerateModal: boolean = false;
  regenerateModalTitle: string = '';
  regenerateComment: string = '';
  currentRegenerateTarget: string | number | null = null;
  regeneratingQuestionIndex: number | null = null;
  
  // Dynamic properties for quiz display
  quizTitle: string = 'MCQ Assessment';
  quizDescription: string = 'Multiple Choice Questions Assessment';
  timeRemaining: number = 0; // in seconds
  timeDisplay: string = '00:00';
  private timerInterval?: number;
  
  // User information
  currentUserName: string = '';

  constructor(
    private mcqAgentService: McqAgentService,
    private toastService: ToastService,
    private loginService: LoginService,
    private router: Router
  ) {}

  ngOnInit() {
    // Initialize timer display
    this.updateTimeDisplay();
    
    // Get current user's name
    this.getCurrentUserName();
  }

  ngOnDestroy() {
    // Clean up timer when component is destroyed
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }

  navigateToNextWorkflowStep() {
    const workflowSequence = JSON.parse(sessionStorage.getItem('workflowSequence') || '[]');
    const currentStep = parseInt(sessionStorage.getItem('currentWorkflowStep') || '0');
    const nextStep = currentStep + 1;

    if (nextStep < workflowSequence.length) {
      // Move to next component
      sessionStorage.setItem('currentWorkflowStep', nextStep.toString());
      const nextComponent = workflowSequence[nextStep];
      
      // Get assessment details for navigation
      const assessmentDetails = JSON.parse(sessionStorage.getItem('assessmentDetails') || '{}');
      
      if (nextComponent === 'debug') {
        this.router.navigate(['/debug-exercise'], {
          queryParams: {
            techStack: JSON.stringify({
              id: assessmentDetails.selectedTechStack?.id || assessmentDetails.selectedTechStack?.tech_stack_id,
              name: assessmentDetails.selectedTechStack?.name
            }),
            concepts: JSON.stringify(assessmentDetails.selectedConcepts || [])
          }
        });
      } else if (nextComponent === 'handsOn') {
        // Navigate to hands-on component when implemented
        console.log('Hands-on component not yet implemented');
        this.proceedToSaveAssessment();
      }
    } else {
      // All components completed, go to save assessment
      this.proceedToSaveAssessment();
    }
  }

  proceedToSaveAssessment() {
    this.router.navigate(['/create-assessment'], {
      queryParams: { step: 'save' }
    });
  }

  getOptionKeys(options: { [key: string]: string }): string[] {
    return Object.keys(options);
  }

  // Check if current user is an employee
  isEmployee(): boolean {
    return this.loginService.getUserRole() === 'Employee';
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

  // Timer functionality
  startTimer(durationInMinutes: number) {
    this.timeRemaining = durationInMinutes * 60; // Convert to seconds
    this.updateTimeDisplay();
    
    this.timerInterval = window.setInterval(() => {
      this.timeRemaining--;
      this.updateTimeDisplay();
      
      if (this.timeRemaining <= 0) {
        this.stopTimer();
        // Optionally handle time up event
        this.onTimeUp();
      }
    }, 1000);
  }

  stopTimer() {
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
    this.toastService.showError('Time is up! Please submit your assessment.');
    // Optionally auto-submit or show warning
  }

  // Generate dynamic title and description based on quiz params
  generateQuizTitle(): string {
    // Return simple assessment title instead of full topic details
    return 'MCQ Assessment';
  }

  generateQuizDescription(): string {
    if (!this.quizParams) return 'Multiple Choice Questions Assessment';
    
    const levels = [...new Set(this.quizParams.topics.map(t => t.level))];
    const levelText = levels.length > 1 ? 'Mixed Level' : levels[0]?.charAt(0).toUpperCase() + levels[0]?.slice(1) || '';
    
    return `${levelText} Multiple Choice Questions Assessment`;
  }

  onSubmitParams(params: QuizParams) {
    this.quizParams = params;
    this.loading = true;
    this.error = '';
    this.showAnswers = false;
    this.reviewMode = true;
    
    // Set dynamic title and description
    this.quizTitle = this.generateQuizTitle();
    this.quizDescription = this.generateQuizDescription();
    
    // Start timer if duration is provided
    if (params.duration && params.duration > 0) {
      this.startTimer(params.duration);
    }
    
    console.log(params,"params")
    this.mcqAgentService.connect(params).subscribe({
      next: (msg: AgentMessage) => {
        if (msg.type === 'review' || msg.type === 'final') {
          this.quizQuestions = this.parseQuizQuestions(msg.content);
          this.reviewIteration = msg.iteration || 0;
          this.loading = false;
          this.showAnswers = msg.type === 'review' || msg.type === 'final';
          this.reviewMode = msg.type === 'review';
        } else if (msg.type === 'error') {
          this.error = typeof msg.content === 'string' ? msg.content : 'Unknown error';
          this.loading = false;
        }
      },
      error: (err) => {
        this.error = 'WebSocket error';
        this.loading = false;
      }
    });
  }

  parseQuizQuestions(content: any): MCQQuestion[] {
    // content is an object with question1, question2, ...
    const questions: MCQQuestion[] = [];
    Object.keys(content).forEach(key => {
      const q = content[key];
      if (q && q.question && q.options && q.correctAnswer && q.explanation) {
        questions.push({
          question: q.question,
          options: q.options,
          correctAnswer: q.correctAnswer,
          explanation: q.explanation,
          topics:q.topics,
          concepts:q.concepts
        });
      }
    });
    return questions;
  }

  sendDecision(decision: string, feedback?: string) {
    const feedbackToSend = feedback || this.feedback;
    if (decision === "APPROVE" && this.quizParams && this.quizQuestions.length > 0) {
      this.loading = true;
      console.log(this.quizParams,this.quizQuestions)
      this.mcqAgentService.storeQuiz(this.quizParams, this.quizQuestions).subscribe({
        next: (response) => {
          // Save quiz_id to localStorage if returned
          if (response && response.quiz_id) {
            sessionStorage.setItem('quiz_id', String(response.quiz_id));
          }
          this.toastService.showQuizSaved();
          this.loading = false;
          this.reviewMode = false;
          // Navigate to next component in workflow
          this.navigateToNextWorkflowStep();
        },
        error: (err) => {
          const errorMessage = "Failed to store quiz: " + (err?.message || "Unknown error");
          this.error = errorMessage;
          this.toastService.showError(errorMessage);
          this.loading = false;
        }
      });
    }
    this.mcqAgentService.sendDecision(decision, feedbackToSend);
    this.feedback = ''; // Clear feedback after sending
    this.loading = true;
  }

  showAllAnswers() {
    this.showAnswers = true;
  }

  regenerateQuestion(index: number) {
    this.regeneratingQuestionIndex = index;
    this.currentRegenerateTarget = index;
    this.regenerateModalTitle = `Regenerate Question ${index + 1}`;
    this.showRegenerateModal = true;
  }

  regenerateEntireAssessment() {
    this.currentRegenerateTarget = 'Entire Assessment';
    this.regenerateModalTitle = 'Regenerate Entire Assessment';
    this.showRegenerateModal = true;
  }

  closeRegenerateModal() {
    this.showRegenerateModal = false;
    this.regenerateComment = '';
    this.currentRegenerateTarget = null;
    this.regeneratingQuestionIndex = null;
  }

  confirmRegenerate() {
    const comment = this.regenerateComment;
    console.log(`Regenerating: ${this.currentRegenerateTarget}`);
    console.log(`With comment: ${comment || 'Regenerate this question'}`);
    
    if (this.currentRegenerateTarget === 'Entire Assessment') {
      // Regenerate all questions
      this.sendDecision('REFINE', comment);
    } else if (typeof this.currentRegenerateTarget === 'number') {
      // Regenerate individual question
      const questionIndex = this.currentRegenerateTarget;
      const questionId = `question${questionIndex + 1}`; // Generate question ID based on index
      
      if (comment && comment.trim()) {
        // Send question ID and feedback for individual question regeneration
        this.sendDecision('FEEDBACK', `Question ID: ${questionId} | Feedback: ${comment}`);
      } else {
        // Send only question ID for regeneration without feedback
        this.sendDecision('FEEDBACK', `Regenerate this question | Question ID: ${questionId}`);
      }
    }
    
    this.closeRegenerateModal();
    this.regeneratingQuestionIndex = null;
  }
}
