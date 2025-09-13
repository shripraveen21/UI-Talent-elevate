import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface MCQQuestion {
  question: string;
  options: { [key: string]: string };
  correctAnswer: string;
  explanation: string;
  selectedAnswer?: string;
  topics:[string];  
  concepts:[string];  
}

@Component({
  selector: 'app-mcq-question',
  templateUrl: './mcq-question.component.html',
  styleUrls: ['./mcq-question.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class McqQuestionComponent {
  @Input() questionData!: MCQQuestion;
  @Input() showAnswer: boolean = false;

  getOptionKeys(options: { [key: string]: string }): string[] {
    return Object.keys(options);
  }

  selectOption(optionKey: string) {
    this.questionData.selectedAnswer = optionKey;
  }

  isCorrect(): boolean {
    return this.questionData.selectedAnswer === this.questionData.correctAnswer;
  }
}
