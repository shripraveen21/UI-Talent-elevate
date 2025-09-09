import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { McqFormComponent } from '../mcq-form/mcq-form.component';
import { McqQuestionComponent, MCQQuestion } from '../mcq-question/mcq-question.component';
import { McqAgentService, QuizParams, AgentMessage } from '../../services/mcq-agent/mcq-agent.service';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';

@Component({
  selector: 'app-mcq-quiz',
  templateUrl: './mcq-quiz.component.html',
  styleUrls: ['./mcq-quiz.component.css'],
  standalone: true,
  imports: [CommonModule, McqFormComponent, McqQuestionComponent]
})
export class McqQuizComponent  {
  quizParams?: QuizParams;
  quizQuestions: MCQQuestion[] = [];
  loading: boolean = false;
  error: string = '';
  reviewIteration: number = 0;
  showAnswers: boolean = false;
  reviewMode: boolean = false;

  constructor(
    private mcqAgentService: McqAgentService,
  ) {}

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
    this.mcqAgentService.sendDecision(decision, feedback);
    this.loading = true;
  }

  showAllAnswers() {
    this.showAnswers = true;
  }
}
