import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { McqFormComponent } from '../mcq-form/mcq-form.component';
import { McqQuestionComponent, MCQQuestion } from '../mcq-question/mcq-question.component';
import { McqAgentService, QuizParams, AgentMessage } from '../../services/mcq-agent/mcq-agent.service';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';

@Component({
  selector: 'app-mcq-quiz',
  templateUrl: './mcq-quiz.component.html',
  styleUrls: ['./mcq-quiz.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, McqFormComponent, McqQuestionComponent]
})
export class McqQuizComponent  {
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

  constructor(
    private mcqAgentService: McqAgentService,
  ) {}

  getOptionKeys(options: { [key: string]: string }): string[] {
    return Object.keys(options);
  }

  onSubmitParams(params: QuizParams) {
    this.quizParams = params;
    this.loading = true;
    this.error = '';
    this.showAnswers = false;
    this.reviewMode = true;
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
        next: () => {
          this.loading = false;
          this.reviewMode = false;
        },
        error: (err) => {
          this.error = "Failed to store quiz: " + (err?.message || "Unknown error");
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
  }

  confirmRegenerate() {
    const comment = this.regenerateComment;
    console.log(`Regenerating: ${this.currentRegenerateTarget}`);
    console.log(`With comment: ${comment || 'No comment provided'}`);
    
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
        this.sendDecision('REFINE', `Question ID: ${questionId}`);
      }
    }
    
    this.closeRegenerateModal();
  }
}
