import { Component } from '@angular/core';
import { HandsonAgentService, AgentMessage } from '../../services/hands-on.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-handson-workflow',
  templateUrl: './hands-on-gen.component.html',
  imports: [CommonModule, FormsModule]
})
export class HandsonWorkflowComponent {
  techStackName = '';
  duration = 30;
  topics: string[] = [];

  srsReview?: AgentMessage;
  finalData?: any;
  error?: string;
  handsonStored : boolean = false

  constructor(private handsonAgent: HandsonAgentService,private router: Router) { }


  addTopic() {
    this.topics.push('');
  }

  removeTopic(i: number) {
    this.topics.splice(i, 1);
  }

  topicsInput = '';

  onSubmit() {
    const params = {
      tech_stack: [{ name: this.techStackName }],
      topics: this.topicsInput.split(',').map(t => t.trim()).filter(t => t),
      duration: this.duration
    };
    this.handsonAgent.connect(params).subscribe(msg => {
      if (msg.type === 'srs_review') {
        this.srsReview = msg;
      } else if (msg.type === 'final') {
        this.finalData = msg.content;
        this.handsonAgent.close();
      } else if (msg.type === 'error') {
        this.error = msg.content;
      }
    });
  }

  approve() {
    this.handsonAgent.sendFeedback('approve');
  }

  suggest() {
    const suggestions = prompt('Enter additional topics, comma-separated:');
    if (suggestions) {
      this.handsonAgent.sendFeedback('suggest', suggestions.split(',').map(s => s.trim()));
    }
  }

  proceedToSaveAssessment() {
    this.router.navigate(['/create-assessment'], {
      queryParams: { step: 'save' }
    });
  }

  saveHandson() {
    if (this.finalData) {
      this.handsonAgent.storeHandson(this.finalData).subscribe(response => {
        let handsonId = response.handson_id;
        sessionStorage.setItem("handson_id", handsonId);
        this.handsonStored = true
        this.proceedToSaveAssessment();
      }, err => {
        this.error = 'Failed to save HandsOn record.';
      });
    }
  }
}

