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
      // techStack is a string, concepts is a JSON string
if (params['techStack']) {
  // If techStack is a number, use as id; if object, use its id and name; if string, do not default to id:0
  let stackParam = params['techStack'];
  if (typeof stackParam === 'object' && stackParam !== null) {
    this.params.tech_stack = [{ id: stackParam.id, name: stackParam.name }];
  } else if (!isNaN(Number(stackParam))) {
    this.params.tech_stack = [{ id: Number(stackParam), name: '' }];
  } else {
    // If only name is present, leave id undefined or handle as needed
    this.params.tech_stack = [{ id: -1, name: stackParam }];
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
