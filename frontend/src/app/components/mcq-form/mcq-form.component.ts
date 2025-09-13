import { Component, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { QuizParams } from '../../services/mcq-agent/mcq-agent.service';

@Component({
  selector: 'app-mcq-form',
  templateUrl: './mcq-form.component.html',
  styleUrls: ['./mcq-form.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class McqFormComponent implements OnInit {
  public params: QuizParams & { concepts: any[] } = {
    tech_stack: [],
    concepts: [],
    topics: [],
    num_questions: 5,
    duration: 15
  };

  @Output() submitParams = new EventEmitter<QuizParams>();

  constructor(private route: ActivatedRoute) { }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      // techStack is now a JSON string, concepts is a JSON string
      if (params['techStack']) {
        try {
          // Try to parse as JSON first (new format)
          const techStackData = JSON.parse(params['techStack']);
          this.params.tech_stack = [{ 
            id: techStackData.id, 
            name: techStackData.name || 'Selected Tech Stack' 
          }];
        } catch {
          // Fallback for old format (just ID or name)
          let stackParam = params['techStack'];
          if (!isNaN(Number(stackParam))) {
            this.params.tech_stack = [{ id: Number(stackParam), name: 'Selected Tech Stack' }];
          } else {
            this.params.tech_stack = [{ id: -1, name: stackParam }];
          }
        }
      }
      if (params['concepts']) {
        try {
          this.params.concepts = JSON.parse(params['concepts']);
        } catch {
          this.params.concepts = [];
        }
      }
    });
  }

  public onSubmit() {
    // Remove concepts property before emitting if QuizParams doesn't expect it
    const { concepts, ...paramsWithoutConcepts } = this.params;
    this.submitParams.emit({ ...paramsWithoutConcepts, topics: concepts });
  }
}
